"""Meeple twin.

Publishes lobby/join with its MAC. When Game_status carries that same MAC it
is this meeple's turn. Type a cell (B2) or a UID and it is published once;
the controller answers on Players/Player_N/result with the same event_id.
The twin also prints its own cell whenever the controller moves it (pirate).

    python3 meeple.py --broker 127.0.0.1 --mac AA:BB:CC:DD:EE:01
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from lost_diamond.mqtt_adapter import codec, topics

CELL = re.compile(r"^[A-E][1-5]$")


def main() -> None:
    parser = argparse.ArgumentParser(description="Meeple twin")
    parser.add_argument("--broker", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--mac", default="AA:BB:CC:DD:EE:01")
    args = parser.parse_args()
    mac = args.mac.strip().upper()
    state = {"player": "", "waiting": "", "cell": ""}

    def on_message(client: mqtt.Client, userdata: object, message: mqtt.MQTTMessage) -> None:
        raw = message.payload.decode("utf-8")
        if not raw:
            return
        body = json.loads(raw)
        if message.topic == topics.assign(mac):
            state["player"] = body["player_id"]
            print(f"You are {body['player_id']}, home {body['home']}.")
            client.subscribe(topics.player_result(state["player"]), qos=1)
            client.subscribe(topics.player_state(state["player"]), qos=1)
        elif message.topic == topics.GAME_STATUS:
            if body.get("phase") == "finished":
                print(f"Game over. Last token: {body.get('token')}.")
                return
            mine = body.get("current_mac") == mac
            text = "Your turn." if mine else f"{body.get('current_player')}'s turn."
            if body.get("movements"):
                text += f" Roll {body['movements']}, {body.get('remaining')} left."
            if body.get("token"):
                text += f" Token: {body['token']}."
            print(text)
        elif state["player"] and message.topic == topics.player_state(state["player"]):
            if body.get("cell") != state["cell"]:
                state["cell"] = body.get("cell", "")
                print(f"You are on {state['cell']}.")
        elif state["waiting"] and body.get("event_id") == state["waiting"]:
            state["waiting"] = ""
            print("OK." if body.get("ok") else f"No: {body.get('reason')}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(args.broker, args.port, keepalive=60)
    client.subscribe(topics.assign(mac), qos=1)
    client.subscribe(topics.GAME_STATUS, qos=1)
    client.loop_start()
    client.publish(
        topics.JOIN,
        json.dumps(codec.join("1", int(time.time()), mac)),
        qos=1,
    )
    print(f"Meeple {mac} on {args.broker}. Type a cell (B2) or a UID.")
    try:
        while True:
            line = input("> ").strip()
            if not line:
                continue
            if not state["player"]:
                print("Not assigned yet.")
                continue
            if state["waiting"]:
                print("Still waiting for the previous answer.")
                continue
            event_id = str(time.time_ns() // 1_000_000)
            state["waiting"] = event_id
            if CELL.fullmatch(line.upper()):
                body = codec.move(event_id, int(time.time()), state["player"], "", line.upper())
            else:
                body = codec.move(event_id, int(time.time()), state["player"], line, "")
            client.publish(topics.player_move(state["player"]), json.dumps(body), qos=1)
    except (KeyboardInterrupt, EOFError):
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
