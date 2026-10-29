import unittest

from lost_diamond.engine.board import (
    BRIDGES,
    HOMES,
    all_cells,
    bridges_from,
    island_neighbors,
)
from lost_diamond.engine.tokens import POOL


class BoardTest(unittest.TestCase):
    def test_sixteen_cells(self) -> None:
        cells = all_cells()
        self.assertEqual(len(cells), 16)
        self.assertEqual(len(set(cells)), 16)

    def test_homes_are_the_two_corners(self) -> None:
        self.assertEqual(HOMES, ("A1", "B4"))
        self.assertTrue(set(HOMES).issubset(all_cells()))

    def test_token_pool_fills_the_other_cells(self) -> None:
        self.assertEqual(len(POOL), 14)
        self.assertEqual(POOL.count("diamond"), 1)
        self.assertEqual(POOL.count("pirate"), 2)
        self.assertEqual(POOL.count("horseshoe"), 2)
        self.assertEqual(POOL.count("coin"), 2)
        self.assertEqual(POOL.count("shipwreck"), 2)
        self.assertEqual(POOL.count("blank"), 5)

    def test_known_bridges_are_bidirectional(self) -> None:
        links = bridges_from()
        self.assertIn(("M1", 2), links["A3"])
        self.assertIn(("A3", 2), links["M1"])
        self.assertIn(("B3", 3), links["T2"])
        self.assertIn(("T1", 1), links["S1"])
        self.assertEqual(len(BRIDGES), 10)

    def test_no_diagonals_inside_islands(self) -> None:
        neighbors = island_neighbors()
        self.assertEqual(neighbors["A3"], {"A2"})
        self.assertEqual(neighbors["M1"], {"M3"})
        self.assertNotIn("M2", neighbors["M1"])
        self.assertEqual(neighbors["B4"], {"B2", "B3"})


if __name__ == "__main__":
    unittest.main()
