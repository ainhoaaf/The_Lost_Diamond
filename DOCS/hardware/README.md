# Hardware

Los [UID del tablero](uids_tablero.md) están documentados por fila, columna y casilla.

Aquí irán los esquemas, cuando el cableado esté probado. Hasta entonces los pines del código están en `-1`, dentro de `firmware/*/include/config.h`.

La pantalla gráfica del kit va por el puerto serie y el conversor de nivel, no por I2C.

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
- FreeRTOS: MQTT, botón, lógica, zumbador, LED y pantalla. El callback solo encola.

El zumbador no puede usar esperas que congelen el botón ni MQTT. El tic del diamante vive en su propia tarea.

## Red

Los cuatro meeples y la estación usan IP estática en una red local pequeña. El broker corre en el PC.
