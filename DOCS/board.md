# Tablero

Dieciséis casillas. El paso entre vecinas de la misma isla cuesta 1. Un puente se toma entero, con el coste de la tabla, y se puede pagar a mitad de camino si quedan pasos suficientes.

```text
A1 —— A2 —— A3          B1
|      |                |
A4 —— A5           B2 —— B3

E1      D1          C1 —— C2
|       |           |      |
E2      D2          C3 —— C4
```

A1 y C4 son las casas. No entran en el sorteo.

No hay diagonal. A3 solo toca a A2. B1 no toca a B2: se pasa por B3.

## Puentes

| Puente | Coste |
|---|---|
| A3–B1, A5–B2, B2–C1, B3–C2 | 2 |
| A4–E1, A5–D1, D1–C1, D2–C3 | 3 |
| E1–D1, E2–D2 | 1 |

Las dos islas grandes no se tocan. La mediana no toca a las pequeñas. Entrar desde A a E o a D cuesta 3.

Los UID de cada casilla están en `docs/hardware/uids_tablero.md`. El programa los lee en `server/lost_diamond/nfc_map.example.json`.

Estos datos están repetidos en `server/lost_diamond/engine/board.py`. Si se cambia un puente, se cambia en los dos sitios.
