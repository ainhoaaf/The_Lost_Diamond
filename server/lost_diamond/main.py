"""Arranque del controlador.

Cuando el adaptador esté hecho, este archivo crea un `Game`, lo pasa a
`MqttAdapter` y se queda escuchando el broker. Hoy solo comprueba que el
paquete se importa.
"""

from __future__ import annotations


def main() -> None:
    print("The Lost Diamond")
    print("El mapa y los mensajes JSON ya están.")
    print("Siguiente paso: implementar lost_diamond.engine.game.")


if __name__ == "__main__":
    main()
