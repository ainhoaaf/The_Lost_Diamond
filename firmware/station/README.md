# Estación

Proyecto PlatformIO del ESP32 (`esp32dev`). El código está en `src/main.cpp`.

`taskMqtt` es la única que usa el cliente MQTT. El callback copia el mensaje y lo deja en una cola. `taskLogic` lo interpreta. `taskDisplay`, `taskLed` y `taskBuzzer` leen el resultado. `taskButton` avisa por otra cola, y `taskMqtt` publica `lostdiamond/Station/button`.

`Serial.begin` se llama antes de crear las tareas. Lo que se escriba por el USB toma `serialMutex`. La pantalla del kit va por otro UART, con el conversor de nivel.

1. Cambia en `include/config.h` la misma red y la IP del broker que usan los meeples.
2. La IP de la estación es `192.168.1.20`.
3. Los pines siguen en `-1` hasta tener el esquema.
