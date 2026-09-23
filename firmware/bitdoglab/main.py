# firmware/bitdoglab/main.py — programa da BitDogLab (RP2350 W, MicroPython).
#
# PAPEL: lê o joystick (simulando temperatura e umidade) e os botões, desenha
# o histórico do eixo X no OLED e publica as leituras via MQTT a cada 2 s.
#
#   BitDogLab --MQTT--> cultivia/sensores --> Mosquitto --> Telegraf --> InfluxDB --> Grafana
#                                                       \--> API --> site
#
# ARQUIVOS NA PLACA (ver firmware/README.md para enviar):
#   main.py                este arquivo
#   config.py              sua cópia de config.example.py (senhas, IP do broker)
#   lib/umqtt/simple.py    cliente MQTT
#   lib/ssd1306.py         driver do display OLED
import time
import json
import network
from machine import Pin, ADC, SoftI2C
from umqtt.simple import MQTTClient
from ssd1306 import SSD1306_I2C
import config

INTERVALO_ENVIO_MS = 2000

# ---------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------
# Botões com pull-up interno: solto = 1, apertado = 0
btn_a = Pin(5, Pin.IN, Pin.PULL_UP)
btn_b = Pin(6, Pin.IN, Pin.PULL_UP)
btn_c = Pin(10, Pin.IN, Pin.PULL_UP)
joy_sw = Pin(22, Pin.IN, Pin.PULL_UP)

# Eixos analógicos do joystick (0-65535)
joy_x = ADC(Pin(27))
joy_y = ADC(Pin(26))

# Display OLED SSD1306 128x64
i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=400000)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Posições Y do gráfico, uma por coluna da tela (largura = 128)
historico_x = [32] * 128


# ---------------------------------------------------------------
# Leituras
# ---------------------------------------------------------------
def ler_joystick():
    """Devolve (x, y) já corrigidos para a orientação da placa."""
    return 65535 - joy_x.read_u16(), 65535 - joy_y.read_u16()


def ler_botao(pino):
    """1 = apertado, 0 = solto (inverte por causa do pull-up)."""
    return 1 if pino.value() == 0 else 0


def monta_leitura(x, y):
    """Dict que vira o JSON de cultivia/sensores. Os nomes das chaves
    precisam bater com telegraf/telegraf.conf."""
    return {
        "modo": "joystick",
        "temperatura_simulada": x / 65535 * 40,   # 0-40 °C
        "umidade_simulada": y / 65535 * 100,      # 0-100 %
        "botao_a": ler_botao(btn_a),
        "botao_b": ler_botao(btn_b),
        "botao_c": ler_botao(btn_c),
        "joystick_sw": ler_botao(joy_sw),
    }


# ---------------------------------------------------------------
# Display
# ---------------------------------------------------------------
def atualiza_grafico(valor_x):
    """Empurra um ponto novo no histórico e redesenha o gráfico."""
    # 0-65535 -> 63-0 (o eixo Y do display cresce para baixo)
    historico_x.pop(0)
    historico_x.append(63 - int(valor_x / 65535 * 63))

    oled.fill(0)
    oled.text("Eixo X (Temp)", 0, 0)
    for i in range(127):
        oled.line(i, historico_x[i], i + 1, historico_x[i + 1], 1)
    oled.show()


# ---------------------------------------------------------------
# Conexões
# ---------------------------------------------------------------
def conecta_wifi(timeout_s=15):
    """Conecta no WiFi de config.py. Lança OSError se passar do timeout."""
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


def conecta_mqtt():
    """Conecta no Mosquitto (com usuário/senha) e devolve o cliente."""
    client = MQTTClient(
        config.CLIENT_ID, config.MQTT_BROKER, port=config.MQTT_PORT,
        user=config.MQTT_USER, password=config.MQTT_PASSWORD, keepalive=30,
    )
    client.connect()
    print("Conectado ao broker MQTT")
    return client


# ---------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------
def main():
    """O display atualiza a cada volta (animação suave); o MQTT só a cada
    INTERVALO_ENVIO_MS. Se a rede cair, `client` vira None e a próxima
    tentativa de envio reconecta — o display continua funcionando."""
    client = None
    ultimo_envio = 0
    while True:
        x, y = ler_joystick()
        atualiza_grafico(x)

        agora = time.ticks_ms()
        if time.ticks_diff(agora, ultimo_envio) >= INTERVALO_ENVIO_MS:
            ultimo_envio = agora
            try:
                if client is None:
                    conecta_wifi()
                    client = conecta_mqtt()
                msg = json.dumps(monta_leitura(x, y))
                client.publish(config.MQTT_TOPIC, msg)
                print("Publicado:", msg)
            except OSError as e:
                print("Erro de rede (tento de novo no próximo envio):", e)
                client = None

        time.sleep_ms(10)   # respiro para não usar 100% da CPU


main()
