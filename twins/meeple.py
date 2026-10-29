"""Gemelo de un meeple.

Habla con el mismo broker y los mismos JSON que firmware/meeple.
Sirve para probar las reglas antes de tener el ESP-01.

Uso previsto, cuando el adaptador esté conectado:

    python3 meeple.py --broker 127.0.0.1 --mac AA:BB:CC:DD:EE:01
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemelo de un meeple")
    parser.add_argument("--broker", default="127.0.0.1")
    parser.add_argument("--mac", default="AA:BB:CC:DD:EE:01")
    args = parser.parse_args()
    print(f"Meeple gemelo {args.mac}")
    print(f"Broker: {args.broker}")
    print("Pendiente: publicar lobby/join y players/{id}/position.")


if __name__ == "__main__":
    main()
