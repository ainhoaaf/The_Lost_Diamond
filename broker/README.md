# Broker

Mosquitto en el PC. Los gemelos y las placas se conectan aquí.

```bash
mosquitto -c mosquitto.conf
```

Para ver todos los mensajes del juego:

```bash
mosquitto_sub -v -t 'lostdiamond/#'
```

Esa ventana es el depurador del protocolo. Si un meeple dice que ha publicado y aquí no aparece nada, el fallo está en la red o en el sketch, no en las reglas.
