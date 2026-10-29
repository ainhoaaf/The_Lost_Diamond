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

1. Cerrar el texto de `docs/` si cambia alguna regla.
2. Implementar `server/lost_diamond/engine/` y sus pruebas, sin red.
3. Conectar el adaptador MQTT y jugar una partida con `twins/`.
4. Compilar `firmware/` con PlatformIO y hacer que publique los JSON de `protocol/examples/`.

## Placas

Los dos programas se abren con VS Code y la extensión PlatformIO. La placa, la IP y las librerías están en el `README.md` de cada carpeta. El framework es Arduino, que en el ESP32 ya incluye FreeRTOS.

## Servidor

```bash
cd server
python3 -m unittest tests.test_board
python3 -m lost_diamond.main
```

El motor de la partida todavía no juega: la estructura y el mapa ya están. El mapa se comprueba con el test de arriba.
