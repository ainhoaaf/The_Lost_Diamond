# Servidor — trabajo de las dos de Python

Esto no está hecho. Lo que hay en el código es el esqueleto, el mapa y el
contrato. Si llamas a `Game().roll()` petará. `python3 -m lost_diamond.main`
solo imprime que el siguiente paso es implementar el motor.

Somos dos. Una persona hace que la partida se pueda jugar en memoria
(Persona A). La otra hace que esa partida se vea en el broker, en los gemelos
y más adelante en las placas (Persona B). El firmware Arduino lo hacen
otras personas del grupo.

El reglamento está en `docs/rules.md`. Los mensajes, en `docs/mqtt.md` y
`protocol/examples/`. El mapa, en `docs/board.md`.

```bash
cd server
python3 -m unittest tests.test_board tests.test_nfc tests.test_turn tests.test_game
python3 -m lost_diamond.main
```

Hoy pasan el mapa, los UID y el JSON. Las pruebas de reglas y de un turno
real están escritas y en `skip` hasta que alguien las implemente.

## Qué hay ya y qué falta

| Archivo | Estado | De quién |
|---|---|---|
| `lost_diamond/engine/board.py` | Hecho. Mapa, vecinas, puentes, `step_cost`. | Las dos lo leen. No lo reescribas. |
| `lost_diamond/engine/tokens.py` | Hecho. Las 14 fichas y `reveal_code`. | A lo usa. |
| `lost_diamond/engine/game.py` | Vacío. Solo las firmas y `StepOutcome`. | **A lo escribe.** |
| `lost_diamond/nfc.py` | Hecho. UID → casilla. | B lo usa. |
| `lost_diamond/nfc_map.example.json` | Hecho. Los 16 tags. | B lo usa. |
| `lost_diamond/mqtt_adapter/topics.py` | Hecho. Nombres de topics. | B lo usa. |
| `lost_diamond/mqtt_adapter/codec.py` | Hecho. Arma el JSON. | B lo usa. |
| `lost_diamond/mqtt_adapter/adapter.py` | Vacío. No se conecta al broker. | **B lo escribe.** |
| `lost_diamond/main.py` | Vacío. Solo un print. | **B lo escribe.** |
| `tests/test_board.py` | Hecho y en verde. | Nadie lo rompe. |
| `tests/test_nfc.py` | Hecho y en verde. | Nadie lo rompe. |
| `tests/test_game.py` | Escrito, todo en `skip`. | **A quita los skip al ir implementando.** |
| `tests/test_turn.py` | El JSON ya se prueba. El turno está en `skip`. | **B quita los skip.** |
| `twins/meeple.py` | Vacío. Un print. | **B lo escribe.** |
| `twins/station.py` | Vacío. Un print. | **B lo escribe.** |

La frontera es `Game`. A no importa MQTT. B no decide fichas, turnos ni
victoria: llama a `roll` y a `step` y publica el `StepOutcome`.

## Persona A — reglas

Archivos suyos: `lost_diamond/engine/game.py` y `tests/test_game.py`.
Puede leer `board.py` y `tokens.py`. No entra en `mqtt_adapter/` ni en `twins/`.

Tiene que hacer, en este orden:

1. `new_game(seats)`. `seats` es `Player_1` → `A1` o `C4`, dos en cada casa.
   Baraja las 14 fichas sobre las casillas que no son casa. El turno alterna
   casa de arriba y casa de abajo. Puede empezar cualquiera de las dos.
   Estar en casa al empezar no es ganar. En A1 y C4 pueden coincidir varios.
   En el resto, solo uno: no se pasa ni se para si hay alguien.
2. `current_player()`, `roll()`, `remaining()`. El dado es 1, 2 o 3 y queda
   guardado como presupuesto de pasos. Si ese jugador tiene `skip` por un
   naufragio, no tira y el turno pasa al siguiente.
3. `legal_next()` y `step(casilla)`. Un salto a una vecina de la misma isla
   cuesta 1. Un puente se puede tomar a mitad de camino si quedan al menos
   tantos pasos como su coste (2 o 3, o 1 entre E y D). No se vuelve a la
   casilla de salida de esa tirada. Un salto ilegal: `ok=False`, `reason`
   relleno, los pasos no se gastan, la posición no cambia. El movimiento
   acaba en cualquier casilla legal cuando `remaining` llega a 0. Solo esa
   casilla revela ficha. Cruzar una casa no gana.
4. Al llegar a 0, aplicar la ficha y poner `token` con el código:
   - Diamante: ese jugador lo lleva. La casilla queda blanca. Los dos piratas
     pasan a `pirate_off`.
   - Pirata, si el diamante no ha salido: vuelve a **su** casa de salida
     (A1 o C4, la que le tocó al empezar). No gana. La casilla pirata sigue
     activa.
   - Herradura: da derecho a ganar solo si el diamante ya salió y no lleva
     el diamante. Luego se apaga (`horseshoe` o `horseshoe_off`).
   - Moneda: `extra_roll=True`. Se tira otra vez **desde esa casilla**, en
     el mismo turno, sin botón. Luego se apaga (`coin` / `coin_off`).
   - Naufragio: el movimiento cuenta. La próxima vez que le toque, no tira.
     La casilla sigue activa.
   - Blanca o casa: no hace nada.
5. Victoria. `won=True` y `winner()` devuelve ese `Player_N` si acaba el
   movimiento en A1 o C4 con el diamante, o con herradura válida antes que
   el portador. Quien ya no puede ganar sigue en la partida y puede bloquear.

Cómo se sabe que A ha terminado: en `test_game.py` se quitan los `skip` uno
a uno y todos pasan. No hace falta Mosquitto ni las placas.

Para probar sin azar, A tiene que poder fijar el sorteo y las tiradas en los
tests (si no, no se puede comprobar un pirata o un diamante a propósito).
Si para eso añade un argumento opcional a `new_game` o a `roll`, **se lo
dice a B** porque B llama a esas funciones.

## Persona B — broker y gemelos

Archivos suyos: `lost_diamond/mqtt_adapter/adapter.py`, `lost_diamond/main.py`,
`tests/test_turn.py`, `twins/meeple.py`, `twins/station.py`.
Usa `codec.py`, `topics.py` y `nfc.py`, que ya están. No cambia las reglas
de `game.py`.

Mientras A no tenga un `Game` de verdad, B trabaja con un `Game` falso que
devuelve un `StepOutcome` inventado. Así puede publicar sin esperar a las
fichas. Cuando A tenga `test_game.py` en verde, B tira el falso y enchufa
el de verdad. **Ese cambio se habla el mismo día.**

Tiene que hacer, en este orden:

1. `lobby/join` con la MAC → asignar `Player_1` … `Player_4` y publicar
   `lobby/assign/{mac}`. La misma MAC recupera al mismo jugador. Guardar
   MAC ↔ `Player_N`. Publicar `Game_status` con `current_player` y
   `current_mac`. El meeple compara esa MAC con la suya y enciende el verde.
   Si el WiFi se corta, el Last Will llega a `lobby/status/{mac}`. Al volver,
   el mismo `Player_N`. No se reparte otro.
2. `Station/button` → `Game.roll()`. Publicar el número en `Game_status`
   (`movements` y `remaining`) y en `Station/display`. El dado lo tira el
   PC, no la estación.
3. `Players/Player_N/move` → traducir el UID con `nfc.cell_for` (el gemelo
   puede traer ya `cell`). Llamar a `Game.step`. Responder en `result` con
   el **mismo** `event_id`. Un UID repetido no llama otra vez a `step`. Un
   `event_id` repetido se responde y no se aplica dos veces. Si `ok` es
   falso, publicar `reason` y no cambiar la posición.
4. Reloj de 15 segundos desde que se publica el dado, y otra vez cada UID
   nuevo. Si se cumple, publicar «muévete» en la pantalla. **No cancela el
   turno.** Este reloj vive en el adaptador, no en `Game`.
5. Cuando `remaining` llega a 0, publicar `token` en `Game_status` (y el
   texto / zumbador en `Station/display` y `Station/buzzer`). Si
   `extra_roll` es verdadero, llamar otra vez a `Game.roll()` **sin esperar
   al botón**. Si `won` es verdadero, cerrar la partida (`phase` de fin).
6. Gemelos. `station.py`: Enter publica el botón; la terminal pinta
   `display` y el patrón de `buzzer`. `meeple.py`: join con `--mac`, lee
   `current_mac`, publica un UID solo cuando cambia, espera `result` con el
   mismo `event_id`.
7. `main.py`: crea un `Game`, lo pasa al adaptador y se queda escuchando
   Mosquitto (`127.0.0.1` en local).

Cómo se sabe que B ha terminado su parte a solas: en `test_turn.py` se
quitan los `skip` y pasan **sin Mosquitto**, con un cliente MQTT falso.
Después se levanta el broker (`broker/README.md`) y se juega un turno con
un meeple gemelo y la estación gemela.

B no implementa piratas, herraduras ni victoria. Si el `StepOutcome` dice
`token="pirate"`, B publica `pirate` y listo. La estación Arduino elige el
dibujo y la música a partir de ese código.

## Contrato — lo que las dos tienen que respetar

`Game` expone esto. B no llama a nada más. A no cambia las firmas sin
hablarlo.

```text
new_game(seats)           seats: Player_N → "A1" o "C4"
current_player() -> str
roll() -> int             1, 2 o 3. También deja remaining.
remaining() -> int
legal_next() -> list[str]
step(cell) -> StepOutcome
winner() -> str | None
```

`StepOutcome`:

| Campo | Tipo | Qué significa |
|---|---|---|
| `ok` | bool | El salto es legal. Si es falso, la ficha no se ha movido. |
| `reason` | str | Aviso para la pantalla. Vacío si ha ido bien. |
| `cell` | str | Casilla oficial del jugador después de este salto. |
| `remaining` | int | Pasos que le quedan de esta tirada. |
| `token` | str o None | Código de ficha solo cuando `remaining` llega a 0. |
| `extra_roll` | bool | Moneda: B tiene que volver a llamar a `roll()` ya. |
| `won` | bool | Este salto ha ganado. B cierra la partida. |

Códigos de `token` (no se inventan otros): `diamond`, `pirate`,
`pirate_off`, `horseshoe`, `horseshoe_off`, `coin`, `coin_off`,
`shipwreck`, `blank`.

`reason` de momento: `destino_ilegal` cuando el salto no toca. Si A necesita
otro (`ocupada`, `no_es_tu_turno`, `uid_desconocido`), **se lo dice a B
antes** y se añade al JSON de `result` y a la frase de pantalla.

A trabaja con nombres de casilla (`B2`, `E1`). B traduce UID → casilla y
luego llama a `step("B2")`. El motor no ve UIDs ni MACs. El adaptador no
calcula costes de puentes.

## En qué hay que comunicarse

Hablar **antes** de tocar nada de esta lista. Un commit por su lado no basta.

1. **Cambiar `StepOutcome` o las firmas de `Game`.** Si A necesita un campo
   (`skip_next`, `sent_home`, lista de casillas legales) o cambiar
   `roll()` / `new_game()`, B se entera el mismo día. Si no, el adaptador
   se rompe.
2. **Textos de `reason`.** A decide el código. B lo pinta. Lista común,
   empezando por `destino_ilegal`.
3. **Textos de pantalla y zumbador.** B publica `line1`, `line2` y el
   patrón (`dice`, `diamond`, `tick`, `horseshoe`, `silence`, y el aviso
   de 15 s). Ponerse de acuerdo en una frase por ficha y por error para
   decírselo luego a Arduino.
4. **`extra_roll`.** A pone el flag. B llama a `roll()` otra vez, sin
   botón. Si A prefiere que `roll()` se llame solo y el flag no exista,
   se habla y se cambia el contrato.
5. **Naufragio / `skip`.** A lo aplica dentro de `roll()`: si toca y tiene
   skip, no tira y pasa. B tiene que publicar el nuevo `current_player` /
   `current_mac` cuando el jugador activo cambia, también en ese caso.
   Avisarse la primera vez que un test de naufragio pase.
6. **Cuándo enchufar el `Game` de verdad.** A avisa cuando `test_game.py`
   esté verde. Ese día B quita el `Game` falso. No se mezcla a medias.
7. **Sorteo y dado fijos en tests.** Si A añade `new_game(..., tokens=...)`
   o `roll(forced=2)`, B usa la misma firma (o ignora los extras). No
   tener dos `new_game` distintos.
8. **Casilla ocupada.** A rechaza el salto si no es casa y hay alguien.
   Decir qué `reason` usa (`ocupada`) para que B lo muestre.
9. **Confirmaciones de Arduino.** La base publicará “pantalla ok / error”
   cuando el grupo cierre el JSON. Eso lo engancha B. A no espera. Hasta
   entonces B no inventa un formato: se pregunta al equipo de placas.
10. **Git.** Cada una commitea solo sus archivos. Si las dos tocan
    `game.py` o `adapter.py` el mismo día, aviso. Hacer `git pull` antes
    de empujar. No reescribir `board.py`, `tokens.py`, `codec.py`,
    `topics.py` ni `nfc_map.example.json` sin decirlo: son el suelo común.

Con Arduino (las dos, sobre todo B) hay que decirles, cuando el contrato
esté estable:

- Publicamos `current_mac` para el LED verde.
- Publicamos `token` al revelar, no un texto libre.
- El botón solo avisa; el dado lo tira el PC.
- El meeple publica el UID **solo cuando cambia**.
- Un `move` se reenvía hasta que llega `result` con el mismo `event_id`.
- Ellos nos pasan el JSON de confirmaciones y errores cuando lo tengan.

## Cuándo se junta el trabajo

Hasta que A tenga los tests de `Game` en verde, cada una avanza en su
carpeta.

El día del encaje:

1. B enchufa el `Game` real en el adaptador.
2. Mosquitto en el PC.
3. Cuatro `twins/meeple.py` (MACs `AA:BB:CC:DD:EE:01` … `04`) y un
   `twins/station.py`.
4. Una partida entera: sorteo, varios saltos, diamante, herradura, moneda,
   pirata o naufragio, llegada a casa.

Si algo falla, se mira primero si `Game.step` devolvió lo esperado (A) o
si el adaptador publicó otro topic (B).

Las placas reales entran después, una a una, con el mismo broker y los
mismos JSON. Eso ya es trabajo de B con el equipo de Arduino, no de A.

## Lo que cada una no hace

A no: conectar Mosquitto, publicar topics, contar 15 segundos, leer UIDs,
escribir gemelos, decidir pines ni hablar el formato de confirmación de la
pantalla.

B no: barajar fichas, calcular puentes, decidir si un salto es legal,
aplicar pirata/moneda/herradura, decidir quién gana.

Si una duda es “¿esta casilla es legal?” es de A. Si es “¿qué topic y qué
JSON?” es de B. Si es “¿cambiamos el contrato?” es de las dos, antes de
escribir código.
