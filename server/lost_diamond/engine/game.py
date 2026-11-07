"""Una partida.

Este archivo es el único que aplica reglas: sorteo, turno, dado, cada salto
del meeple, efecto de la ficha y victoria. No importa MQTT.

Flujo de un turno:

1. `new_game` baraja las 14 fichas y sienta a dos jugadores en A1 y dos en C4.
   El turno alterna casa de arriba y casa de abajo.
2. `roll` guarda un 1, 2 o 3 y el presupuesto de pasos. Si el jugador tiene
   `skip` por un naufragio, no tira y el turno pasa.
3. `step` recibe la siguiente casilla (traducida del UID). Si el salto es
   ilegal, avisa y no gasta pasos. Si es legal, resta el coste. No se puede
   volver a la casilla de salida de esa tirada.
4. Cuando los pasos llegan a 0, `step` revela la ficha y aplica el efecto.
   Moneda: otra tirada en el mismo turno, desde esa casilla.
   Pirata, si el diamante no ha salido: vuelve a su casa de salida.
   Naufragio: el siguiente turno de ese jugador se salta.
   Herradura: da derecho a ganar solo si el diamante ya salió.
5. Gana quien acaba un movimiento en A1 o C4 con el diamante, o con el
   derecho de la herradura antes que el portador.

El aviso de 15 segundos no vive aquí: lo cuenta el adaptador y no cancela el turno.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StepOutcome:
    ok: bool
    reason: str
    cell: str
    remaining: int
    token: str | None
    extra_roll: bool
    won: bool


class Game:
    def new_game(self, seats: dict[str, str]) -> None:
        """Baraja las fichas y sienta a los jugadores.

        `seats` es Player_N → casa (A1 o C4). Dos en cada casa.
        El primer turno es de un jugador de la casa que se elija al azar.
        """
        raise NotImplementedError

    def current_player(self) -> str:
        """Player_N al que le toca."""
        raise NotImplementedError

    def roll(self) -> int:
        """Dado de 1 a 3 para el jugador activo. Guarda los pasos que quedan."""
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
