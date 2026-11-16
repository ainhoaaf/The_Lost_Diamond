"""Pruebas del motor, sin red.

Cada test fija el sorteo (`tokens=`), quién abre (`first_player=`) y las
tiradas (`roll(forced=)`) para no depender del azar.

Orden de turno en todos los tests: Player_1 (A1), Player_2 (C4),
Player_3 (A1), Player_4 (C4).

    python3 -m unittest tests.test_game
"""

from __future__ import annotations

import random
import unittest
from collections import Counter

from lost_diamond.engine.game import Game, GameError
from lost_diamond.engine.tokens import POOL, playable_cells

P1, P2, P3, P4 = "Player_1", "Player_2", "Player_3", "Player_4"

_FILL_ORDER = ("A2", "A4", "C2", "C3", "A5", "C1", "A3", "B3", "B1", "B2", "E1", "E2", "D1", "D2")


def _seats() -> dict[str, str]:
    return {P1: "A1", P2: "C4", P3: "A1", P4: "C4"}


def _layout(**fixed: str) -> dict[str, str]:
    """Sorteo completo con las fichas de `fixed` en su sitio y el resto repartido."""
    left = Counter(POOL)
    left.subtract(fixed.values())
    if any(n < 0 for n in left.values()):
        raise ValueError("más fichas de las que hay en POOL")
    kinds = sorted(left.elements(), key=lambda k: (k != "blank", k))
    free = [c for c in _FILL_ORDER if c not in fixed]
    layout = dict(fixed)
    layout.update(zip(free, kinds))
    assert set(layout) == set(playable_cells())
    return layout


def _game(**fixed: str) -> Game:
    """Partida con las fichas de `fixed` y todo lo demás en blanco."""
    game = Game(rng=random.Random(0))
    game.new_game(_seats(), tokens=_layout(**fixed), first_player=P1)
    for cell, tile in game._tiles.items():  # noqa: SLF001
        if cell not in fixed:
            tile.kind = "blank"
    return game


def _place(game: Game, player: str, cell: str) -> None:
    """Atajo de test: coloca un meeple sin jugar los turnos intermedios."""
    game._players[player].cell = cell  # noqa: SLF001


def _move(game: Game, die: int, *cells: str):
    """Tira `die` para el jugador activo y hace los saltos. Devuelve el último StepOutcome."""
    game.roll(forced=die)
    outcome = None
    for cell in cells:
        outcome = game.step(cell)
        assert outcome.ok, (cell, outcome)
    return outcome


class SetupTest(unittest.TestCase):
    def test_new_game_seats_two_players_on_each_home(self) -> None:
        game = Game()
        game.new_game(_seats())
        self.assertIn(game.current_player(), _seats())
        for player, home in _seats().items():
            self.assertEqual(game.player_state(player).cell, home)

    def test_bottom_home_can_open(self) -> None:
        game = Game()
        game.new_game(_seats(), tokens=_layout(), first_player=P2)
        self.assertEqual(game.current_player(), P2)

    def test_random_deal_uses_the_whole_pool(self) -> None:
        game = Game(rng=random.Random(42))
        game.new_game(_seats())
        kinds = Counter(tile.kind for tile in game._tiles.values())  # noqa: SLF001
        self.assertEqual(kinds, Counter(POOL))

    def test_bad_seats_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Game().new_game({P1: "A1", P2: "A1", P3: "A1", P4: "C4"})
        with self.assertRaises(ValueError):
            Game().new_game({P1: "A1", P2: "C4", P3: "A1", P4: "B2"})

    def test_starting_at_home_is_not_a_win(self) -> None:
        self.assertIsNone(_game().winner())


if __name__ == "__main__":
    unittest.main()