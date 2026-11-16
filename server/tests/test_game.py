"""Game engine tests, no network.

Every test fixes the deal (`tokens=`), who opens (`first_player=`) and the
die (`roll(forced=)`) so nothing depends on randomness.

Turn order in every test: Player_1 (A1), Player_2 (C4),
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

# Cells next to the homes get the leftover blanks first, so tokens a test does not fix cannot get in its way.
_FILL_ORDER = ("A2", "A4", "C2", "C3", "A5", "C1", "A3", "B3", "B1", "B2", "E1", "E2", "D1", "D2")


def _seats() -> dict[str, str]:
    return {P1: "A1", P2: "C4", P3: "A1", P4: "C4"}


def _layout(**fixed: str) -> dict[str, str]:
    """Full deal with the `fixed` tokens in place and the rest distributed."""
    left = Counter(POOL)
    left.subtract(fixed.values())
    if any(n < 0 for n in left.values()):
        raise ValueError("more tokens than POOL contains")
    kinds = sorted(left.elements(), key=lambda k: (k != "blank", k))
    free = [c for c in _FILL_ORDER if c not in fixed]
    layout = dict(fixed)
    layout.update(zip(free, kinds))
    assert set(layout) == set(playable_cells())
    return layout


def _game(**fixed: str) -> Game:
    """Game with the `fixed` tokens and every other cell blank.

    `_layout` validates a complete deal first; tokens the test did not ask
    for are then blanked so they cannot interfere.
    """
    game = Game(rng=random.Random(0))
    game.new_game(_seats(), tokens=_layout(**fixed), first_player=P1)
    for cell, tile in game._tiles.items():  # noqa: SLF001
        if cell not in fixed:
            tile.kind = "blank"
    return game


def _place(game: Game, player: str, cell: str) -> None:
    """Test shortcut: place a meeple without playing the turns in between."""
    game._players[player].cell = cell  # noqa: SLF001


def _move(game: Game, die: int, *cells: str):
    """Roll `die` for the active player and make the hops. Returns the last StepOutcome."""
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

class MovementTest(unittest.TestCase):
    def test_turn_alternates_top_and_bottom_home(self) -> None:
        game = _game()
        order = []
        for cell_by_player in ({P1: "A2"}, {P2: "C2"}, {P3: "A4"}, {P4: "C3"}):
            order.append(game.current_player())
            _move(game, 1, cell_by_player[game.current_player()])
        self.assertEqual(order, [P1, P2, P3, P4])
        self.assertEqual(game.current_player(), P1)

    def test_roll_is_one_to_three_and_sets_remaining(self) -> None:
        game = Game(rng=random.Random(7))
        game.new_game(_seats(), tokens=_layout(), first_player=P1)
        value = game.roll().value
        self.assertIn(value, (1, 2, 3))
        self.assertEqual(game.remaining(), value)
        self.assertEqual(game.status().movements, value)

    def test_cannot_roll_twice(self) -> None:
        game = _game()
        game.roll(forced=2)
        with self.assertRaises(GameError):
            game.roll()

    def test_step_without_roll_is_rejected(self) -> None:
        outcome = _game().step("A2")
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.reason, "sin_tirada")

    def test_illegal_step_does_not_spend_the_roll(self) -> None:
        """An illegal hop is reported and keeps the same budget."""
        game = _game()
        game.roll(forced=2)
        for bad in ("C1", "A3", "XX"):
            outcome = game.step(bad)
            self.assertFalse(outcome.ok)
            self.assertEqual(outcome.reason, "destino_ilegal")
            self.assertEqual(outcome.cell, "A1")
            self.assertEqual(outcome.remaining, 2)
            self.assertIsNone(outcome.token)
        self.assertEqual(game.remaining(), 2)
        self.assertTrue(game.step("A2").ok)
        self.assertEqual(game.remaining(), 1)

    def test_occupied_cell_is_rejected(self) -> None:
        game = _game()
        _move(game, 1, "A2")  # P1
        _move(game, 1, "C2")  # P2
        game.roll(forced=1)  # P3, on A1
        outcome = game.step("A2")
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.reason, "ocupada")
        self.assertNotIn("A2", game.legal_next())

    def test_turn_ends_on_any_legal_cell_except_the_start(self) -> None:
        """With a 2 on E2 you can reach D1 spending 1+1; no exact bridge roll needed."""
        game = _game()
        _place(game, P1, "E2")
        game.roll(forced=2)
        self.assertIn("E1", game.legal_next())
        self.assertIn("D2", game.legal_next())
        self.assertEqual(game.step("E1").remaining, 1)
        self.assertNotIn("E2", game.legal_next())  # starting cell
        self.assertIn("D1", game.legal_next())
        outcome = game.step("D1")
        self.assertTrue(outcome.ok)
        self.assertEqual(outcome.remaining, 0)
        self.assertEqual(outcome.cell, "D1")

    def test_bridge_taken_mid_move(self) -> None:
        game = _game()
        _place(game, P1, "A2")
        game.roll(forced=3)
        game.step("A3")
        self.assertEqual(game.legal_next(), ["B1"])  # A2 is the starting cell
        outcome = game.step("B1")
        self.assertEqual((outcome.ok, outcome.remaining), (True, 0))

    def test_bridge_more_expensive_than_remaining_is_illegal(self) -> None:
        game = _game()
        game.roll(forced=3)
        game.step("A4")
        outcome = game.step("E1")  # costs 3, only 2 left
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.remaining, 2)

    def test_dead_end_is_illegal(self) -> None:
        """From A2 with a 2, A3 leaves 1 unspendable step (A2 is the start, B1 costs 2)."""
        game = _game()
        _place(game, P1, "A2")
        game.roll(forced=2)
        self.assertNotIn("A3", game.legal_next())
        self.assertFalse(game.step("A3").ok)

    def test_only_the_final_cell_reveals(self) -> None:
        game = _game(A2="diamond")
        game.roll(forced=2)
        passing = game.step("A2")
        self.assertIsNone(passing.token)
        self.assertFalse(game.status().diamond_found)
        landing = game.step("A3")
        self.assertEqual(landing.token, "blank")

    def test_blocked_player_passes_the_turn(self) -> None:
        game = _game()
        _place(game, P1, "A3")
        _place(game, P3, "A2")
        _place(game, P2, "B1")
        # P1 on A3: A2 and B1 are occupied, so nothing can be spent.
        rolled = game.roll(forced=1)
        self.assertEqual(rolled.value, 1)
        self.assertTrue(rolled.blocked)
        self.assertEqual(rolled.next_player, P2)
        self.assertEqual(game.remaining(), 0)
        self.assertEqual(game.current_player(), P2)


class StatusTest(unittest.TestCase):
    def test_status_follows_the_turn(self) -> None:
        game = _game()
        st = game.status()
        self.assertEqual((st.current_player, st.phase, st.movements, st.remaining), (P1, "playing", 0, 0))
        game.roll(forced=2)
        mid = game.step("A2")
        self.assertEqual(mid.next_player, P1)  # the turn is still open
        st = game.status()
        self.assertEqual((st.movements, st.remaining), (2, 1))
        end = game.step("A3")
        self.assertEqual(end.next_player, P2)
        self.assertEqual(end.skipped, [])
        st = game.status()
        self.assertEqual((st.current_player, st.movements, st.remaining), (P2, 0, 0))

    def test_player_state_reports_home_and_cell(self) -> None:
        game = _game()
        _move(game, 1, "A2")
        view = game.player_state(P1)
        self.assertEqual((view.id, view.home, view.cell), (P1, "A1", "A2"))
        self.assertFalse(view.has_diamond or view.has_horseshoe or view.skip)

class TokenTest(unittest.TestCase):
    def test_coin_gives_an_extra_roll(self) -> None:
        """Landing on a coin rolls again from that cell, without pressing the button."""
        game = _game(A2="coin")
        outcome = _move(game, 1, "A2")
        self.assertEqual(outcome.token, "coin")
        self.assertTrue(outcome.extra_roll)
        self.assertEqual(game.current_player(), P1)
        game.roll(forced=1)
        self.assertNotIn("A2", game.legal_next())  # new starting cell
        self.assertEqual(sorted(game.legal_next()), ["A1", "A3", "A5"])
        outcome = game.step("A3")
        self.assertFalse(outcome.extra_roll)
        self.assertEqual(game.current_player(), P2)

    def test_pirate_sends_you_home_before_the_diamond(self) -> None:
        game = _game(A2="pirate", C1="pirate")
        outcome = _move(game, 1, "A2")
        self.assertEqual(outcome.token, "pirate")
        self.assertEqual(outcome.cell, "A1")
        self.assertFalse(outcome.won)
        # The pirate stays active and sends you to YOUR home, not the nearest one.
        _place(game, P3, "C2")
        _move(game, 1, "C3")  # P2
        game.roll(forced=1)  # P3, from C2 to C1
        outcome = game.step("C1")
        self.assertEqual(outcome.token, "pirate")
        self.assertEqual(outcome.cell, "A1")
        self.assertEqual(game.player_state(P3).cell, "A1")

    def test_pirates_turn_off_after_the_diamond(self) -> None:
        game = _game(A2="diamond", C2="pirate")
        outcome = _move(game, 1, "A2")
        self.assertEqual(outcome.token, "diamond")
        self.assertTrue(game.status().diamond_found)
        self.assertEqual(game.status().carrier, P1)
        self.assertEqual(game._tiles["A2"].kind, "blank")  # noqa: SLF001
        outcome = _move(game, 1, "C2")  # P2
        self.assertEqual(outcome.token, "pirate_off")
        self.assertEqual(outcome.cell, "C2")

    def test_horseshoe_only_counts_after_the_diamond(self) -> None:
        game = _game(A2="horseshoe", C2="horseshoe", C3="diamond")
        self.assertEqual(_move(game, 1, "A2").token, "horseshoe_off")  # P1, before the diamond
        self.assertEqual(_move(game, 1, "C3").token, "diamond")  # P2
        _move(game, 1, "A4")  # P3
        self.assertEqual(_move(game, 1, "C2").token, "horseshoe")  # P4
        self.assertFalse(game.player_state(P1).has_horseshoe)
        self.assertTrue(game.player_state(P4).has_horseshoe)

    def test_carrier_does_not_get_the_horseshoe(self) -> None:
        game = _game(A2="diamond", A5="horseshoe")
        _move(game, 1, "A2")  # P1 takes the diamond
        _move(game, 1, "C2")
        _move(game, 1, "A4")
        _move(game, 1, "C3")
        self.assertEqual(_move(game, 1, "A5").token, "horseshoe_off")  # P1
        self.assertFalse(game.player_state(P1).has_horseshoe)

    def test_good_tokens_turn_off_after_landing(self) -> None:
        """Spent coins and horseshoes publish coin_off and horseshoe_off."""
        game = _game(A2="coin", C1="diamond", A5="horseshoe")
        _move(game, 1, "A2")  # P1: coin
        _move(game, 1, "A5")  # P1, extra roll
        _place(game, P1, "B1")
        _move(game, 2, "C2", "C1")  # P2: diamond
        _move(game, 1, "A2")  # P3: spent coin
        self.assertEqual(game._tiles["A2"].spent, True)  # noqa: SLF001
        self.assertEqual(game.current_player(), P4)  # no extra roll

        game2 = _game(A2="coin")
        _move(game2, 1, "A2")
        game2.roll(forced=1)
        game2.step("A3")
        _move(game2, 1, "C2")
        outcome = _move(game2, 1, "A2")  # P3
        self.assertEqual(outcome.token, "coin_off")
        self.assertFalse(outcome.extra_roll)

        game3 = _game(C3="diamond", A2="horseshoe", A4="horseshoe")
        _move(game3, 1, "A4")  # P1, before the diamond: switched off
        _move(game3, 1, "C3")  # P2, diamond
        self.assertEqual(_move(game3, 1, "A2").token, "horseshoe")  # P3
        _move(game3, 1, "C2")  # P4
        _place(game3, P3, "A5")
        _place(game3, P1, "A1")
        game3.roll(forced=1)  # P1
        self.assertEqual(game3.step("A4").token, "horseshoe_off")

class ShipwreckTest(unittest.TestCase):
    def test_shipwreck_skips_the_next_turn(self) -> None:
        game = _game(A2="shipwreck")
        self.assertEqual(_move(game, 1, "A2").token, "shipwreck")
        self.assertTrue(game.player_state(P1).skip)
        _move(game, 1, "C2")  # P2
        _move(game, 1, "A4")  # P3
        outcome = _move(game, 1, "C3")  # P4 ends: P1 is skipped automatically
        self.assertEqual(outcome.skipped, [P1])
        self.assertEqual(outcome.next_player, P2)
        self.assertEqual(game.current_player(), P2)
        self.assertFalse(game.player_state(P1).skip)
        self.assertEqual(game.player_state(P1).cell, "A2")

if __name__ == "__main__":
    unittest.main()