#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <SPIFFS.h>
#include <ArduinoJson.h>

// --- Config ---
#define DHTPIN 15
#define DHTTYPE DHT22
#define BTN_PIN 4

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

const char* MQTT_HOST = "broker.hivemq.com";
const uint16_t MQTT_PORT = 1883;
const char* MQTT_TOPIC = "cardioia/grupo1/vitals";

// Resiliência e fila
const size_t MAX_QUEUED_LINES = 300; // limite de amostras offline
const uint32_t PUBLISH_INTERVAL_MS = 3000; // 3s

// --- Globals ---
DHT dht(DHTPIN, DHTTYPE);
WiFiClient espClient;
PubSubClient mqtt(espClient);

volatile uint16_t bpm_clicks = 0;
uint32_t last_publish = 0;
uint32_t last_bpm_calc = 0;
float last_bpm = 0;

// --- Utils ---
void ensureSPIFFS() {
  if (!SPIFFS.begin(true)) {
    Serial.println("[SPIFFS] Falha ao montar SPIFFS");
  }
}

size_t countQueued() {
  File f = SPIFFS.open("/queue.txt", FILE_READ);
  if (!f) return 0;
  size_t lines = 0;
  while (f.available()) {
    if (f.read() == '\n') lines++;
  }
  f.close();
  return lines;
}

void appendQueue(const String& line) {
  // Limita tamanho da fila removendo do início se necessário
  while (countQueued() >= MAX_QUEUED_LINES) {
    // remove primeira linha
    File f = SPIFFS.open("/queue.txt", FILE_READ);
    if (!f) break;
    String rest;
    bool skipped = false;
    while (f.available()) {
      String l = f.readStringUntil('\n');
      if (!skipped) { skipped = true; continue; }
      rest += l + "\n";
    }
    f.close();
    File w = SPIFFS.open("/queue.txt", FILE_WRITE);
    if (w) { w.print(rest); w.close(); }
    else break;
  }

  File f = SPIFFS.open("/queue.txt", FILE_APPEND);
  if (f) { f.println(line); f.close(); }
}

bool wifiConnected() {
  return WiFi.status() == WL_CONNECTED;
}

void connectWiFi() {
  if (wifiConnected()) return;
  Serial.printf("[WiFi] Conectando em %s...\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
}

void ensureMQTT() {
  if (mqtt.connected()) return;
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  String cid = String("cardioia-") + String((uint32_t)ESP.getEfuseMac(), HEX);
  if (mqtt.connect(cid.c_str())) {
    Serial.println("[MQTT] Conectado");
  }
}

void IRAM_ATTR onButton() {
  // Contagem de batimentos via clique
  bpm_clicks++;
}

float calcBPM() {
  uint32_t now = millis();
  if (now - last_bpm_calc >= 10000) { // janela de 10s
    last_bpm = (bpm_clicks * 6.0f);   // extrapola para 60s
    bpm_clicks = 0;
    last_bpm_calc = now;
  }
  return last_bpm;
}

String buildPayload() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  float bpm = calcBPM();

  // fallback se leitura falhar
  if (isnan(t) || isnan(h)) {
    t = 36.5 + random(-10, 10) / 10.0; // simulação leve
    h = 55 + random(-50, 50) / 10.0;
  }

  DynamicJsonDocument doc(256);
  doc["ts"] = (uint32_t) (millis() / 1000);
  doc["temp"] = t;
  doc["hum"] = h;
  doc["bpm"] = bpm;
  String out;
  serializeJson(doc, out);
  return out;
}

void publishOrQueue(const String& line) {
  if (wifiConnected() && mqtt.connected()) {
    bool ok = mqtt.publish(MQTT_TOPIC, line.c_str());
    if (ok) {
      Serial.printf("[MQTT] Pub: %s\n", line.c_str());
      return;
    }
  }
  appendQueue(line);
  Serial.println("[QUEUE] offline → armazenado no SPIFFS");
}

void flushQueue() {
  if (!wifiConnected() || !mqtt.connected()) return;
  File f = SPIFFS.open("/queue.txt", FILE_READ);
  if (!f) return;
  String remaining;
  while (f.available()) {
    String l = f.readStringUntil('\n');
    if (l.length() == 0) continue;
    if (mqtt.publish(MQTT_TOPIC, l.c_str())) {
      Serial.printf("[MQTT] Flush: %s\n", l.c_str());
    } else {
      remaining += l + "\n"; // não conseguiu publicar, mantém
    }
    delay(50);
  }
  f.close();
  File w = SPIFFS.open("/queue.txt", FILE_WRITE);
  if (w) { w.print(remaining); w.close(); }
}

void setup() {
  Serial.begin(115200);
  pinMode(BTN_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BTN_PIN), onButton, FALLING);

  ensureSPIFFS();
  dht.begin();
  connectWiFi();
}

void loop() {
  if (!wifiConnected()) {
    connectWiFi();
  }
  if (wifiConnected() && !mqtt.connected()) {
    ensureMQTT();
  }
  mqtt.loop();

  // Publica periodicamente
  uint32_t now = millis();
  if (now - last_publish >= PUBLISH_INTERVAL_MS) {
    last_publish = now;
    String payload = buildPayload();
    publishOrQueue(payload);
  }

  // Sincroniza fila
  flushQueue();

  delay(10);
}

