# Firmware

Dos sketches independientes. Cada uno se abre con el Arduino IDE desde su carpeta.

| Carpeta | Placa en el IDE | Qué hace |
|---|---|---|
| `meeple/` | Generic ESP8266 Module | Lee el NFC y enciende el LED de turno. |
| `station/` | ESP32 Dev Module | Botón, pantalla, zumbador y LED, con FreeRTOS. |

Hay que instalar el soporte de placas ESP8266 y ESP32 en el gestor de placas, y la librería PubSubClient en el gestor de librerías.

Los pines no están escritos todavía. Se anotan en `docs/hardware/` cuando el primer cableado funcione, y se copian a los sketches.

El ESP-01 se programa con el módulo programador. Se desconecta la alimentación antes de mover el interruptor de modo. El ESP32 se programa por el cable USB.
