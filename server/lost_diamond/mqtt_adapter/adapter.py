"""Une el broker con `engine.Game`.

Este archivo es el único que habla con Mosquitto. Recibe hechos de las placas
y publica lo que la pantalla, el LED y el zumbador tienen que hacer.

Flujo de un turno:

1. Un meeple publica `lobby/join` con su MAC. Se le asigna el mismo Player_N
   si esa MAC ya jugaba.
2. El PC publica `Game_status` con `current_player` y `current_mac`. El meeple
   compara esa MAC con la suya y enciende el verde.
3. La estación publica `Station/button`. El PC llama a `Game.roll` y publica
   el número en `Game_status` y en `Station/display`.
4. El meeple publica `Players/Player_N/move` solo cuando cambia el UID.
   El PC traduce el UID con `nfc.cell_for`, llama a `Game.step` y responde
   en `result` con el mismo `event_id`.
5. Si el salto es ilegal, publica `reason` y no gasta pasos.
6. A los 15 segundos sin UID nuevo, publica un aviso de "muévete". El turno
   sigue abierto.
7. Cuando `remaining` llega a 0, publica el código de la ficha
   (`diamond`, `pirate`, `coin`…). La estación elige dibujo y música.

Las confirmaciones de la estación se enganchan aquí cuando el grupo cierre el JSON.
"""

from __future__ import annotations

from lost_diamond.engine.game import Game


class MqttAdapter:
    def __init__(self, game: Game) -> None:
        self.game = game

    def start(self, host: str, port: int = 1883) -> None:
        """Conecta con Mosquitto y se suscribe a join, button, move y LWT."""
        raise NotImplementedError
