import json
import time

import paho.mqtt.client as mqtt
from fastapi import HTTPException

from . import config


class Memoria:
    # guarda só a última mensagem que chegou da placa. se o container reiniciar
    # perde tudo, mas o cultivia/estado é retido então volta na hora
    sensores: dict | None = None
    sensores_recebidos_em: float | None = None
    dispositivo: dict | None = None

    def idade_leitura(self) -> float | None:
        if self.sensores_recebidos_em is None:
            return None
        return round(time.time() - self.sensores_recebidos_em, 1)

    def placa_online(self) -> bool:
        # a placa tem que ter dito online:1 e mandado leitura faz pouco tempo
        idade = self.idade_leitura()
        return (
            (self.dispositivo or {}).get("online") == 1
            and idade is not None
            and idade < config.PLACA_TIMEOUT_S
        )


memoria = Memoria()


def _on_connect(client, userdata, flags, reason_code, properties):
    # assino aqui pq assim ele assina de novo sozinho quando reconecta
    print("MQTT conectado:", reason_code)
    client.subscribe([(config.TOPICO_SENSORES, 0), (config.TOPICO_ESTADO, 0)])


def _on_message(client, userdata, msg):
    try:
        dados = json.loads(msg.payload)
    except ValueError:
        return

    if msg.topic == config.TOPICO_SENSORES:
        memoria.sensores = dados
        memoria.sensores_recebidos_em = time.time()
    elif msg.topic == config.TOPICO_ESTADO:
        memoria.dispositivo = dados


cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="cultivia-api")
cliente.username_pw_set(config.MQTT_USER, config.MQTT_PASSWORD)
cliente.on_connect = _on_connect
cliente.on_message = _on_message
cliente.reconnect_delay_set(min_delay=1, max_delay=15)


def iniciar():
    # connect_async pra API subir mesmo se o broker ainda não estiver no ar
    cliente.connect_async(config.MQTT_HOST, config.MQTT_PORT)
    cliente.loop_start()


def parar():
    cliente.loop_stop()
    cliente.disconnect()


def conectado() -> bool:
    return cliente.is_connected()


def publicar_comando(nome: str, payload: dict, retain: bool):
    # com retain o broker guarda a mensagem e a placa recebe quando conectar
    info = cliente.publish(
        f"{config.TOPICO_COMANDOS}/{nome}", json.dumps(payload), qos=1, retain=retain
    )
    if info.rc != mqtt.MQTT_ERR_SUCCESS:
        raise HTTPException(503, "Broker MQTT indisponível")
