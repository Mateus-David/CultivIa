import time
import json
import network
from machine import Pin, ADC, SoftI2C
from umqtt.simple import MQTTClient
from ssd1306 import SSD1306_I2C

# ================= Configurações de Rede e MQTT =================
WIFI_SSID = "moto"
WIFI_PASSWORD = "12345678"
MQTT_BROKER = "10.80.102.72"
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

# Inicialização do Display OLED SSD1306
i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=400000)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Lista para armazenar as posições Y do gráfico (largura da tela = 128)
historico_x = [32] * 128 

# ================= Funções Auxiliares =================
def aplicar_orientacao_joystick(raw_x, raw_y):
    x = 65535 - raw_x
    y = 65535 - raw_y
    return x, y

def ler_botao(pino):
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

def atualizar_grafico_oled(valor_x):
    # Mapeia o valor analógico (0-65535) para a altura da tela (63-0)
    # A inversão ocorre porque o eixo Y do display cresce para baixo
    y_mapeado = 63 - int((valor_x / 65535.0) * 63)
    
    # Atualiza a lista deslocando os valores
    historico_x.pop(0)
    historico_x.append(y_mapeado)
    
    # Renderiza o display
    oled.fill(0)
    oled.text("Eixo X (Temp)", 0, 0)
    
    # Desenha o gráfico conectando os pontos da lista com linhas
    for i in range(127):
        oled.line(i, historico_x[i], i+1, historico_x[i+1], 1)
        
    oled.show()

# ================= Loop Principal =================
def main():
    conecta_wifi()
    
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    try:
        client.connect()
        print("Conectado ao Broker MQTT com sucesso!")
    except Exception as e:
        print("Erro ao conectar no MQTT:", e)
        return

    # Variável para rastrear o último momento em que o MQTT foi enviado
    ultimo_envio_mqtt = 0

    while True:
        try:
            # Leituras contínuas
            raw_x, raw_y = joy_x.read_u16(), joy_y.read_u16()
            x_corr, y_corr = aplicar_orientacao_joystick(raw_x, raw_y)

            # Atualiza o gráfico no display frequentemente (animação suave)
            atualizar_grafico_oled(x_corr)

            # Timer não-bloqueante: Publica no MQTT apenas a cada 2000 milissegundos
            agora = time.ticks_ms()
            if time.ticks_diff(agora, ultimo_envio_mqtt) >= 2000:
                estado_a = ler_botao(btn_a)
                estado_b = ler_botao(btn_b)
                estado_c = ler_botao(btn_c)
                estado_sw = ler_botao(joy_sw)
                
                payload = {
                    "temperatura_simulada": x_corr / 65535.0 * 40.0,
                    "umidade_simulada": y_corr / 65535.0 * 100.0,
                    "botao_a": estado_a,
                    "botao_b": estado_b,
                    "botao_c": estado_c,
                    "joystick_sw": estado_sw
                }
                
                mensagem = json.dumps(payload)
                client.publish(MQTT_TOPIC, mensagem)
                print("Publicado:", mensagem)
                
                ultimo_envio_mqtt = agora
            
            # Pequeno delay para a atualização da tela não consumir 100% da CPU
            time.sleep(0.01)
            
        except OSError as e:
            print("Erro no loop principal:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()