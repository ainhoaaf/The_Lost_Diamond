# Reglamento

Cuatro jugadores. Un dado de 1 a 3. Dieciséis casillas en cinco islas. El mapa de islas es siempre el mismo. Las fichas de las otras catorce casillas se sortean al empezar cada partida.

## Casas

Las casas son siempre A1 (arriba a la izquierda) y C4 (abajo a la derecha). No tienen ficha de evento: sin diamante ni herradura, caer en una casa no hace nada.

Dos jugadores empiezan en A1 y dos en C4. En el turno se alternan las casas: uno de arriba, uno de abajo, uno de arriba y uno de abajo. Puede empezar cualquiera de las dos casas. Estar en casa al empezar no es ganar.

En A1 y en C4 pueden coincidir varios jugadores. En el resto de casillas solo cabe uno: no se puede pasar ni parar si hay alguien.

## Movimiento

El número del dado es un presupuesto de pasos. Cada salto a una casilla vecina de la misma isla cuesta 1. Un puente se puede tomar a mitad de camino si quedan al menos tantos pasos como su coste. Sobran los pasos que no se gasten en ese salto, y se siguen gastando en el siguiente.

No hace falta que el dado coincida con el coste de un puente al empezar el turno. Ejemplo: en E2, un 2 puede ser un paso a E1 y el puente de coste 1 hasta D1.

La casilla de la que sales en esa tirada no se vuelve a pisar. El movimiento acaba en otra casilla, cualquiera que sea legal cuando los pasos llegan a 0.

Si lo dejas en una casilla que no toca, la estación avisa y lo colocas bien. La tirada no cambia y el turno no se pierde. La posición oficial no cambia hasta que el salto es válido.

El PC cuenta 15 segundos desde que publica el dado, y vuelve a contar cada vez que llega un UID nuevo. Si se cumple el tiempo, publica un aviso de «muévete». Ese aviso no cancela el turno.

Solo tiene efecto la casilla donde los pasos llegan a 0. Pasar por encima no descubre la ficha. Se puede cruzar una casa. Solo se gana si el movimiento acaba en una casa y tienes el diamante o el derecho de la herradura.

## Fichas

El programa conoce el sorteo desde el principio. En la mesa las fichas están ocultas y, al caer, se anuncian a los cuatro. El PC publica un código para la estación:

| Ficha | Cuántas | Efecto | Al pisarla |
|---|---|---|---|
| Diamante | 1 | El primero que lo pisa se lo queda. Código `diamond`. | La casilla pasa a blanca. |
| Pirata | 2 | Antes del diamante te manda a la casa en la que empezaste. Código `pirate`. Después de salir el diamante, las dos publican `pirate_off`. | Sigue activo hasta que sale el diamante. Se puede volver a pisar. |
| Herradura | 2 | Sirve solo si la pisas sin llevar el diamante y con el diamante ya descubierto. Te guarda el derecho de ganar al llegar a una casa. Código `horseshoe`. Si no vale, `horseshoe_off`. | Se apaga. |
| Moneda | 2 | Tiras otra vez en el mismo turno, desde esa casilla, sin pulsar el botón. Código `coin`. Si ya se gastó, `coin_off`. | Se apaga. |
| Naufragio | 2 | El movimiento cuenta. La próxima vez que te toque, no tiras. Código `shipwreck`. | Sigue activo. Se puede volver a pisar. |
| Blanca | 5 | No hace nada. Código `blank`. | Sigue en blanco. |

Las fichas buenas (moneda, herradura) quedan desactivadas después de la primera caída. Pirata y naufragio siguen activos. Al salir el diamante, los piratas se apagan en las dos casillas. Una herradura que aún no se ha pisado solo da el derecho si se pisa después del diamante.

Quien ya tiene el derecho y pisa la otra herradura, también la apaga. El derecho no se pierde al salir de la casilla.

El pirata no gana la partida: ocurre antes de tener el diamante, y te lleva a tu casa de salida.

## Victoria

Quien lleva el diamante gana al acabar un movimiento en A1 o en C4. Cualquier otro gana solo si consiguió una herradura después de salir el diamante y acaba un movimiento en A1 o en C4 antes de que lo haga el portador. Da igual en qué casa empezaste.

Quien ya no puede ganar sigue jugando y puede bloquear casillas. Se juega hasta que alguien gana.
