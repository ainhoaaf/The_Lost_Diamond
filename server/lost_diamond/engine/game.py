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
from collections import Counter
from dataclasses import dataclass, field

from lost_diamond.engine.board import HOMES, all_cells, hops_from
from lost_diamond.engine.tokens import POOL, playable_cells, reveal_code

DIE_FACES = (1, 2, 3)

REASON_ILLEGAL = "destino_ilegal"
REASON_OCCUPIED = "ocupada"
REASON_NO_ROLL = "sin_tirada"

PHASE_PLAYING = "playing"
PHASE_FINISHED = "finished"


class GameError(RuntimeError):
    """Llamada fuera de orden: `roll` con tirada abierta, partida acabada..."""


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

@dataclass
class _Player:
    id: str
    home: str
    cell: str
    has_diamond: bool = False
    has_horseshoe: bool = False
    skip: bool = False


@dataclass
class _Tile:
    kind: str
    spent: bool = False

class Game:
    def __init__(self, rng: random.Random | None = None) -> None:
        """`rng` fija sorteo y dado en los tests. Sin él, usa el azar normal."""
        self.rng = rng or random.Random()
        self._players: dict[str, _Player] = {}
        self._order: list[str] = []
        self._turn = 0
        self._tiles: dict[str, _Tile] = {}
        self._diamond_found = False
        self._winner: str | None = None
        # Tirada actual.
        self._movements = 0
        self._remaining = 0
        self._start: str | None = None
        self._rolling = False

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
        if set(seats.values()) - set(HOMES):
            raise ValueError("las casas son A1 y C4")
        by_home = {h: sorted(p for p, home in seats.items() if home == h) for h in HOMES}
        if any(len(players) != 2 for players in by_home.values()):
            raise ValueError("tiene que haber dos jugadores en A1 y dos en C4")

        if first_player is None:
            first_player = by_home[self.rng.choice(HOMES)][0]
        if first_player not in seats:
            raise ValueError(f"first_player no está sentado: {first_player}")

        # Turno: casa del primero, la otra casa, casa del primero, la otra casa.
        first_home = seats[first_player]
        other_home = HOMES[1] if first_home == HOMES[0] else HOMES[0]
        mate = next(p for p in by_home[first_home] if p != first_player)
        self._order = [first_player, by_home[other_home][0], mate, by_home[other_home][1]]
        self._turn = 0

        self._players = {p: _Player(id=p, home=h, cell=h) for p, h in seats.items()}
        self._tiles = self._deal(tokens)
        self._diamond_found = False
        self._winner = None
        self._end_roll()

    def _deal(self, tokens: dict[str, str] | None) -> dict[str, _Tile]:
        cells = playable_cells()
        if tokens is None:
            kinds = list(POOL)
            self.rng.shuffle(kinds)
            return {cell: _Tile(kind) for cell, kind in zip(cells, kinds)}
        if set(tokens) != set(cells):
            raise ValueError("tokens tiene que cubrir las 14 casillas que no son casa")
        if Counter(tokens.values()) != Counter(POOL):
            raise ValueError("tokens no respeta el reparto de POOL")
        return {cell: _Tile(tokens[cell]) for cell in cells}

    def current_player(self) -> str:
        """Player_N al que le toca."""
        self._require_started()
        return self._order[self._turn]

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
        return self._winner
    def status(self) -> StatusView:
        """Estado de la partida, para publicar `Game_status`."""
        self._require_started()
        carrier = next((p.id for p in self._players.values() if p.has_diamond), None)
        return StatusView(
            current_player=self.current_player(),
            diamond_found=self._diamond_found,
            carrier=carrier,
            phase=PHASE_FINISHED if self._winner else PHASE_PLAYING,
            winner=self._winner,
            movements=self._movements,
            remaining=self.remaining(),
        )

    def player_state(self, player_id: str) -> PlayerView:
        """Estado de un jugador, para publicar `Players/Player_N`."""
        p = self._players[player_id]
        return PlayerView(p.id, p.home, p.cell, p.has_diamond, p.has_horseshoe, p.skip)

    # --------------------------------------------------------------- interno

    def _require_started(self) -> None:
        if not self._order:
            raise GameError("falta llamar a new_game")

    def _end_roll(self) -> None:
        self._movements = 0
        self._remaining = 0
        self._start = None
        self._rolling = False

_ALL_CELLS = frozenset(all_cells())
