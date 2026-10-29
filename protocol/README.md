# Ejemplos de mensajes

Cada archivo es el cuerpo JSON de un topic de `docs/mqtt.md`.

En `position.json` el campo `cell` lo rellena el gemelo. La placa rellena `uid` y deja `cell` vacío: el PC traduce el UID con `server/lost_diamond/nfc_map.example.json`.

`buzzer.json` usa uno de estos patrones: `dice`, `diamond`, `tick`, `horseshoe`, `silence`.
