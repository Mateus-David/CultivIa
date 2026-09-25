import os

# uso os.environ[] direto pra API nem subir se faltar alguma variável no .env
MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = int(os.environ["MQTT_PORT"])
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]

# tem que bater com o firmware e com o mosquitto/config/acl
TOPICO_SENSORES = "cultivia/sensores"
TOPICO_ESTADO = "cultivia/estado"
TOPICO_COMANDOS = "cultivia/comandos"

# sem leitura nova por esse tempo considero a placa offline
PLACA_TIMEOUT_S = 15
