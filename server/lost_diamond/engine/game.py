"""Una partida.

El sorteo, los turnos y la victoria se implementan aquí.
Esta clase todavía no juega: deja escrito el orden de las operaciones.
"""

from __future__ import annotations


class Game:
    def new_game(self, player_ids: list[str]) -> None:
        """Baraja las 14 fichas y sienta a los jugadores, dos en cada casa.

        El turno alterna A1 y B4.
        """
        raise NotImplementedError

    def roll(self, player_id: str) -> int:
        """Devuelve 1, 2 o 3 para el jugador activo."""
        raise NotImplementedError

    def legal_cells(self, player_id: str, steps: int) -> list[str]:
        """Casillas donde puede acabar un camino de `steps` o un puente de ese coste."""
        raise NotImplementedError

    def move(self, player_id: str, cell: str) -> str:
        """Aplica la casilla si es legal. Si no, devuelve el motivo del aviso."""
        raise NotImplementedError
