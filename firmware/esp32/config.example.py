# firmware/esp32/config.example.py — MODELO das configurações da placa.
#
# COMO USAR: copie para `config.py` (ignorado pelo git, cada pessoa tem o seu),
# preencha e envie ao ESP32 junto com main.py. O main.py faz `import config` e
# usa estes valores. Não coloque senhas reais neste arquivo de exemplo.
WIFI_SSID = "sua_rede"          # nome do WiFi (a placa só usa redes 2,4 GHz)
WIFI_PASSWORD = "sua_senha"
MQTT_BROKER = "192.168.0.10"    # IP do PC/servidor que roda o docker compose
MQTT_PORT = 1883
MQTT_USER = "esp32"             # usuário fixo, definido em mosquitto/config/acl
MQTT_PASSWORD = "mesma_do_MQTT_ESP32_PASSWORD_no_.env"   # a senha vem do .env do servidor
MQTT_TOPIC = "cultivia/sensores"  # igual ao MQTT_TOPIC do .env (obs.: o main.py atual usa tópicos fixos)
CLIENT_ID = "ESP32_CultivIA"    # nome desta conexão no broker (único por dispositivo)
INTERVALO_MS = 2000             # intervalo inicial entre leituras (o site pode mudar depois)
LED_PIN = 2                     # GPIO do LED de status (2 = onboard na maioria dos devkits)
