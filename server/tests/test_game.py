"""Pruebas del motor, sin red.

Cuando `Game` esté implementado, quitar los skip. Cada test fija el sorteo
y las tiradas para no depender del azar.

    python3 -m unittest tests.test_game
"""

from __future__ import annotations

import unittest

from lost_diamond.engine.game import Game


def _seats() -> dict[str, str]:
    return {
        "Player_1": "A1",
        "Player_2": "C4",
        "Player_3": "A1",
        "Player_4": "C4",
    }


class GameTest(unittest.TestCase):
    @unittest.skip("Implementar Game.new_game")
    def test_new_game_seats_two_players_on_each_home(self) -> None:
        game = Game()
        game.new_game(_seats())
        self.assertIn(game.current_player(), _seats())

    @unittest.skip("Implementar Game.roll y Game.step")
    def test_illegal_step_does_not_spend_the_roll(self) -> None:
        """Un salto que no toca avisa y deja los mismos pasos."""
        raise NotImplementedError

    @unittest.skip("Implementar el presupuesto de pasos")
    def test_turn_ends_on_any_legal_cell_except_the_start(self) -> None:
        """Con un 2 en E2 se puede ir a D1 gastando 1+1. No hace falta un 2 exacto de puente."""
        raise NotImplementedError

    @unittest.skip("Implementar moneda")
    def test_coin_gives_an_extra_roll(self) -> None:
        """Al caer en moneda se tira otra vez desde esa casilla, sin pulsar el botón."""
        raise NotImplementedError

    @unittest.skip("Implementar pirata")
    def test_pirate_sends_you_home_before_the_diamond(self) -> None:
        raise NotImplementedError

    @unittest.skip("Implementar diamante")
    def test_pirates_turn_off_after_the_diamond(self) -> None:
        raise NotImplementedError

    @unittest.skip("Implementar herradura")
    def test_horseshoe_only_counts_after_the_diamond(self) -> None:
        raise NotImplementedError

    @unittest.skip("Implementar naufragio")
    def test_shipwreck_skips_the_next_turn(self) -> None:
        raise NotImplementedError

    @unittest.skip("Implementar fichas que se apagan")
    def test_good_tokens_turn_off_after_landing(self) -> None:
        """Moneda y herradura gastadas publican coin_off y horseshoe_off."""
        raise NotImplementedError

    @unittest.skip("Implementar victoria")
    def test_diamond_carrier_wins_on_either_home(self) -> None:
        raise NotImplementedError

    @unittest.skip("Implementar victoria")
    def test_horseshoe_wins_if_home_before_the_carrier(self) -> None:
        raise NotImplementedError


if __name__ == "__main__":
    unittest.main()
