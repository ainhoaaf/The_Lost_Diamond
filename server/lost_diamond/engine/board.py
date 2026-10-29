"""Mapa fijo. Los costes y las vecinas están explicados en docs/board.md."""

from __future__ import annotations

HOMES = ("A1", "B4")

ISLANDS = {
    "A": ("A1", "A2", "A3", "A4", "A5"),
    "M": ("M1", "M2", "M3"),
    "S": ("S1", "S2"),
    "T": ("T1", "T2"),
    "B": ("B1", "B2", "B3", "B4"),
}

# Paso de coste 1. Sin diagonales.
ISLAND_LINKS = (
    ("A1", "A2"),
    ("A2", "A3"),
    ("A1", "A4"),
    ("A2", "A5"),
    ("A4", "A5"),
    ("M1", "M3"),
    ("M2", "M3"),
    ("S1", "S2"),
    ("T1", "T2"),
    ("B1", "B2"),
    ("B1", "B3"),
    ("B2", "B4"),
    ("B3", "B4"),
)

# (origen, destino, coste). El puente vale en los dos sentidos.
BRIDGES = (
    ("A3", "M1", 2),
    ("A5", "M2", 2),
    ("M2", "B1", 2),
    ("M3", "B2", 2),
    ("A4", "S1", 3),
    ("A5", "T1", 3),
    ("T1", "B1", 3),
    ("T2", "B3", 3),
    ("S1", "T1", 1),
    ("S2", "T2", 1),
)


def all_cells() -> tuple[str, ...]:
    cells: list[str] = []
    for island in ISLANDS.values():
        cells.extend(island)
    return tuple(cells)


def island_neighbors() -> dict[str, set[str]]:
    neighbors = {cell: set() for cell in all_cells()}
    for left, right in ISLAND_LINKS:
        neighbors[left].add(right)
        neighbors[right].add(left)
    return neighbors


def bridges_from() -> dict[str, set[tuple[str, int]]]:
    links = {cell: set() for cell in all_cells()}
    for left, right, cost in BRIDGES:
        links[left].add((right, cost))
        links[right].add((left, cost))
    return links
