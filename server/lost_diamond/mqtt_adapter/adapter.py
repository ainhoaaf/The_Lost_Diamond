"""Une el broker con `engine.Game`.

Cuando esté hecho, el flujo de un turno será:

1. La estación publica en `station/button`.
2. El PC tira el dado y publica `game/dice` y `station/display`.
3. El meeple activo publica `players/{id}/position`.
4. El PC responde en `players/{id}/move_result`.
5. Si la casilla es válida, publica el evento y pasa el turno.
"""

from __future__ import annotations

from lost_diamond.engine.game import Game


class MqttAdapter:
    def __init__(self, game: Game) -> None:
        self.game = game

    def start(self, host: str, port: int = 1883) -> None:
        """Conecta con Mosquitto y se suscribe a los topics de las placas."""
        raise NotImplementedError
