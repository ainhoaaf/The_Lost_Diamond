# Meeple

Sketch: `meeple.ino`

1. Herramientas → Placa → Generic ESP8266 Module.
2. Librería: PubSubClient.
3. Edita `config.h`: WiFi, IP del PC y una MAC distinta en cada una de las cuatro placas.
4. El lector PN532 se añade en `pollTag()` cuando el primer tag lea bien. Hasta entonces el sketch solo se conecta y anuncia su MAC.

El LED usa el mensaje `lostdiamond/players/{id}/status`. El pin se rellena al cerrar el esquema.
