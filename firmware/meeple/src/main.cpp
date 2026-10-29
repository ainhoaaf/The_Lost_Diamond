/*
  Meeple. ESP-01.

  Publica su MAC de WiFi al arrancar. El PC le asigna Player_N.
  Cuando turn vale 1, lee el tag y publica el movimiento.
  El LED sigue el campo turn de Players/Player_N.

  La identidad es WiFi.macAddress(), no un nombre escrito a mano.
*/

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "config.h"

WiFiClient wifi;
PubSubClient mqtt(wifi);

String deviceMac;
String playerId;
bool myTurn = false;
uint32_t eventCounter = 1;

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.config(WIFI_LOCAL_IP, WIFI_GATEWAY, WIFI_SUBNET);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  deviceMac = WiFi.macAddress();
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
  }
}

void publishJoin() {
  StaticJsonDocument<192> doc;
  doc["event_id"] = String(eventCounter++);
  doc["player_id"] = "";
  doc["timestamp"] = millis();
  doc["action"] = "join";
  doc["mac"] = deviceMac;
  char body[192];
  serializeJson(doc, body, sizeof(body));
  mqtt.publish("lostdiamond/lobby/join", body);
}

void connectMqtt() {
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  String willTopic = "lostdiamond/lobby/status/" + deviceMac;
  while (!mqtt.connected()) {
    // Last Will: si este meeple desaparece, el broker avisa al PC.
    bool ok = mqtt.connect(
        deviceMac.c_str(),
        willTopic.c_str(),
        1,
        true,
        "{\"online\":false}");
    if (ok) {
      String online = String("{\"mac\":\"") + deviceMac + "\",\"online\":true}";
      mqtt.publish(willTopic.c_str(), online.c_str(), true);
      publishJoin();
      String assignTopic = "lostdiamond/lobby/assign/" + deviceMac;
      mqtt.subscribe(assignTopic.c_str(), 1);
      if (playerId.length() > 0) {
        mqtt.subscribe(("lostdiamond/Players/" + playerId).c_str(), 1);
        mqtt.subscribe(("lostdiamond/Players/" + playerId + "/result").c_str(), 1);
      }
    } else {
      delay(500);
    }
  }
}

void onAssign(JsonDocument &doc) {
  const char *id = doc["player_id"] | "";
  if (id[0] == '\0') {
    return;
  }
  playerId = id;
  mqtt.subscribe(("lostdiamond/Players/" + playerId).c_str(), 1);
  mqtt.subscribe(("lostdiamond/Players/" + playerId + "/result").c_str(), 1);
}

void onPlayerState(JsonDocument &doc) {
  myTurn = doc["turn"] | 0;
  if (PIN_LED >= 0) {
    digitalWrite(PIN_LED, myTurn ? HIGH : LOW);
  }
}

// El callback solo interpreta lo justo. Publicar la posición se hace en loop.
void onMqtt(char *topic, byte *payload, unsigned int length) {
  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, payload, length)) {
    return;
  }
  String name(topic);
  if (name.indexOf("/assign/") >= 0) {
    onAssign(doc);
  } else if (name.indexOf("/result") >= 0) {
    // Aquí se comparará event_id para no repetir un movimiento.
  } else {
    onPlayerState(doc);
  }
}

String pollTag() {
  return "";
}

void publishMove(const String &uid) {
  if (playerId.length() == 0 || uid.length() == 0) {
    return;
  }
  StaticJsonDocument<256> doc;
  doc["event_id"] = String(eventCounter++);
  doc["player_id"] = playerId;
  doc["timestamp"] = millis();
  doc["action"] = "move";
  doc["uid"] = uid;
  doc["cell"] = "";
  char body[256];
  size_t n = serializeJson(doc, body, sizeof(body));
  String topic = "lostdiamond/Players/" + playerId + "/move";
  mqtt.publish(topic.c_str(), (const uint8_t *)body, n);
}

void setup() {
  Serial.begin(115200);
  if (PIN_LED >= 0) {
    pinMode(PIN_LED, OUTPUT);
  }
  mqtt.setCallback(onMqtt);
  connectWifi();
  connectMqtt();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWifi();
  }
  if (!mqtt.connected()) {
    connectMqtt();
  }
  mqtt.loop();

  if (myTurn) {
    String uid = pollTag();
    if (uid.length() > 0) {
      publishMove(uid);
    }
  }
}
