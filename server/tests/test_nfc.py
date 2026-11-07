"""Pruebas del mapa UID → casilla.

Los 16 tags de docs/hardware/uids_tablero.md tienen que resolver al nombre
nuevo del tablero (A1…A5, B1…B3, E, D, C).
"""

from __future__ import annotations

import unittest

from lost_diamond.engine.board import all_cells
from lost_diamond.nfc import cell_for, load_map, normalize


class NfcMapTest(unittest.TestCase):
    def test_sixteen_unique_uids(self) -> None:
        mapping = load_map()
        self.assertEqual(len(mapping), 16)
        self.assertEqual(set(mapping.values()), set(all_cells()))

    def test_spaces_in_the_tag_are_ignored(self) -> None:
        self.assertEqual(normalize("04 1D 33 AE 87 26 81"), "041D33AE872681")
        self.assertEqual(cell_for("04 1D 33 AE 87 26 81"), "A1")
        self.assertEqual(cell_for("0471AEAD872681"), "C4")
        self.assertEqual(cell_for("04 35 69 46 C7 2A 81"), "B2")


if __name__ == "__main__":
    unittest.main()
