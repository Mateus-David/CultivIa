import time
import json
import random
import network
from machine import Pin
from umqtt.simple import MQTTClient
import config

T_SENSORES = b"cultivia/sensores"
T_ESTADO = b"cultivia/estado"
T_SETPOINT = b"cultivia/comandos/setpoint"

INTERVALO_MS = 2000

led = Pin(2, Pin.OUT)  # led da placa, na maioria dos devkits é o GPIO 2
led.value(0)

# não tem sensor ligado, então os valores vão andando sozinhos até o alvo
temperatura = 25.0
umidade = 50.0
alvo = {"temperatura": 25.0, "umidade": 50.0}
alvo_mudou = True


def limitar(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def pisca(vezes=1, ms=80):
    # 1 piscada = mandou leitura, 3 = conectou no broker
    for _ in range(vezes):
        led.value(1)
        time.sleep_ms(ms)
        led.value(0)
        time.sleep_ms(ms)


def conecta_wifi(timeout_s=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando ao Wi-Fi...")
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        inicio = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), inicio) > timeout_s * 1000:
                raise OSError("timeout Wi-Fi")
            time.sleep_ms(200)
    print("Wi-Fi conectado. IP:", wlan.ifconfig()[0])


def ao_receber(topico, msg):
    # alvo novo vindo do site, ex: {"temperatura": 28, "umidade": 60}
    global alvo_mudou
    try:
        dados = json.loads(msg)
        if "temperatura" in dados:
            alvo["temperatura"] = limitar(float(dados["temperatura"]), 0, 50)
        if "umidade" in dados:
            alvo["umidade"] = limitar(float(dados["umidade"]), 0, 100)
        alvo_mudou = True
        print("Alvos do site:", alvo)
    except Exception as e:
        print("Mensagem invalida:", e)


def publica_estado(client):
    global alvo_mudou
    estado = {"online": 1, "setpoint": alvo}
    client.publish(T_ESTADO, json.dumps(estado), retain=True)
    alvo_mudou = False


def conecta_mqtt():
    client = MQTTClient(
        config.CLIENT_ID, config.MQTT_BROKER, port=config.MQTT_PORT,
        user=config.MQTT_USER, password=config.MQTT_PASSWORD, keepalive=30,
    )
    # se a placa cair o broker publica isso no lugar dela e o site mostra offline
    client.set_last_will(T_ESTADO, b'{"online": 0}', retain=True)
    client.set_callback(ao_receber)
    client.connect()
    client.subscribe(T_SETPOINT)
    publica_estado(client)
    print("Conectado ao broker MQTT")
    pisca(3, 100)
    return client


def simula():
    # anda 10% em direção ao alvo + um ruído pequeno
    global temperatura, umidade
    temperatura += (alvo["temperatura"] - temperatura) * 0.1 + random.uniform(-0.4, 0.4)
    umidade += (alvo["umidade"] - umidade) * 0.1 + random.uniform(-1.0, 1.0)
    temperatura = limitar(temperatura, 0, 50)
    umidade = limitar(umidade, 0, 100)
    # mesmo formato da BitDogLab, as chaves tem que bater com o telegraf.conf
    return {
        "modo": "joystick",
        "temperatura_simulada": round(temperatura, 2),
        "umidade_simulada": round(umidade, 2),
        "temperatura_ideal": alvo["temperatura"],
        "umidade_ideal": alvo["umidade"],
    }


def main():
    client = None
    ultimo_envio = 0
    while True:
        try:
            if client is None:
                conecta_wifi()
                client = conecta_mqtt()

            client.check_msg()  # se chegou algo chama o ao_receber
            if alvo_mudou:
                publica_estado(client)

            agora = time.ticks_ms()
            if time.ticks_diff(agora, ultimo_envio) >= INTERVALO_MS:
                msg = json.dumps(simula())
                client.publish(T_SENSORES, msg)
                print("Publicado:", msg)
                pisca()
                ultimo_envio = agora

            time.sleep_ms(100)
        except OSError as e:
            # caiu a rede, zera o client e na próxima volta conecta tudo de novo
            print("Erro, reconectando:", e)
            client = None
            led.value(0)
            time.sleep(2)


main()
