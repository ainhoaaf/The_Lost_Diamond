#pragma once

// Datos de la red local. Cámbialos en el laboratorio.
// El broker es el PC que ejecuta Mosquitto.

static const char *WIFI_SSID = "lost-diamond";
static const char *WIFI_PASSWORD = "cambiar";
static const char *MQTT_HOST = "192.168.1.10";
static const int MQTT_PORT = 1883;

// Una MAC distinta en cada meeple. El PC asigna el jugador con este valor.
static const char *DEVICE_MAC = "AA:BB:CC:DD:EE:01";
