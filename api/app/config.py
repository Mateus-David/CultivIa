"""Configurações da API — tudo que vem de fora do código fica aqui.

As variáveis de ambiente fazem o caminho:
    .env  ->  docker-compose.yml (serviço `api`)  ->  container  ->  este arquivo

os.environ["X"] (com colchetes) derruba a API na hora se X não existir.
É proposital: uma configuração esquecida aparece logo ao subir, e não
no meio do uso.
"""
import os

# Senha de acesso do site. O navegador envia no cabeçalho
# "Authorization: Bearer <token>" (ver web/src/lib/api.ts).
API_TOKEN = os.environ["API_TOKEN"]

# Broker MQTT. No compose, o host é "mosquitto" (nome do serviço).
MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = int(os.environ["MQTT_PORT"])
MQTT_USER = os.environ["MQTT_USER"]          # usuário "api" em mosquitto/config/acl
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]

# Tópicos MQTT. Precisam ser iguais aos do firmware (firmware/esp32/main.py)
# e às permissões em mosquitto/config/acl.
TOPICO_SENSORES = "cultivia/sensores"   # leituras que a placa publica
TOPICO_ESTADO = "cultivia/estado"       # "como estou": atuadores, alvos, online
TOPICO_COMANDOS = "cultivia/comandos"   # base dos comandos; a API acrescenta /<nome>

# A placa é considerada offline se a última leitura for mais velha que isto.
PLACA_TIMEOUT_S = 15
