# Firmware

Dos proyectos de PlatformIO, con el framework Arduino. Se abren con VS Code y la extensión PlatformIO.

| Carpeta | Entorno | Qué hace |
|---|---|---|
| `meeple/` | `esp01_1m` o `esp01` | Lee el NFC y enciende el LED de turno. |
| `station/` | `esp32dev` | Botón, pantalla, zumbador y LED, con FreeRTOS. |

Librerías, en los dos `platformio.ini`: ArduinoJson 6.21 y PubSubClient 2.8.

```bash
cd firmware/meeple
pio run -t upload
pio device monitor

cd firmware/station
pio run -t upload
pio device monitor
```

El ESP-01 se programa con el módulo programador. Se desconecta la alimentación antes de mover el interruptor de modo. Si el módulo es de 512 KB y no arranca, se sube con `pio run -e esp01 -t upload`.

El ESP32 se programa por el cable USB. En el Arduino IDE esa placa se llama DOIT ESP32 DEVKIT V1.

La IP de cada placa está en `include/config.h`. Tiene que ser distinta, y el broker es la IP del PC.
