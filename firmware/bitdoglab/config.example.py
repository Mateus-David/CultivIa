# copia pra config.py e preenche (o config.py não vai pro git)
WIFI_SSID = "sua_rede"  # só 2.4GHz
WIFI_PASSWORD = "sua_senha"
MQTT_BROKER = "192.168.0.10"  # IP do PC que roda o docker (ver no ipconfig)
MQTT_PORT = 1883
MQTT_USER = "esp32"
MQTT_PASSWORD = "mesma_do_MQTT_ESP32_PASSWORD_no_.env"
CLIENT_ID = "BitDogLab_CultivIA"  # tem que ser diferente do ESP32
