"""Opens the four meeples and the station, each in its own Terminal window.

Each one can also be opened alone:

    python3 meeple.py --mac AA:BB:CC:DD:EE:01
    python3 station.py

Mosquitto and the controller must already be running:

    python3 -m lost_diamond.main
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MACS = tuple(f"AA:BB:CC:DD:EE:0{number}" for number in range(1, 5))


def open_terminal(command: str) -> None:
    escaped = command.replace("\\", "\\\\").replace('"', '\\"')
    subprocess.run(
        ["osascript", "-e", f'tell application "Terminal" to do script "{escaped}"'],
        check=False,
    )


def main() -> None:
    folder = Path(__file__).resolve().parent
    python = sys.executable
    commands = [
        f'cd "{folder}" && "{python}" meeple.py --mac {mac}'
        for mac in MACS
    ]
    commands.append(f'cd "{folder}" && "{python}" station.py')
    if sys.platform != "darwin":
        print("Run each command in its own terminal:")
        for command in commands:
            print(command)
        return
    for command in commands:
        open_terminal(command)
    print("Five windows: four meeples and the station.")


if __name__ == "__main__":
    main()
