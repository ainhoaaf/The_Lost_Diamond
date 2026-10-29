# MQTT

El PC es el único sitio donde viven las reglas. Las placas cuentan hechos y obedecen órdenes. Los gemelos usan estos mismos mensajes.

El broker es Mosquitto, en el ordenador, sin cifrado, en la red local. La configuración está en `broker/mosquitto.conf`.

Los ejemplos copiables están en `protocol/examples/`.

## Topics

| Topic | Quién publica | Qué es |
|---|---|---|
| `lostdiamond/lobby/join` | Meeple | Su MAC, al encender. |
| `lostdiamond/lobby/assign/{mac}` | PC | Número de jugador, casa y token. |
| `lostdiamond/game/state` | PC, retenido | Turno, si el diamante ya salió, portador. |
| `lostdiamond/game/dice` | PC | Tirada de 1 a 3. La estación la muestra. |
| `lostdiamond/game/event` | PC | Diamante, herradura, pirata, moneda, naufragio o victoria. |
| `lostdiamond/players/{id}/position` | Meeple | UID del NFC, o la casilla si es un gemelo. Lleva `seq`. |
| `lostdiamond/players/{id}/status` | PC | Si le toca. El meeple enciende o apaga el LED. |
| `lostdiamond/players/{id}/move_result` | PC | Casilla aceptada o aviso para colocarla bien. |
| `lostdiamond/station/button` | Estación | Han pulsado el botón. |
| `lostdiamond/station/display` | PC | Dos líneas y el icono del diamante. |
| `lostdiamond/station/buzzer` | PC | Patrón de sonido: dado, diamante, tic, herradura o silencio. |

`{id}` es `1`, `2`, `3` o `4`. `{mac}` es la MAC con dos puntos, tal como la envía el meeple.

Posición y botón van en QoS 1. Pantalla y zumbador pueden ir en QoS 0. `game/state` se publica retenido para que, si la estación se reinicia a mitad de la partida, recupere el turno y el diamante.

El dado lo genera el PC. La estación solo lo enseña.

## Lectura NFC

Cada casilla tiene un tag. El meeple lee solo durante su turno, al dejarlo en la casilla, y luego apaga el lector. Así dos meeples pueden estar en la misma casa sin leer a la vez.

Una lectura repetida del mismo tag lleva el mismo `seq` y el PC la ignora. El mapa UID → casilla se rellenará cuando se lean los tags de verdad. La plantilla está en `server/lost_diamond/nfc_map.example.json`.
