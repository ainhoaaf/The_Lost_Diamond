# The Lost Diamond

Juego de mesa electrónico para cuatro jugadores. Los meeples leen casillas NFC, la estación central tira el dado y el PC aplica las reglas por MQTT.

Las primeras partidas se juegan con gemelos en Python. Cuando una partida entera funciona, se sustituye cada gemelo por su placa sin cambiar los mensajes.

## Carpetas

| Carpeta | Qué hay |
|---|---|
| `docs/` | Reglamento, tablero, topics MQTT y, más adelante, esquemas eléctricos. |
| `protocol/examples/` | Un JSON de ejemplo por cada mensaje. |
| `server/` | Motor de la partida y el programa que habla con el broker. |
| `twins/` | Meeples y estación simulados. Publican los mismos mensajes que las placas. |
| `firmware/meeple/` | Sketch de Arduino del ESP-01 (NFC y LED). |
| `firmware/station/` | Sketch de Arduino del ESP32 (pantalla, botón, zumbador, FreeRTOS). |
| `broker/` | Configuración de Mosquitto para la red local. |
| `DOCS/` | Enunciado de la asignatura y los documentos del grupo. No es código. |

## Orden de trabajo

1. Cerrar el texto de `docs/` si cambia alguna regla.
2. Implementar `server/lost_diamond/engine/` y sus pruebas, sin red.
3. Conectar el adaptador MQTT y jugar una partida con `twins/`.
4. Abrir los sketches de `firmware/` y hacer que publiquen los JSON de `protocol/examples/`.

## Arduino

Cada sketch se abre solo, con el Arduino IDE. La placa y las librerías están en el `README.md` de cada carpeta.

## Servidor

```bash
cd server
python3 -m unittest tests.test_board
python3 -m lost_diamond.main
```

El motor de la partida todavía no juega: la estructura y el mapa ya están. El mapa se comprueba con el test de arriba.
