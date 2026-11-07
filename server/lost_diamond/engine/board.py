"""Mapa fijo.

Nombres de casilla, vecinas de la misma isla y puentes. El motor llama a
`step_cost` para saber cuántos pasos gasta un salto. Este archivo no decide
turnos, fichas ni victoria.
"""

from __future__ import annotations

HOMES = ("A1", "C4")

ISLANDS = {
    "A": ("A1", "A2", "A3", "A4", "A5"),
    "B": ("B1", "B2", "B3"),
    "E": ("E1", "E2"),
    "D": ("D1", "D2"),
    "C": ("C1", "C2", "C3", "C4"),
}

# Paso de coste 1. Sin diagonales. B1 no toca a B2.
ISLAND_LINKS = (
    ("A1", "A2"),
    ("A2", "A3"),
    ("A1", "A4"),
    ("A2", "A5"),
    ("A4", "A5"),
    ("B1", "B3"),
    ("B2", "B3"),
    ("E1", "E2"),
    ("D1", "D2"),
    ("C1", "C2"),
    ("C1", "C3"),
    ("C2", "C4"),
    ("C3", "C4"),
)

# (origen, destino, coste). El puente vale en los dos sentidos.
BRIDGES = (
    ("A3", "B1", 2),
    ("A5", "B2", 2),
    ("B2", "C1", 2),
    ("B3", "C2", 2),
    ("A4", "E1", 3),
    ("A5", "D1", 3),
    ("D1", "C1", 3),
    ("D2", "C3", 3),
    ("E1", "D1", 1),
    ("E2", "D2", 1),
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


def hops_from(cell: str) -> dict[str, int]:
    """Casillas a un salto y el coste de cada una."""
    hops = {neighbor: 1 for neighbor in island_neighbors()[cell]}
    for dest, cost in bridges_from()[cell]:
        hops[dest] = cost
    return hops


def step_cost(origin: str, dest: str) -> int | None:
    """Coste de un salto. None si origin y dest no son adyacentes."""
    return hops_from(origin).get(dest)
