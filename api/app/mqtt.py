"""MQTT — a conversa da API com a placa (através do Mosquitto).

Dois sentidos:
  OUVIR  placa -> Mosquitto -> on_message() -> guarda em `memoria`
  FALAR  rota HTTP -> publicar_comando() -> Mosquitto -> placa

O cliente roda numa thread própria do paho (loop_start), separada das
requisições HTTP. Quem liga/desliga essa thread é o `lifespan` em main.py.
"""
import json
import time

import paho.mqtt.client as mqtt
from fastapi import HTTPException

from . import config


class Memoria:
    """A ÚLTIMA coisa recebida da placa, guardada na RAM do processo.

    Escreve: on_message (abaixo).  Lê: rota GET /estado (routes.py).
    Se o container reiniciar, isto zera — a placa repopula na próxima
    mensagem (e cultivia/estado é retido, então chega na hora).
    """
    sensores: dict | None = None
    sensores_recebidos_em: float | None = None   # time.time() da última leitura
    dispositivo: dict | None = None

    def idade_leitura(self) -> float | None:
        """Há quantos segundos chegou a última leitura (None = nunca)."""
        if self.sensores_recebidos_em is None:
            return None
        return round(time.time() - self.sensores_recebidos_em, 1)

    def placa_online(self) -> bool:
        """Online = a placa disse online:1 (o Last Will troca para 0 se ela
        cair) E mandou leitura recentemente."""
        idade = self.idade_leitura()
        return (
            (self.dispositivo or {}).get("online") == 1
            and idade is not None
            and idade < config.PLACA_TIMEOUT_S
        )


memoria = Memoria()


# ---------------------------------------------------------------
# Callbacks: o paho chama estas funções sozinho
# ---------------------------------------------------------------
def _on_connect(client, userdata, flags, reason_code, properties):
    """Chamada a cada (re)conexão. Assinar AQUI garante que a assinatura
    é refeita automaticamente depois de uma queda."""
    print("MQTT conectado:", reason_code)
    client.subscribe([(config.TOPICO_SENSORES, 0), (config.TOPICO_ESTADO, 0)])


def _on_message(client, userdata, msg):
    """Chamada a cada mensagem dos tópicos assinados."""
    try:
        dados = json.loads(msg.payload)   # bytes -> dict
    except ValueError:
        return                            # não é JSON: ignora, não derruba a API

    if msg.topic == config.TOPICO_SENSORES:
        memoria.sensores = dados
        memoria.sensores_recebidos_em = time.time()
    elif msg.topic == config.TOPICO_ESTADO:
        memoria.dispositivo = dados


# ---------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------
cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="cultivia-api")
cliente.username_pw_set(config.MQTT_USER, config.MQTT_PASSWORD)
cliente.on_connect = _on_connect
cliente.on_message = _on_message
cliente.reconnect_delay_set(min_delay=1, max_delay=15)   # se cair, tenta de 1 s a 15 s


def iniciar():
    """Conecta em segundo plano. Se o broker estiver fora do ar, a API sobe
    mesmo assim e o paho continua tentando."""
    cliente.connect_async(config.MQTT_HOST, config.MQTT_PORT)
    cliente.loop_start()


def parar():
    cliente.loop_stop()
    cliente.disconnect()


def conectado() -> bool:
    return cliente.is_connected()


def publicar_comando(nome: str, payload: dict, retain: bool):
    """Publica em cultivia/comandos/<nome>.

    qos=1   o broker confirma o recebimento (mais confiável que qos=0).
    retain  o broker GUARDA a última mensagem do tópico e entrega para quem
            assinar depois: se a placa reiniciar, recebe o último comando e
            volta ao estado certo.
    """
    info = cliente.publish(
        f"{config.TOPICO_COMANDOS}/{nome}", json.dumps(payload), qos=1, retain=retain
    )
    if info.rc != mqtt.MQTT_ERR_SUCCESS:
        raise HTTPException(503, "Broker MQTT indisponível")
