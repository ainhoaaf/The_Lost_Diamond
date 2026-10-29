/*
  Meeple. ESP-01.

  Publica la MAC al arrancar y, cuando el PC le da el turno,
  lee el tag NFC y publica la posición.
  El LED sigue el mensaje de status.

  Placa: Generic ESP8266 Module.
  Librería: PubSubClient.
  Red: config.h
*/

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include "config.h"

// Rellenar con el GPIO cuando el esquema esté en docs/hardware.
const int PIN_LED = -1;

WiFiClient wifi;
PubSubClient mqtt(wifi);
String playerId;

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
  }
}

void onMqtt(char *topic, byte *payload, unsigned int length) {
  String name(topic);
  String body;
  for (unsigned int i = 0; i < length; i++) {
    body += (char)payload[i];
  }
  if (name.indexOf("/assign/") >= 0) {
    rememberPlayerId(body);
    return;
  }
  // status llega como {"active": true} o {"active": false}.
  bool myTurn = body.indexOf("\"active\": true") >= 0 || body.indexOf("\"active\":true") >= 0;
  if (PIN_LED >= 0) {
    digitalWrite(PIN_LED, myTurn ? HIGH : LOW);
  }
}

void connectMqtt() {
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqtt);
  while (!mqtt.connected()) {
    if (mqtt.connect(DEVICE_MAC)) {
      String joinTopic = "lostdiamond/lobby/join";
      String joinBody = String("{\"mac\":\"") + DEVICE_MAC + "\"}";
      mqtt.publish(joinTopic.c_str(), joinBody.c_str());

      String assignTopic = String("lostdiamond/lobby/assign/") + DEVICE_MAC;
      mqtt.subscribe(assignTopic.c_str());
    } else {
      delay(500);
    }
  }
}

void rememberPlayerId(const String &body) {
  // El PC responde con {"player_id":"1", ...}. A partir de ahí
  // este meeple escucha su status y publica su posición.
  int mark = body.indexOf("\"player_id\":\"");
  if (mark < 0) {
    return;
  }
  int from = mark + 13;
  int to = body.indexOf('"', from);
  playerId = body.substring(from, to);
  String statusTopic = "lostdiamond/players/" + playerId + "/status";
  mqtt.subscribe(statusTopic.c_str());
}

// Aquí irá el PN532. Devuelve el UID en hexadecimal, o cadena vacía
// si no hay tag delante. Solo se llama durante el turno.
String pollTag() {
  return "";
}

void publishPosition(const String &uid) {
  if (playerId.length() == 0 || uid.length() == 0) {
    return;
  }
  String topic = "lostdiamond/players/" + playerId + "/position";
  String body = String("{\"player_id\":\"") + playerId + "\",\"uid\":\"" + uid + "\",\"cell\":\"\"}";
  mqtt.publish(topic.c_str(), body.c_str());
}

void setup() {
  if (PIN_LED >= 0) {
    pinMode(PIN_LED, OUTPUT);
  }
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

  String uid = pollTag();
  if (uid.length() > 0) {
    publishPosition(uid);
  }
}
