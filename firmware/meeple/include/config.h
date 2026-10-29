#pragma once

#include <Arduino.h>

// Red local. Cambia el último número de la IP en cada meeple.
static const char *WIFI_SSID = "lost-diamond";
static const char *WIFI_PASSWORD = "cambiar";

static const IPAddress WIFI_LOCAL_IP(192, 168, 1, 21);
static const IPAddress WIFI_GATEWAY(192, 168, 1, 1);
static const IPAddress WIFI_SUBNET(255, 255, 255, 0);

static const char *MQTT_HOST = "192.168.1.10";
static const uint16_t MQTT_PORT = 1883;

// GPIO del LED. -1 hasta que el esquema esté en docs/hardware.
static const int PIN_LED = -1;
