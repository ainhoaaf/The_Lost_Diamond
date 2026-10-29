"""Topics de `docs/mqtt.md`. El id de jugador es 1, 2, 3 o 4."""

PREFIX = "lostdiamond"

JOIN = f"{PREFIX}/lobby/join"
GAME_STATE = f"{PREFIX}/game/state"
DICE = f"{PREFIX}/game/dice"
EVENT = f"{PREFIX}/game/event"
BUTTON = f"{PREFIX}/station/button"
DISPLAY = f"{PREFIX}/station/display"
BUZZER = f"{PREFIX}/station/buzzer"


def assign(mac: str) -> str:
    return f"{PREFIX}/lobby/assign/{mac}"


def position(player_id: str) -> str:
    return f"{PREFIX}/players/{player_id}/position"


def status(player_id: str) -> str:
    return f"{PREFIX}/players/{player_id}/status"


def move_result(player_id: str) -> str:
    return f"{PREFIX}/players/{player_id}/move_result"
