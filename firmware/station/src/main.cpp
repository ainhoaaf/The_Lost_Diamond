/*
  Estación. ESP32 + FreeRTOS.

  El callback MQTT solo deja el mensaje en una cola.
  taskLogic lo interpreta. Pantalla, LED y zumbador leen ese resultado.
  Serial.begin va antes de crear las tareas. Quien escriba por Serial
  toma serialMutex.

  La pantalla del kit es un UART con conversor de nivel, no I2C.
  Serial (el USB) no es ese UART. El dibujo se conectará cuando
  el esquema fije los pines.
*/

#include <cstring>

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "config.h"

struct MqttMessage {
  char topic[80];
  char payload[192];
};

WiFiClient wifi;
PubSubClient mqtt(wifi);

QueueHandle_t mqttQueue;
QueueHandle_t buttonQueue;
SemaphoreHandle_t stateMutex;
SemaphoreHandle_t serialMutex;

char line1[48] = "The Lost Diamond";
char line2[48] = "";
char buzzerPattern[16] = "silence";
volatile bool ledOn = false;
uint32_t eventCounter = 1;

void logLine(const char *text) {
  if (xSemaphoreTake(serialMutex, pdMS_TO_TICKS(50)) == pdTRUE) {
    Serial.println(text);
    xSemaphoreGive(serialMutex);
  }
}

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.config(WIFI_LOCAL_IP, WIFI_GATEWAY, WIFI_SUBNET);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
  }
}

void onMqtt(char *topic, byte *payload, unsigned int length) {
  MqttMessage message = {};
  strncpy(message.topic, topic, sizeof(message.topic) - 1);
  unsigned int n = length < sizeof(message.payload) - 1 ? length : sizeof(message.payload) - 1;
  memcpy(message.payload, payload, n);
  xQueueSend(mqttQueue, &message, 0);
}

void connectMqtt() {
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqtt);
  const char *willTopic = "lostdiamond/lobby/status/station";
  while (!mqtt.connected()) {
    bool ok = mqtt.connect("station", willTopic, 1, true, "{\"online\":false}");
    if (ok) {
      mqtt.publish(willTopic, "{\"mac\":\"station\",\"online\":true}", true);
      mqtt.subscribe("lostdiamond/Game_status", 1);
      mqtt.subscribe("lostdiamond/Station/display", 1);
      mqtt.subscribe("lostdiamond/Station/buzzer", 1);
    } else {
      delay(500);
    }
  }
}

void publishButton() {
  StaticJsonDocument<160> doc;
  doc["event_id"] = String(eventCounter++);
  doc["player_id"] = "";
  doc["timestamp"] = millis();
  doc["action"] = "button";
  doc["pressed"] = true;
  char body[160];
  size_t n = serializeJson(doc, body, sizeof(body));
  mqtt.publish("lostdiamond/Station/button", (const uint8_t *)body, n);
}

void copyField(char *dest, size_t size, const char *value) {
  if (value == nullptr) {
    return;
  }
  strncpy(dest, value, size - 1);
  dest[size - 1] = '\0';
}

void applyMessage(const MqttMessage &message) {
  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, message.payload)) {
    return;
  }
  String name(message.topic);
  if (xSemaphoreTake(stateMutex, pdMS_TO_TICKS(20)) != pdTRUE) {
    return;
  }
  if (name.endsWith("/display")) {
    copyField(line1, sizeof(line1), doc["line1"] | "");
    copyField(line2, sizeof(line2), doc["line2"] | "");
  } else if (name.endsWith("/buzzer")) {
    copyField(buzzerPattern, sizeof(buzzerPattern), doc["pattern"] | "silence");
  } else if (name.endsWith("Game_status")) {
    int roll = doc["movements"] | 0;
    const char *who = doc["current_player"] | "";
    snprintf(line1, sizeof(line1), "%s", who);
    snprintf(line2, sizeof(line2), "Tirada: %d", roll);
    ledOn = doc["diamond_found"] | false;
  }
  xSemaphoreGive(stateMutex);
}

void taskLogic(void *param) {
  MqttMessage message;
  for (;;) {
    if (xQueueReceive(mqttQueue, &message, portMAX_DELAY) == pdTRUE) {
      applyMessage(message);
    }
  }
}

void taskMqtt(void *param) {
  connectWifi();
  logLine("WiFi listo");
  connectMqtt();
  uint8_t pressed = 0;
  for (;;) {
    if (!mqtt.connected()) {
      connectMqtt();
    }
    mqtt.loop();
    if (xQueueReceive(buttonQueue, &pressed, 0) == pdTRUE) {
      publishButton();
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

void taskButton(void *param) {
  bool wasDown = false;
  for (;;) {
    bool down = PIN_BUTTON >= 0 && digitalRead(PIN_BUTTON) == LOW;
    if (down && !wasDown) {
      uint8_t pressed = 1;
      xQueueSend(buttonQueue, &pressed, 0);
    }
    wasDown = down;
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

void taskBuzzer(void *param) {
  char pattern[16] = "silence";
  for (;;) {
    if (xSemaphoreTake(stateMutex, pdMS_TO_TICKS(20)) == pdTRUE) {
      strncpy(pattern, buzzerPattern, sizeof(pattern) - 1);
      xSemaphoreGive(stateMutex);
    }
    // tone() cuando PIN_BUZZER deje de ser -1. pattern: dice, diamond, tick, horseshoe, silence.
    (void)pattern;
    (void)PIN_BUZZER;
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

void taskLed(void *param) {
  for (;;) {
    if (PIN_LED >= 0) {
      digitalWrite(PIN_LED, ledOn ? HIGH : LOW);
    }
    vTaskDelay(pdMS_TO_TICKS(50));
  }
}

void taskDisplay(void *param) {
  for (;;) {
    if (xSemaphoreTake(stateMutex, pdMS_TO_TICKS(20)) == pdTRUE) {
      // line1 y line2 saldrán por el UART de la pantalla, no por el USB.
      xSemaphoreGive(stateMutex);
    }
    vTaskDelay(pdMS_TO_TICKS(50));
  }
}

void setup() {
  Serial.begin(115200);
  if (PIN_LED >= 0) {
    pinMode(PIN_LED, OUTPUT);
  }
  if (PIN_BUTTON >= 0) {
    pinMode(PIN_BUTTON, INPUT_PULLUP);
  }

  mqttQueue = xQueueCreate(8, sizeof(MqttMessage));
  buttonQueue = xQueueCreate(4, sizeof(uint8_t));
  stateMutex = xSemaphoreCreateMutex();
  serialMutex = xSemaphoreCreateMutex();

  xTaskCreatePinnedToCore(taskMqtt, "mqtt", 8192, nullptr, 2, nullptr, 0);
  xTaskCreate(taskButton, "button", 2048, nullptr, 1, nullptr);
  xTaskCreatePinnedToCore(taskLogic, "logic", 4096, nullptr, 1, nullptr, 1);
  xTaskCreate(taskBuzzer, "buzzer", 2048, nullptr, 1, nullptr);
  xTaskCreate(taskLed, "led", 2048, nullptr, 1, nullptr);
  xTaskCreatePinnedToCore(taskDisplay, "lcd", 3072, nullptr, 1, nullptr, 1);
}

void loop() {
  vTaskDelay(portMAX_DELAY);
}
