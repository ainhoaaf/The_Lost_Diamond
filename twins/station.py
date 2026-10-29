"""Gemelo de la estación central.

El Enter hace de botón. La terminal hace de pantalla y de zumbador.
Los mensajes son los de firmware/station.

Uso previsto, cuando el adaptador esté conectado:

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
    print("Pendiente: publicar station/button y pintar station/display.")


if __name__ == "__main__":
    main()
