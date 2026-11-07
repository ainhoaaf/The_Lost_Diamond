# The Lost Diamond

Juego de mesa electrónico para cuatro jugadores. Los meeples leen casillas NFC, la estación central tira el dado y el PC aplica las reglas por MQTT.

Las primeras partidas se juegan con gemelos en Python. Cuando una partida entera funciona, se sustituye cada gemelo por su placa sin cambiar los mensajes.

## Carpetas

| Carpeta | Qué hay |
|---|---|
| `docs/` | Reglamento, tablero, topics MQTT y esquemas. El enunciado de la asignatura está en `docs/enunciado/` y los documentos del grupo en `docs/nuestro juego/`. |
| `protocol/examples/` | Un JSON de ejemplo por cada mensaje. |
| `server/` | Motor de la partida y el programa que habla con el broker. |
| `twins/` | Meeples y estación simulados. Publican los mismos mensajes que las placas. |
| `firmware/meeple/` | Proyecto PlatformIO del ESP-01 (NFC y LED). |
| `firmware/station/` | Proyecto PlatformIO del ESP32 (pantalla, botón, zumbador, FreeRTOS). |
| `broker/` | Configuración de Mosquitto para la red local. |

## Orden de trabajo

1. Implementar `server/lost_diamond/engine/game.py` y `tests/test_game.py`, sin red.
2. Implementar `mqtt_adapter/adapter.py` y `tests/test_turn.py`.
3. Jugar una partida con `twins/` contra Mosquitto.
4. Sustituir un gemelo por una placa, con el mapa NFC que ya está en `nfc_map.example.json`.

## Placas

Los dos programas se abren con VS Code y la extensión PlatformIO. La placa, la IP y las librerías están en el `README.md` de cada carpeta. El framework es Arduino, que en el ESP32 ya incluye FreeRTOS.

## Servidor

```bash
cd server
python3 -m unittest tests.test_board tests.test_nfc tests.test_turn tests.test_game
python3 -m lost_diamond.main
```

El mapa, los UID y los JSON del turno ya se comprueban. El motor de la partida todavía no juega: `Game` está escrito como contrato en `server/lost_diamond/engine/game.py`. Cómo partir el trabajo en dos está en `server/README.md`.
