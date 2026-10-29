# Hardware

Aquí irán los esquemas, cuando el cableado esté probado. Hasta entonces no hay números de pin en el código: se rellenan en los sketches.

## Meeple (uno por jugador, cuatro en total)

- ESP-01
- Lector PN532 por I2C
- LED de turno
- Tag NFC en cada casilla del tablero

El ESP-01 se programa con su módulo programador. Hay que quitar la alimentación antes de cambiar el interruptor de modo. La alimentación tiene que aguantar los picos del WiFi.

## Estación (una para los cuatro)

- ESP32
- Pantalla gráfica serie 128×64, por TX/RX, con conversor de nivel
- Botón
- Zumbador pasivo
- LED
- FreeRTOS: una tarea para MQTT, otra para el botón, otra para el zumbador y otra para la pantalla

El zumbador no puede usar esperas que congelen el botón ni MQTT. El tic del diamante vive en su propia tarea.

## Red

Los cuatro meeples y la estación usan IP estática en una red local pequeña. El broker corre en el PC.
