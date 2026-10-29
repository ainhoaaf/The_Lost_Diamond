"""Une el broker con `engine.Game`.

Cuando esté hecho, el flujo de un turno será:

1. El meeple publica su MAC en `lobby/join` y queda como Player_N.
2. La estación publica en `Station/button`.
3. El PC tira el dado, actualiza `Game_status` y `Station/display`.
4. El meeple activo publica `Players/Player_N/move` con un event_id.
5. El PC responde en `Players/Player_N/result` con el mismo event_id.
6. Si la casilla es válida, actualiza `Game_status` y el estado de ese jugador.
"""

from __future__ import annotations

from lost_diamond.engine.game import Game


class MqttAdapter:
    def __init__(self, game: Game) -> None:
        self.game = game

    def start(self, host: str, port: int = 1883) -> None:
        """Conecta con Mosquitto y se suscribe a los topics de las placas."""
        raise NotImplementedError
