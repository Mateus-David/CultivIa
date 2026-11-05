#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_AHTX0.h>
#include "driver/ledc.h"
#include "config.h"            

// ---------- Sensores ----------
#define SDA_PIN  21
#define SCL_PIN  22
#define AHT_ADDR 0x38
#define SOIL_PIN 34

Adafruit_AHTX0 aht;

// Calibração do sensor capacitivo (valores brutos de 0 a 4095)
// Sensor capacitivo: SECO = valor ALTO, MOLHADO = valor BAIXO
// Ajuste pelos comandos D e W (veja abaixo) e depois grave aqui
int SOIL_DRY = 3000;             // sensor no ar / solo seco
int SOIL_WET = 1300;             // sensor na água / solo encharcado

// ---------- Atuadores ----------
const int FANS[] = {32, 33, 13};
const int N = sizeof(FANS) / sizeof(FANS[0]);
const int N_COOL = 2;            // fans 1 e 2 = ventilação
const int PUMP   = 2;            // bomba d'água = umidade
const uint32_t FREQ = 1000;

// ---------- Setpoints (alteráveis pelo site e pela Serial) ----------
float tempSet = 25.0;            // °C desejada
float soilSet = 60.0;            // % de umidade do solo desejada

// ---------- Parâmetros de controle ----------
const float    TEMP_ON_MARGIN = 0.5;    // liga fans acima de tempSet + 0.5
const float    KP_TEMP        = 20.0;   // % de velocidade por °C acima do alvo
const int      FAN_MIN_PCT    = 30;     // velocidade mínima para girar
const float    SOIL_HYST      = 5.0;    // liga bomba abaixo de soilSet - 5
const float    KP_SOIL        = 5.0;    // % de velocidade da bomba por ponto abaixo do alvo
const int      PUMP_MIN_PCT   = 50;     // abaixo disso a bomba não puxa água
const uint32_t PUMP_ON_MS     = 1000;   // duração de cada pulso
const uint32_t PUMP_SOAK_MS   = 2000;  // espera para a água infiltrar
const uint32_t READ_MS        = 1000;

// MQTT
// tem que bater com a api/app/config.py e o mosquitto/config/acl
const char* T_SENSORES = "cultivia/sensores";
const char* T_ESTADO   = "cultivia/estado";
const char* T_SETPOINT = "cultivia/comandos/setpoint";
const uint32_t PUBLISH_MS   = 2000;
const uint32_t RECONNECT_MS = 5000;

WiFiClient net;
PubSubClient mqtt(net);

// ---------- Estado ----------
float temp = NAN, airHum = NAN;
int   soilRaw = 0;
float soilPct = NAN;
bool  fansOn = false;
int   fanPct = 0, pumpPct = 0;   // o que está saindo no PWM agora (vai no MQTT)
enum PumpState { P_IDLE, P_RUNNING, P_SOAKING };
PumpState pumpState = P_IDLE;
uint32_t pumpT0 = 0, lastRead = 0, lastPublish = 0, lastMqttTry = 0;

bool   alvoMudou = true;         // quando true publica o cultivia/estado de novo
bool   acabouDeConectar = false;
String alvoDoSite;               // último setpoint aplicado que veio do site

void fanSet(int i, int pct) {
  pct = constrain(pct, 0, 100);
  ledc_set_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i, pct * 255 / 100);
  ledc_update_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i);
}

void coolSet(int pct) {
  fanPct = pct;
  for (int i = 0; i < N_COOL; i++) fanSet(i, pct);
}

void pumpSet(int pct) {
  if (pct == pumpPct) return;
  pumpPct = pct;
  fanSet(PUMP, pct);
}

// ---------- Leitura do solo (média de 16 amostras) ----------
void readSoil() {
  long sum = 0;
  for (int i = 0; i < 16; i++) { sum += analogRead(SOIL_PIN); delay(2); }
  soilRaw = sum / 16;

  // valor perto de 0 ou 4095 = sensor desconectado/em curto
  if (soilRaw < 100 || soilRaw > 4000) { soilPct = NAN; return; }

  soilPct = (float)(SOIL_DRY - soilRaw) * 100.0 / (SOIL_DRY - SOIL_WET);
  soilPct = constrain(soilPct, 0.0, 100.0);
}

// ---------- Temperatura ----------
void controlTemp() {
  float err = temp - tempSet;
  if (!fansOn && err > TEMP_ON_MARGIN) fansOn = true;
  if (fansOn && err <= 0)              fansOn = false;

  int pct = 0;
  if (fansOn) pct = constrain(FAN_MIN_PCT + (int)(KP_TEMP * err), FAN_MIN_PCT, 100);
  coolSet(pct);
}

// ---------- Bomba (máquina de estados, sem delay) ----------
// quanto mais seco em relação ao alvo, mais rápido ela gira
int pumpSpeed() {
  float err = soilSet - soilPct;
  return constrain(PUMP_MIN_PCT + (int)(KP_SOIL * err), PUMP_MIN_PCT, 100);
}

void controlPump(uint32_t now) {
  bool soilOk = !isnan(soilPct);

  switch (pumpState) {
    case P_IDLE:
      if (soilOk && soilPct < soilSet - SOIL_HYST) {
        pumpSet(pumpSpeed());
        pumpT0 = now;
        pumpState = P_RUNNING;
        Serial.printf(">> Bomba LIGADA (%d%%)\n", pumpPct);
      }
      break;

    case P_RUNNING:
      // desliga se: atingiu o alvo, sensor falhou ou acabou o tempo do pulso
      if (!soilOk || soilPct >= soilSet || now - pumpT0 >= PUMP_ON_MS) {
        pumpSet(0);
        pumpT0 = now;
        pumpState = P_SOAKING;
        Serial.println(">> Bomba DESLIGADA (aguardando infiltrar)");
      } else {
        pumpSet(pumpSpeed());   // vai diminuindo conforme o solo molha
      }
      break;

    case P_SOAKING:
      if (now - pumpT0 >= PUMP_SOAK_MS) pumpState = P_IDLE;
      break;
  }
}

// ---------- MQTT ----------
void publicaEstado() {
  JsonDocument doc;
  doc["online"] = 1;
  doc["setpoint"]["temperatura"] = tempSet;
  doc["setpoint"]["umidade"] = soilSet;

  char buf[128];
  size_t n = serializeJson(doc, buf);
  mqtt.publish(T_ESTADO, (const uint8_t*)buf, n, true);   // retido, o site lê quando abrir
  alvoMudou = false;
}

float umaCasa(float v) { return roundf(v * 10) / 10; }

void publicaLeitura() {
  // as chaves tem que bater com o telegraf.conf
  JsonDocument doc;
  doc["modo"] = "estufa";
  // sensor em falha fica fora da mensagem, o telegraf não aceita null
  if (!isnan(temp))    doc["temperatura"] = umaCasa(temp);
  if (!isnan(soilPct)) doc["umidade"]     = umaCasa(soilPct);   // umidade do solo
  if (!isnan(airHum))  doc["umidade_ar"]  = umaCasa(airHum);
  doc["solo_raw"] = soilRaw;
  doc["temperatura_ideal"] = tempSet;
  doc["umidade_ideal"] = soilSet;
  doc["fans"] = fanPct;
  doc["bomba"] = pumpPct;

  char buf[256];
  size_t n = serializeJson(doc, buf);
  mqtt.publish(T_SENSORES, (const uint8_t*)buf, n, false);
}

void aoReceber(char* topic, byte* payload, unsigned int len) {
  // alvo novo vindo do site, ex: {"temperatura": 28, "umidade": 60}
  String msg;
  msg.reserve(len);
  for (unsigned int i = 0; i < len; i++) msg += (char)payload[i];

  // quando reconecta o broker manda de novo o último alvo (retido). se for o mesmo
  // que já foi aplicado ignora, senão uma queda de rede desfaz o que mudei pela Serial
  bool repetido = acabouDeConectar && msg == alvoDoSite;
  acabouDeConectar = false;
  if (repetido) return;
  alvoDoSite = msg;

  JsonDocument doc;
  if (deserializeJson(doc, msg)) { Serial.println("Mensagem invalida: " + msg); return; }
  if (doc["temperatura"].is<float>()) tempSet = constrain(doc["temperatura"].as<float>(), 0.0f, 50.0f);
  if (doc["umidade"].is<float>())     soilSet = constrain(doc["umidade"].as<float>(), 0.0f, 100.0f);
  alvoMudou = true;
  Serial.printf("Alvos do site: %.1f C / %.0f %%\n", tempSet, soilSet);
}

bool conectaMqtt() {
  Serial.printf("Wi-Fi ok (IP da ESP %s). Conectando ao MQTT em %s:%d...\n",
                WiFi.localIP().toString().c_str(), MQTT_BROKER, MQTT_PORT);
  // se a placa cair o broker publica isso no lugar dela e o site mostra offline
  if (!mqtt.connect(CLIENT_ID, MQTT_USER, MQTT_PASSWORD, T_ESTADO, 0, true, "{\"online\":0}")) {
    // -2 = PC não respondeu (IP/firewall), 4 ou 5 = usuário/senha
    Serial.printf("Falha no MQTT (estado %d), confira o config.h\n", mqtt.state());
    return false;
  }
  acabouDeConectar = true;
  mqtt.subscribe(T_SETPOINT);
  alvoMudou = true;
  Serial.println("MQTT conectado");
  return true;
}

// roda todo ciclo mas nunca fica esperando a rede: o controle continua sem o PC
void cuidaDaRede(uint32_t now) {
  if (!mqtt.connected()) {
    if (now - lastMqttTry < RECONNECT_MS) return;
    lastMqttTry = now;
    // sem Wi-Fi não tem broker (a ESP reconecta sozinha). com a bomba ligada também
    // não tento, pq o connect pode travar uns 3s e o pulso passaria do tempo
    if (WiFi.status() != WL_CONNECTED || pumpState == P_RUNNING) return;
    if (!conectaMqtt()) return;
  }

  mqtt.loop();   // se chegou algo chama o aoReceber
  if (alvoMudou) publicaEstado();
  if (now - lastPublish >= PUBLISH_MS) {
    lastPublish = now;
    publicaLeitura();
  }
}

// ---------- Comandos pela Serial ----------
// T26.5 = alvo de temperatura | S55 = alvo de umidade do solo
// D = grava leitura atual como SECO | W = grava leitura atual como MOLHADO
void handleSerial() {
  if (!Serial.available()) return;
  String s = Serial.readStringUntil('\n');
  s.trim();
  if (s.length() < 1) return;

  char c = toupper(s[0]);
  bool temValor = s.length() > 1;
  float v = temValor ? s.substring(1).toFloat() : 0;

  if (c == 'T' && temValor) {
    tempSet = constrain(v, 0.0f, 50.0f); alvoMudou = true;
    Serial.printf("Novo alvo temp: %.1f C\n", tempSet);
  }
  else if (c == 'S' && temValor) {
    soilSet = constrain(v, 0.0f, 100.0f); alvoMudou = true;
    Serial.printf("Novo alvo solo: %.1f %%\n", soilSet);
  }
  else if (c == 'D') { readSoil(); SOIL_DRY = soilRaw; Serial.printf("SOIL_DRY = %d\n", SOIL_DRY); }
  else if (c == 'W') { readSoil(); SOIL_WET = soilRaw; Serial.printf("SOIL_WET = %d\n", SOIL_WET); }
}

void setup() {
  Serial.begin(115200);
  delay(500);

  Wire.begin(SDA_PIN, SCL_PIN);
  if (!aht.begin(&Wire, 0, AHT_ADDR)) {
    Serial.println("ERRO: AHT10 nao encontrado (cheque fios e endereco 0x38)");
  }

  analogReadResolution(12);
  analogSetPinAttenuation(SOIL_PIN, ADC_11db);   // faixa até ~3,3 V

  ledc_timer_config_t t = {};
  t.speed_mode      = LEDC_LOW_SPEED_MODE;
  t.duty_resolution = LEDC_TIMER_8_BIT;
  t.timer_num       = LEDC_TIMER_0;
  t.freq_hz         = FREQ;
  t.clk_cfg         = LEDC_AUTO_CLK;
  ledc_timer_config(&t);

  for (int i = 0; i < N; i++) {
    ledc_channel_config_t c = {};
    c.gpio_num   = FANS[i];
    c.speed_mode = LEDC_LOW_SPEED_MODE;
    c.channel    = (ledc_channel_t)i;
    c.intr_type  = LEDC_INTR_DISABLE;
    c.timer_sel  = LEDC_TIMER_0;
    c.duty       = 0;
    ledc_channel_config(&c);
  }

  // não espero conectar aqui pro controle já começar, quem confere é o cuidaDaRede()
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.printf("Conectando no Wi-Fi \"%s\"...\n", WIFI_SSID);

  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(aoReceber);
  mqtt.setBufferSize(512);       // o padrão de 256 bytes é pouco pra leitura
  mqtt.setKeepAlive(30);
  mqtt.setSocketTimeout(2);

  Serial.println("\n=== Controle de temperatura e umidade do solo ===");
  Serial.println("T<valor> alvo temp | S<valor> alvo solo | D = calibra seco | W = calibra molhado");
}

void loop() {
  handleSerial();
  uint32_t now = millis();

  if (now - lastRead >= READ_MS) {
    lastRead = now;

    sensors_event_t hEvt, tEvt;
    bool ahtOk = aht.getEvent(&hEvt, &tEvt);
    temp   = ahtOk ? tEvt.temperature : NAN;
    airHum = ahtOk ? hEvt.relative_humidity : NAN;

    readSoil();

    if (isnan(temp)) {
      Serial.println("ERRO: leitura do AHT10 falhou -> fans 100%");
      coolSet(100);
    } else {
      controlTemp();
    }

    Serial.printf("T=%.1fC (alvo %.1f) | ArUR=%.0f%% | Solo raw=%d -> %.0f%% (alvo %.0f) | fans=%d%% | bomba=%d%% | mqtt=%s\n",
                  temp, tempSet, airHum, soilRaw, soilPct, soilSet,
                  fanPct, pumpPct, mqtt.connected() ? "ok" : (WiFi.status() == WL_CONNECTED ? "off" : "sem wifi"));
  }

  controlPump(now);
  cuidaDaRede(now);
}