# Estación

Sketch: `station.ino`

1. Herramientas → Placa → ESP32 Dev Module.
2. Librería: PubSubClient.
3. Edita `config.h` con la misma red y la misma IP del broker que los meeples.
4. Cable USB propio: el ESP32 no trae el cable en el kit.

La pantalla del kit es serie (TX/RX) y pasa por el conversor de nivel. El zumbador es pasivo. Los pines se dejan en `-1` hasta tener el esquema.

FreeRTOS reparte el trabajo para que el tic del diamante no congele el botón ni MQTT:

- `taskMqtt` es la única que toca el cliente MQTT.
- `taskButton` solo marca que han pulsado.
- `taskBuzzer` hace sonar el patrón que manda el PC.
- `loop` pinta la pantalla.
