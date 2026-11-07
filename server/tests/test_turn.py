"""Un turno publicado, sin Mosquitto.

El cliente MQTT se sustituye por una lista de mensajes. Así se comprueba el
adaptador: botón → dado → UID → result → ficha.

    python3 -m unittest tests.test_turn
"""

from __future__ import annotations

import unittest

from lost_diamond.mqtt_adapter import codec
from lost_diamond.mqtt_adapter import topics


class CodecTest(unittest.TestCase):
    def test_game_status_carries_mac_and_remaining(self) -> None:
        body = codec.game_status(
            current_player="Player_2",
            current_mac="AA:BB:CC:DD:EE:02",
            diamond_found=False,
            carrier=None,
            movements=3,
            remaining=2,
            token=None,
        )
        self.assertEqual(body["current_mac"], "AA:BB:CC:DD:EE:02")
        self.assertEqual(body["remaining"], 2)
        self.assertIsNone(body["token"])

    def test_move_and_result_share_the_event_id(self) -> None:
        sent = codec.move("4", 1710000004, "Player_1", "04356946C72A81")
        answer = codec.result("4", 1710000005, "Player_1", True, "", "B2", 1)
        self.assertEqual(sent["event_id"], answer["event_id"])
        self.assertEqual(answer["remaining"], 1)

    def test_player_topics_use_player_id(self) -> None:
        self.assertEqual(topics.player_move("Player_1"), "lostdiamond/Players/Player_1/move")
        self.assertEqual(topics.GAME_STATUS, "lostdiamond/Game_status")


class TurnTest(unittest.TestCase):
    @unittest.skip("Implementar MqttAdapter con un cliente falso")
    def test_button_publishes_a_roll(self) -> None:
        """Al llegar Station/button, el adaptador publica movements 1, 2 o 3."""
        raise NotImplementedError

    @unittest.skip("Implementar MqttAdapter con un cliente falso")
    def test_new_uid_calls_game_step(self) -> None:
        """Un UID nuevo se traduce a casilla y se responde con el mismo event_id."""
        raise NotImplementedError

    @unittest.skip("Implementar MqttAdapter con un cliente falso")
    def test_same_uid_is_ignored(self) -> None:
        """El segundo mensaje con el mismo UID no llama otra vez a step."""
        raise NotImplementedError

    @unittest.skip("Implementar el aviso de 15 segundos")
    def test_idle_warning_does_not_end_the_turn(self) -> None:
        raise NotImplementedError


if __name__ == "__main__":
    unittest.main()
