"""Una partida.

Este archivo es el único que aplica reglas: sorteo, turno, dado, cada salto
del meeple, efecto de la ficha y victoria. No importa MQTT.

Flujo de un turno:

1. `new_game` baraja las 14 fichas y sienta a dos jugadores en A1 y dos en C4.
   El turno alterna casa de arriba y casa de abajo.
2. `roll` tira siempre para quien tiene el turno: 1, 2 o 3, y guarda el
   presupuesto de pasos. Nunca devuelve 0. Si no hay ninguna casilla legal
   (`blocked`), el turno pasa solo. Quien tiene un naufragio pendiente se
   salta solo al pasar el turno y queda en `skipped`.
3. `step` recibe la siguiente casilla (traducida del UID). Si el salto es
   ilegal, avisa y no gasta pasos. Si es legal, resta el coste. No se puede
   volver a la casilla de salida de esa tirada.
4. Cuando los pasos llegan a 0, `step` revela la ficha y aplica el efecto.
   Moneda: otra tirada en el mismo turno, desde esa casilla (`extra_roll`).
   Pirata, si el diamante no ha salido: vuelve a su casa de salida.
   Naufragio: el siguiente turno de ese jugador se salta.
   Herradura: da derecho a ganar solo si el diamante ya salió.
5. Gana quien acaba un movimiento en A1 o C4 con el diamante, o con el
   derecho de la herradura antes que el portador.
6. `status` y `player_state` solo leen. El adaptador los usa para publicar
   `Game_status` y `Players/Player_N`.

Para tests: `Game(rng=...)`, `new_game(..., tokens=..., first_player=...)` y
`roll(forced=...)` fijan el azar. En producción se llaman sin esos argumentos.

El aviso de 15 segundos no vive aquí: lo cuenta el adaptador y no cancela el turno.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class RollOutcome:
    player: str
    value: int
    blocked: bool
    next_player: str
    skipped: list[str] = field(default_factory=list)


@dataclass
class StepOutcome:
    ok: bool
    reason: str
    cell: str
    remaining: int
    token: str | None
    extra_roll: bool
    won: bool
    next_player: str
    skipped: list[str] = field(default_factory=list)


@dataclass
class StatusView:
    current_player: str
    diamond_found: bool
    carrier: str | None
    phase: str
    winner: str | None
    movements: int
    remaining: int


@dataclass
class PlayerView:
    id: str
    home: str
    cell: str
    has_diamond: bool
    has_horseshoe: bool
    skip: bool


class Game:
    def __init__(self, rng: random.Random | None = None) -> None:
        """`rng` fija sorteo y dado en los tests. Sin él, usa el azar normal."""
        self.rng = rng or random.Random()

    def new_game(
        self,
        seats: dict[str, str],
        *,
        tokens: dict[str, str] | None = None,
        first_player: str | None = None,
    ) -> None:
        """Baraja las fichas y sienta a los jugadores.

        `seats` es Player_N → casa (A1 o C4). Dos en cada casa.
        `tokens` (solo tests) es casilla → ficha y evita el sorteo.
        `first_player` (solo tests) fija quién empieza. Sin él, empieza un
        jugador de una casa elegida al azar.
        """
        raise NotImplementedError

    def current_player(self) -> str:
        """Player_N al que le toca."""
        raise NotImplementedError

    def roll(self, *, forced: int | None = None) -> RollOutcome:
        """Dado de 1 a 3 para el jugador activo. Guarda los pasos que quedan.

        `forced` (solo tests) fija el número.
        """
        raise NotImplementedError

    def remaining(self) -> int:
        """Pasos que le faltan al jugador activo en esta tirada."""
        raise NotImplementedError

    def legal_next(self) -> list[str]:
        """Casillas a un salto cuyo coste cabe en los pasos que quedan.

        La casilla de salida de la tirada no entra.
        """
        raise NotImplementedError

    def step(self, cell: str) -> StepOutcome:
        """Aplica un salto. Si no es legal, `ok` es falso y no gasta pasos."""
        raise NotImplementedError

    def winner(self) -> str | None:
        """Player_N si alguien ha ganado, si no None."""
        raise NotImplementedError

    def status(self) -> StatusView:
        """Estado de la partida, para publicar `Game_status`."""
        raise NotImplementedError

    def player_state(self, player_id: str) -> PlayerView:
        """Estado de un jugador, para publicar `Players/Player_N`."""
        raise NotImplementedError
