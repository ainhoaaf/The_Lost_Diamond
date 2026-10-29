# Meeple

Proyecto PlatformIO del ESP-01. El código está en `src/main.cpp`.

La placa publica `WiFi.macAddress()` en `lostdiamond/lobby/join`. El PC responde en `lobby/assign/{mac}` con `Player_1` … `Player_4`. El LED sigue el campo `turn` de `lostdiamond/Players/Player_N`.

1. Cambia en `include/config.h` el WiFi, la IP de esta placa y la IP del PC.
2. Cada meeple lleva un último número de IP distinto. La estación usa `.20` y los meeples pueden usar `.21` a `.24`.
3. Compila el entorno `esp01_1m`. Si el chip es de 512 KB, usa `esp01`.

El lector PN532 se añade en `pollTag()` cuando el primer tag lea bien. Hasta entonces el programa solo se conecta y anuncia su MAC.
