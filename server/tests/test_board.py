"""Pruebas del mapa.

Comprueba nombres de casilla, casas, puentes, coste de un salto y que un
puente se puede pagar a mitad de camino. Se ejecuta desde `server/`:

    python3 -m unittest tests.test_board
"""

from __future__ import annotations

import unittest

from lost_diamond.engine.board import (
    BRIDGES,
    HOMES,
    all_cells,
    bridges_from,
    hops_from,
    island_neighbors,
    step_cost,
)
from lost_diamond.engine.tokens import POOL, playable_cells


class BoardTest(unittest.TestCase):
    def test_sixteen_cells(self) -> None:
        cells = all_cells()
        self.assertEqual(len(cells), 16)
        self.assertEqual(len(set(cells)), 16)

    def test_homes_are_the_two_corners(self) -> None:
        self.assertEqual(HOMES, ("A1", "C4"))
        self.assertTrue(set(HOMES).issubset(all_cells()))

    def test_token_pool_fills_the_other_cells(self) -> None:
        self.assertEqual(len(POOL), 14)
        self.assertEqual(set(playable_cells()), set(all_cells()) - set(HOMES))
        self.assertEqual(POOL.count("diamond"), 1)
        self.assertEqual(POOL.count("pirate"), 2)
        self.assertEqual(POOL.count("horseshoe"), 2)
        self.assertEqual(POOL.count("coin"), 2)
        self.assertEqual(POOL.count("shipwreck"), 2)
        self.assertEqual(POOL.count("blank"), 5)

    def test_known_bridges_are_bidirectional(self) -> None:
        links = bridges_from()
        self.assertIn(("B1", 2), links["A3"])
        self.assertIn(("A3", 2), links["B1"])
        self.assertIn(("C3", 3), links["D2"])
        self.assertIn(("D1", 1), links["E1"])
        self.assertEqual(len(BRIDGES), 10)

    def test_no_diagonals_inside_islands(self) -> None:
        neighbors = island_neighbors()
        self.assertEqual(neighbors["A3"], {"A2"})
        self.assertEqual(neighbors["B1"], {"B3"})
        self.assertNotIn("B2", neighbors["B1"])
        self.assertEqual(neighbors["C4"], {"C2", "C3"})

    def test_step_cost_is_one_inside_an_island(self) -> None:
        self.assertEqual(step_cost("A1", "A2"), 1)
        self.assertEqual(step_cost("E2", "E1"), 1)
        self.assertIsNone(step_cost("A1", "C4"))
        self.assertIsNone(step_cost("B1", "B2"))

    def test_step_cost_uses_the_bridge_price(self) -> None:
        self.assertEqual(step_cost("A3", "B1"), 2)
        self.assertEqual(step_cost("A4", "E1"), 3)
        self.assertEqual(step_cost("E2", "D2"), 1)
        self.assertEqual(hops_from("A5")["B2"], 2)
        self.assertEqual(hops_from("A5")["D1"], 3)

    def test_a_bridge_can_be_paid_mid_path(self) -> None:
        self.assertEqual(step_cost("E2", "D2"), 1)
        self.assertIn("E1", hops_from("E2"))
        self.assertEqual(step_cost("E1", "D1"), 1)


if __name__ == "__main__":
    unittest.main()
