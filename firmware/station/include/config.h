#pragma once

#include <Arduino.h>

// Misma red que los meeples. Otra IP.
static const char *WIFI_SSID = "lost-diamond";
static const char *WIFI_PASSWORD = "cambiar";

static const IPAddress WIFI_LOCAL_IP(192, 168, 1, 20);
static const IPAddress WIFI_GATEWAY(192, 168, 1, 1);
static const IPAddress WIFI_SUBNET(255, 255, 255, 0);

static const char *MQTT_HOST = "192.168.1.10";
static const uint16_t MQTT_PORT = 1883;

// -1 hasta cerrar el esquema. La pantalla es serie, con conversor de nivel.
static const int PIN_BUTTON = -1;
static const int PIN_BUZZER = -1;
static const int PIN_LED = -1;
