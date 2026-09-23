# firmware/bitdoglab/config.example.py — MODELO das configurações da placa.
#
# COMO USAR: copie para `config.py` (ignorado pelo git, cada pessoa tem o seu),
# preencha e envie à placa junto com main.py (ver firmware/README.md).
WIFI_SSID = "sua_rede"          # a placa só usa redes 2,4 GHz
WIFI_PASSWORD = "sua_senha"
MQTT_BROKER = "192.168.0.10"    # IP do PC que roda o docker compose (confira com ipconfig)
MQTT_PORT = 1883
MQTT_USER = "esp32"             # login das placas em mosquitto/config/acl
MQTT_PASSWORD = "mesma_do_MQTT_ESP32_PASSWORD_no_.env"
MQTT_TOPIC = "cultivia/sensores"
CLIENT_ID = "BitDogLab_CultivIA"   # único por placa (diferente do ESP32)
