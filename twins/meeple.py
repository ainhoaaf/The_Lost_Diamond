"""Gemelo de un meeple.

Habla con el mismo broker y los mismos JSON que firmware/meeple.
Sirve para probar las reglas antes de tener el ESP-01.

Cuando esté hecho:

- Publica `lobby/join` con `--mac`.
- Lee `Game_status.current_mac` y, si coincide, se considera en turno.
- Publica `Players/Player_N/move` solo cuando el UID (o la casilla) cambia.
- Espera `result` con el mismo `event_id` antes de enviar otro movimiento.

Uso:

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
    print("Pendiente: join, comparar current_mac y publicar un UID solo al cambiar.")


if __name__ == "__main__":
    main()
