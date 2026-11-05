// copia pra config.h e preenche (o config.h não vai pro git)
#pragma once

// rede Wi-Fi que a ESP e o PC usam (só 2.4GHz, no hotspot do celular ative a banda 2.4GHz)
#define WIFI_SSID     "sua_rede"
#define WIFI_PASSWORD "sua_senha"

// IP do PC que roda o docker nessa rede (ver no ipconfig, muda se trocar de rede)
#define MQTT_BROKER   "192.168.0.10"
#define MQTT_PORT     1883
#define MQTT_USER     "esp32"
#define MQTT_PASSWORD "mesma_do_MQTT_ESP32_PASSWORD_no_.env"
#define CLIENT_ID     "ESP32_Estufa"   // tem que ser diferente das outras placas
