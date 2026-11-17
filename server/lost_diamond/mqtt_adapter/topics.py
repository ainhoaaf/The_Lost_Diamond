"""Topic names from docs/mqtt.md.

The MAC only shows up under `lobby/` and, once assigned, in the
`current_mac` field of `Game_status`. In the game a player is `Player_1` …
`Player_4`.
"""

PREFIX = "lostdiamond"

JOIN = f"{PREFIX}/lobby/join"
GAME_STATUS = f"{PREFIX}/Game_status"
STATION_BUTTON = f"{PREFIX}/Station/button"
STATION_DISPLAY = f"{PREFIX}/Station/display"
STATION_BUZZER = f"{PREFIX}/Station/buzzer"


def assign(mac: str) -> str:
    return f"{PREFIX}/lobby/assign/{mac}"


def lobby_status(mac: str) -> str:
    return f"{PREFIX}/lobby/status/{mac}"


def player_state(player_id: str) -> str:
    return f"{PREFIX}/Players/{player_id}"


def player_move(player_id: str) -> str:
    return f"{PREFIX}/Players/{player_id}/move"


def player_result(player_id: str) -> str:
    return f"{PREFIX}/Players/{player_id}/result"
