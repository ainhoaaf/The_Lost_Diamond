"""Fichas de las 14 casillas que no son casa.

`new_game` baraja `POOL` sobre esas casillas. `reveal_code` es el texto que
el PC publica cuando los pasos llegan a 0, para que la estación pinte y suene.

Moneda y herradura se apagan al pisarlas. Pirata y naufragio siguen activos.
Al salir el diamante, las dos casillas pirata pasan a `pirate_off`.
"""

from __future__ import annotations

POOL = (
    "diamond",
    "pirate",
    "pirate",
    "horseshoe",
    "horseshoe",
    "coin",
    "coin",
    "shipwreck",
    "shipwreck",
    "blank",
    "blank",
    "blank",
    "blank",
    "blank",
)

CONSUMED_ON_LANDING = frozenset({"diamond", "horseshoe", "coin"})
PERSISTENT = frozenset({"pirate", "shipwreck"})
CODES = (
    "diamond",
    "pirate",
    "pirate_off",
    "horseshoe",
    "horseshoe_off",
    "coin",
    "coin_off",
    "shipwreck",
    "blank",
)


def playable_cells() -> tuple[str, ...]:
    """Las 14 casillas que reciben ficha. Las casas A1 y C4 quedan fuera."""
    from lost_diamond.engine.board import HOMES, all_cells

    return tuple(cell for cell in all_cells() if cell not in HOMES)


def reveal_code(kind: str, *, diamond_found: bool, spent: bool) -> str:
    """Código que ve la estación al revelar una casilla."""
    if kind == "diamond":
        return "diamond"
    if kind == "blank":
        return "blank"
    if kind == "shipwreck":
        return "shipwreck"
    if kind == "pirate":
        return "pirate_off" if diamond_found else "pirate"
    if kind == "horseshoe":
        if spent or not diamond_found:
            return "horseshoe_off"
        return "horseshoe"
    if kind == "coin":
        return "coin_off" if spent else "coin"
    return "blank"
