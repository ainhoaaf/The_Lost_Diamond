# MQTT

El PC es el único sitio donde viven las reglas. Las placas cuentan hechos y obedecen órdenes. Los gemelos usan estos mismos mensajes.

El broker es Mosquitto, en el ordenador, sin cifrado, en la red local. La configuración está en `broker/mosquitto.conf`.

Los ejemplos copiables están en `protocol/examples/`.

## Árbol

La forma es la de clase: un estado de partida y un nodo por jugador. La MAC solo sirve para entrar. Cuando el PC reconoce al dispositivo, pasa a ser `Player_1` … `Player_4`.

```text
lostdiamond/
  lobby/
    join                      meeple → PC
    assign/{mac}              PC → ese meeple
    status/{mac}              retenido. Last Will: online true/false
  Game_status                 retenido. PC → todos
  Players/
    Player_1                  retenido. Estado de ese jugador
    Player_1/move             meeple → PC
    Player_1/result           PC → ese meeple
    Player_2 …
  Station/
    button                    estación → PC
    display                   PC → estación
    buzzer                    PC → estación
```

`Game_status` lleva el turno, si el diamante ya salió y el portador. El campo `movements` es la tirada de esta partida: 0 si aún no se ha tirado, y 1, 2 o 3 cuando hay dado. En la diapositiva el ejemplo llega hasta 6. Aquí el dado es de 1 a 3.

`Players/Player_N` es la vista de ese jugador: casa, casilla, si le toca (`turn` 1 o 0), si lleva el diamante o el derecho de la herradura, y si pierde el próximo turno (`skip`).

## Mensajes de acción

Todo lo que cambia la partida lleva estos cuatro campos, para poder ignorar un duplicado:

```json
{
  "event_id": "4",
  "player_id": "Player_1",
  "timestamp": 1710000000,
  "action": "move"
}
```

`action` es `join`, `assign`, `move`, `move_result` o `button`. El PC guarda el último `event_id` de cada jugador y no aplica dos veces el mismo.

## QoS

Las acciones y el estado van en QoS 1. La pantalla y el zumbador van en QoS 0: si se pierde un dibujo, el siguiente lo reemplaza.

`Game_status`, `Players/Player_N` y `lobby/status/{mac}` se publican retenidos. Una placa que se reinicia lee el último estado y no se inventa la partida.

La diapositiva pide QoS 2 para las acciones que no se pueden repetir. `PubSubClient`, la librería que usa el firmware, no implementa QoS 2 y además publica en QoS 0. El PC, con Python, sí publica en QoS 1. En el meeple, un `move` se vuelve a enviar hasta que llega `result` con el mismo `event_id`. El PC, si ve ese `event_id` otra vez, responde y no mueve la ficha de nuevo.

## Caídas

Cada meeple conecta con Last Will en `lobby/status/{mac}` y el mensaje `{"online": false}`. Si el WiFi se corta, el broker avisa al PC. Al volver, el meeple publica la misma MAC en `lobby/join` y recupera su `Player_N`. No se reparte otro jugador.

## Lectura NFC

Cada casilla tiene un tag. El meeple lee solo durante su turno, al dejarlo en la casilla, y luego deja quieto el lector. Así dos meeples pueden estar en la misma casa sin leer a la vez.

El mapa UID → casilla se rellenará cuando se lean los tags. La plantilla está en `server/lost_diamond/nfc_map.example.json`. En el gemelo el campo `cell` ya viene relleno.

## Estación

El callback MQTT solo copia el mensaje en una cola. Otra tarea lo interpreta y actualiza pantalla, LED y zumbador. La pantalla del kit es serie, con conversor de nivel. No va por I2C.
