/*
  Estación central. ESP32 + FreeRTOS.

  Publica el botón. Muestra lo que el PC manda a la pantalla
  y hace sonar el patrón del zumbador.

  Placa: ESP32 Dev Module.
  Librería: PubSubClient.
  Red: config.h

  Solo taskMqtt usa el cliente MQTT.
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include "config.h"

// Rellenar cuando el esquema esté en docs/hardware. -1 = sin asignar.
const int PIN_BUTTON = -1;
const int PIN_BUZZER = -1;
const int PIN_LED = -1;

WiFiClient wifi;
PubSubClient mqtt(wifi);

volatile bool buttonEdge = false;
String buzzerPattern = "silence";
String line1 = "The Lost Diamond";
String line2 = "";

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
  }
}

void onMqtt(char *topic, byte *payload, unsigned int length) {
  String body;
  for (unsigned int i = 0; i < length; i++) {
    body += (char)payload[i];
  }
  String name(topic);
  if (name.endsWith("/buzzer")) {
    buzzerPattern = body;
  } else if (name.endsWith("/display")) {
    line1 = body;
    // El dibujo de las dos líneas se hace en paintScreen().
  } else if (name.endsWith("/dice")) {
    line2 = body;
  }
}

void connectMqtt() {
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqtt);
  while (!mqtt.connected()) {
    if (mqtt.connect("station")) {
      mqtt.subscribe("lostdiamond/station/display");
      mqtt.subscribe("lostdiamond/station/buzzer");
      mqtt.subscribe("lostdiamond/game/dice");
      mqtt.subscribe("lostdiamond/game/event");
    } else {
      delay(500);
    }
  }
}

void publishButton() {
  if (!mqtt.connected()) {
    return;
  }
  mqtt.publish("lostdiamond/station/button", "{\"pressed\":true}");
}

void paintScreen() {
  // Pantalla serie 128x64, a través del conversor de nivel.
  // Pintar line1 y line2 cuando conozcamos el modelo.
}

void taskMqtt(void *param) {
  connectWifi();
  connectMqtt();
  for (;;) {
    if (!mqtt.connected()) {
      connectMqtt();
    }
    mqtt.loop();
    if (buttonEdge) {
      buttonEdge = false;
      publishButton();
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

void taskButton(void *param) {
  for (;;) {
    if (PIN_BUTTON >= 0 && digitalRead(PIN_BUTTON) == LOW) {
      buttonEdge = true;
    }
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

void taskBuzzer(void *param) {
  for (;;) {
    // Traducir buzzerPattern (dice, diamond, tick, horseshoe, silence)
    // a tone() sin parar las otras tareas. El pin sigue en -1.
    (void)PIN_BUZZER;
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

void setup() {
  if (PIN_LED >= 0) {
    pinMode(PIN_LED, OUTPUT);
  }
  if (PIN_BUTTON >= 0) {
    pinMode(PIN_BUTTON, INPUT_PULLUP);
  }
  xTaskCreate(taskMqtt, "mqtt", 8192, nullptr, 1, nullptr);
  xTaskCreate(taskButton, "button", 2048, nullptr, 1, nullptr);
  xTaskCreate(taskBuzzer, "buzzer", 2048, nullptr, 1, nullptr);
}

void loop() {
  paintScreen();
  vTaskDelay(pdMS_TO_TICKS(50));
}
