"""Station twin.

Enter publishes Station/button. Whatever reaches the screen and the buzzer
is printed in this terminal. The PC rolls the die, not the station.

    python3 station.py --broker 127.0.0.1
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from lost_diamond.mqtt_adapter import codec, topics


def main() -> None:
    parser = argparse.ArgumentParser(description="Station twin")
    parser.add_argument("--broker", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()

    def on_message(_client: mqtt.Client, _userdata: object, message: mqtt.MQTTMessage) -> None:
        body = json.loads(message.payload.decode("utf-8") or "{}")
        if message.topic == topics.STATION_DISPLAY:
            diamond = "  [diamond found]" if body.get("diamond") else ""
            print(f"Screen: {body.get('line1', '')} | {body.get('line2', '')}{diamond}")
        elif message.topic == topics.STATION_BUZZER:
            print(f"Buzzer: {body.get('pattern', '')}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(args.broker, args.port, keepalive=60)
    client.subscribe(topics.STATION_DISPLAY, qos=0)
    client.subscribe(topics.STATION_BUZZER, qos=0)
    client.loop_start()
    print(f"Station on {args.broker}. Press Enter to roll the die.")
    try:
        while True:
            input()
            event_id = str(time.time_ns() // 1_000_000)
            client.publish(
                topics.STATION_BUTTON,
                json.dumps(codec.button(event_id, int(time.time()))),
                qos=1,
            )
    except (KeyboardInterrupt, EOFError):
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
