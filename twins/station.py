"""Gemelo de la estación central.

El Enter hace de botón. La terminal hace de pantalla y de zumbador.
Los mensajes son los de firmware/station.

Cuando esté hecho:

- Publica `Station/button` al pulsar Enter.
- Pinta `Station/display` (line1, line2, diamond).
- Escribe el patrón de `Station/buzzer`.
- No tira el dado: el número lo publica el PC.

Uso:

    python3 station.py --broker 127.0.0.1
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemelo de la estación")
    parser.add_argument("--broker", default="127.0.0.1")
    args = parser.parse_args()
    print("Estación gemela")
    print(f"Broker: {args.broker}")
    print("Pendiente: publicar Station/button y pintar Station/display.")


if __name__ == "__main__":
    main()
