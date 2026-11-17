"""Controller entry point.

Creates the real `Game`, clears the retained messages and listens to
Mosquitto.

    python3 -m lost_diamond.main
    python3 -m lost_diamond.main --broker 127.0.0.1
"""

from __future__ import annotations

import argparse

from lost_diamond.engine.game import Game
from lost_diamond.mqtt_adapter.adapter import MqttAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description="The Lost Diamond controller")
    parser.add_argument("--broker", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()
    print("The Lost Diamond")
    MqttAdapter(Game()).start(args.broker, args.port)


if __name__ == "__main__":
    main()
