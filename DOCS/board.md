# Tablero

Dieciséis casillas. El paso entre vecinas de la misma isla cuesta 1. Un puente se toma entero, con el coste de la tabla.

```text
A1 —— A2 —— A3          M1
|      |                |
A4 —— A5           M2 —— M3

S1      T1          B1 —— B2
|       |           |      |
S2      T2          B3 —— B4
```

A1 y B4 son las casas. No entran en el sorteo.

No hay diagonal. A3 solo toca a A2. M1 no toca a M2: se pasa por M3.

## Puentes

| Puente | Coste |
|---|---|
| A3–M1, A5–M2, M2–B1, M3–B2 | 2 |
| A4–S1, A5–T1, T1–B1, T2–B3 | 3 |
| S1–T1, S2–T2 | 1 |

Las dos islas grandes no se tocan. La mediana no toca a las pequeñas.

## Consecuencias del dado

En las islas pequeñas, un 2 no tiene destino: el único paso es el vecino, no se puede volver al origen y ningún puente cuesta 2.

En M3, un 3 no tiene destino: sus puentes cuestan 2 y, sin pisar otra vez M3, no hay un paseo de tres pasos.

En M1, un 3 puede ser M3 → M2 → M3. En M2, un 3 puede ser M3 → M1 → M3.

Estos datos están repetidos en `server/lost_diamond/engine/board.py`. Si se cambia un puente, se cambia en los dos sitios.
