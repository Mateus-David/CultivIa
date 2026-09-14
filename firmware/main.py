import time
import json
import network
from machine import Pin, ADC
from umqtt.simple import MQTTClient

# ================= Configurações de Rede e MQTT =================
WIFI_SSID = "iPhone de Victor"
WIFI_PASSWORD = "20200767"
MQTT_BROKER = "172.20.10.8"
MQTT_PORT = 1883
MQTT_TOPIC = "cultivia/sensores"
CLIENT_ID = "BitDogLab_CultivIA"

# ================= Configuração de Hardware =================
# Botões com pull-up interno
btn_a = Pin(5, Pin.IN, Pin.PULL_UP)
btn_b = Pin(6, Pin.IN, Pin.PULL_UP)
btn_c = Pin(10, Pin.IN, Pin.PULL_UP)
joy_sw = Pin(22, Pin.IN, Pin.PULL_UP)

# Eixos analógicos do Joystick
joy_x = ADC(Pin(27))
joy_y = ADC(Pin(26))

# ================= Funções Auxiliares =================
def aplicar_orientacao_joystick(raw_x, raw_y):
    # Inverte logicamente os eixos subtraindo do valor máximo (16 bits)
    x = 65535 - raw_x
    y = 65535 - raw_y
    return x, y

def ler_botao(pino):
    # Retorna 1 se pressionado (LOW), 0 se solto (HIGH)
    return 1 if pino.value() == 0 else 0

def conecta_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando ao Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print("Wi-Fi Conectado. IP:", wlan.ifconfig()[0])

# ================= Loop Principal =================
def main():
    conecta_wifi()
    
    # Inicializa o cliente MQTT
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    try:
        client.connect()
        print("Conectado ao Broker MQTT com sucesso!")
    except Exception as e:
        print("Erro ao conectar no MQTT:", e)
        return

    while True:
        try:
            # Leitura dos botões
            estado_a = ler_botao(btn_a)
            estado_b = ler_botao(btn_b)
            estado_c = ler_botao(btn_c)
            estado_sw = ler_botao(joy_sw)

            # Leitura e inversão lógica do joystick
            raw_x, raw_y = joy_x.read_u16(), joy_y.read_u16()
            x_corr, y_corr = aplicar_orientacao_joystick(raw_x, raw_y)

            # Estrutura JSON simulando temperatura, umidade, saúde e acionamentos
            payload = {
                "temperatura_simulada": x_corr / 65535.0 * 40.0, # Mapeia X para 0-40°C
                "umidade_simulada": y_corr / 65535.0 * 100.0,    # Mapeia Y para 0-100%
                "botao_a": estado_a,
                "botao_b": estado_b,
                "botao_c": estado_c,
                "joystick_sw": estado_sw
            }
            
            mensagem = json.dumps(payload)
            client.publish(MQTT_TOPIC, mensagem)
            print("Publicado:", mensagem)
            
            # Aguarda 2 segundos antes da próxima atualização
            time.sleep(2)
            
        except OSError as e:
            print("Erro de conexão no loop, tentando reconectar...", e)
            time.sleep(5)
            # Em aplicações reais, adicione uma rotina robusta de reconexão ao Wi-Fi e MQTT aqui

if __name__ == "__main__":
    main()