"""JSON de cada mensaje MQTT.

Aquí se construyen y se leen los cuerpos de `protocol/examples/`. El adaptador
no arma diccionarios a mano: llama a estas funciones. El motor no importa este
archivo.
"""

from __future__ import annotations

from typing import Any


def join(event_id: str, timestamp: int, mac: str) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "player_id": "",
        "timestamp": timestamp,
        "action": "join",
        "mac": mac,
    }


def assign(event_id: str, timestamp: int, player_id: str, home: str, token: str) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "player_id": player_id,
        "timestamp": timestamp,
        "action": "assign",
        "home": home,
        "token": token,
    }


def game_status(
    *,
    current_player: str,
    current_mac: str,
    diamond_found: bool,
    carrier: str | None,
    movements: int,
    remaining: int,
    token: str | None,
    phase: str = "playing",
    num_players: int = 4,
) -> dict[str, Any]:
    return {
        "num_players": num_players,
        "current_player": current_player,
        "current_mac": current_mac,
        "diamond_found": diamond_found,
        "carrier": carrier,
        "phase": phase,
        "movements": movements,
        "remaining": remaining,
        "token": token,
    }


def player_state(
    *,
    player_id: str,
    home: str,
    cell: str,
    turn: int,
    movements: int,
    has_diamond: bool,
    has_horseshoe: bool,
    skip: bool,
) -> dict[str, Any]:
    return {
        "id": player_id,
        "home": home,
        "cell": cell,
        "turn": turn,
        "movements": movements,
        "has_diamond": has_diamond,
        "has_horseshoe": has_horseshoe,
        "skip": skip,
    }


def move(event_id: str, timestamp: int, player_id: str, uid: str, cell: str = "") -> dict[str, Any]:
    return {
        "event_id": event_id,
        "player_id": player_id,
        "timestamp": timestamp,
        "action": "move",
        "uid": uid,
        "cell": cell,
    }


def result(
    event_id: str,
    timestamp: int,
    player_id: str,
    ok: bool,
    reason: str,
    cell: str,
    remaining: int,
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "player_id": player_id,
        "timestamp": timestamp,
        "action": "move_result",
        "ok": ok,
        "reason": reason,
        "cell": cell,
        "remaining": remaining,
    }


def button(event_id: str, timestamp: int) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "player_id": "",
        "timestamp": timestamp,
        "action": "button",
        "pressed": True,
    }


def display(line1: str, line2: str, *, diamond: bool = False) -> dict[str, Any]:
    return {"line1": line1, "line2": line2, "diamond": diamond}


def buzzer(pattern: str) -> dict[str, Any]:
    return {"pattern": pattern}
