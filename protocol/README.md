# Ejemplos de mensajes

Cada archivo es el cuerpo JSON de un topic de `docs/mqtt.md`.

| Archivo | Topic |
|---|---|
| `join.json` | `lobby/join` |
| `assign.json` | `lobby/assign/{mac}` |
| `lwt.json` | `lobby/status/{mac}` |
| `game_status.json` | `Game_status` |
| `player_state.json` | `Players/Player_1` |
| `move.json` | `Players/Player_1/move` |
| `result.json` | `Players/Player_1/result` |
| `button.json` | `Station/button` |
| `display.json` | `Station/display` |
| `buzzer.json` | `Station/buzzer` |

En `move.json` el campo `cell` lo rellena el gemelo. La placa rellena `uid` y deja `cell` vacío: el PC traduce el UID con `server/lost_diamond/nfc_map.example.json`.

`buzzer.json` usa uno de estos patrones: `dice`, `diamond`, `tick`, `horseshoe`, `silence`.
