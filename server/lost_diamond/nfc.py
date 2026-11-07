"""Traduce el UID de un tag a la casilla del juego.

El meeple real publica el UID. El gemelo puede publicar ya la casilla.
`normalize` quita espacios y pone el UID en mayúsculas, como en
`nfc_map.example.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

MAP_PATH = Path(__file__).with_name("nfc_map.example.json")


def normalize(uid: str) -> str:
    return uid.replace(" ", "").upper()


def load_map(path: Path | None = None) -> dict[str, str]:
    data = json.loads((path or MAP_PATH).read_text(encoding="utf-8"))
    return {normalize(uid): cell for uid, cell in data.items()}


def cell_for(uid: str, mapping: dict[str, str] | None = None) -> str | None:
    table = mapping if mapping is not None else load_map()
    return table.get(normalize(uid))
