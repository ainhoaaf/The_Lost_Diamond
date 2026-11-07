# MQTT

El PC es el único sitio donde viven las reglas. Las placas cuentan hechos y obedecen órdenes. Los gemelos usan estos mismos mensajes.

El broker es Mosquitto, en el ordenador, sin cifrado, en la red local. La configuración está en `broker/mosquitto.conf`.

Los ejemplos copiables están en `protocol/examples/`.

## Árbol

La forma es la de clase: un estado de partida y un nodo por jugador. La MAC solo sirve para entrar y para saber a quién le toca. Cuando el PC reconoce al dispositivo, pasa a ser `Player_1` … `Player_4`.

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

`Game_status` lleva el jugador activo, su MAC (`current_mac`), si el diamante ya salió, el portador, la tirada (`movements` 0–3), los pasos que quedan (`remaining`) y, al revelar, el código de la ficha (`token`). El meeple compara `current_mac` con la suya y enciende el verde.

`Players/Player_N` es la vista de ese jugador: casa, casilla, si le toca (`turn` 1 o 0), si lleva el diamante o el derecho de la herradura, y si pierde el próximo turno (`skip`).

## Turno

1. El PC publica `Game_status` con la MAC a la que le toca.
2. El jugador pulsa el botón. La estación publica `Station/button`.
3. El PC tira el dado y publica el número en `Game_status` y en `Station/display`.
4. El meeple publica `Players/Player_N/move` solo cuando el UID cambia.
5. El PC responde en `result` con el mismo `event_id`. Si el salto es ilegal, `ok` es falso, `reason` lleva el aviso y los pasos no se gastan.
6. Si pasan 15 segundos sin un UID nuevo, el PC publica un aviso de «muévete». El turno sigue abierto.
7. Cuando `remaining` llega a 0, el PC publica el código de la ficha. La estación elige dibujo y música.

Códigos de ficha: `diamond`, `pirate`, `pirate_off`, `horseshoe`, `horseshoe_off`, `coin`, `coin_off`, `shipwreck`, `blank`.

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

`PubSubClient` no implementa QoS 2 y publica en QoS 0. El PC, con Python, publica en QoS 1. En el meeple, un `move` se vuelve a enviar hasta que llega `result` con el mismo `event_id`. El PC, si ve ese `event_id` otra vez, responde y no mueve la ficha de nuevo.

## Caídas

Cada meeple conecta con Last Will en `lobby/status/{mac}` y el mensaje `{"online": false}`. Si el WiFi se corta, el broker avisa al PC. Al volver, el meeple publica la misma MAC en `lobby/join` y recupera su `Player_N`. No se reparte otro jugador.

## Lectura NFC

Cada casilla tiene un tag. El meeple publica el UID solo cuando cambia. El PC traduce UID → casilla con `server/lost_diamond/nfc_map.example.json`. En el gemelo el campo `cell` ya puede ir relleno.

## Estación

El callback MQTT solo copia el mensaje en una cola. Otra tarea lo interpreta y actualiza pantalla, LED y zumbador. La pantalla del kit es serie, con conversor de nivel. No va por I2C.

Las confirmaciones de la estación (pantalla pintada, zumbador sonado) se enganchan cuando el grupo cierre el JSON de esas respuestas.
