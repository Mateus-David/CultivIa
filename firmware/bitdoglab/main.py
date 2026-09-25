import time
import json
import network
import framebuf
from machine import Pin, ADC, SoftI2C, PWM
from ssd1306 import SSD1306_I2C
from neopixel import NeoPixel
from umqtt.simple import MQTTClient, MQTTException
import config

# ================= Hardware =================
# botões com pull-up: 1 solto, 0 apertado
btn_a = Pin(5, Pin.IN, Pin.PULL_UP)
btn_b = Pin(6, Pin.IN, Pin.PULL_UP)
btn_c = Pin(10, Pin.IN, Pin.PULL_UP)
joy_sw = Pin(22, Pin.IN, Pin.PULL_UP)

joy_y = ADC(Pin(26))

i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

matriz = NeoPixel(Pin(7), 25)

buzzer = PWM(Pin(21))
buzzer.freq(2000)
buzzer.duty_u16(0)

wlan = network.WLAN(network.STA_IF)
cliente_mqtt = MQTTClient(
    config.CLIENT_ID, config.MQTT_BROKER, port=config.MQTT_PORT,
    user=config.MQTT_USER, password=config.MQTT_PASSWORD, keepalive=30,
)

# ================= Configurações =================
TEMP_MIN, TEMP_MAX = 0, 50
UMID_MIN, UMID_MAX = 0, 100

# quanto o valor muda por ciclo com o joystick no máximo
VEL_TEMP = 0.3
VEL_UMID = 1.0

PASSO_ALVO_TEMP = 1
PASSO_ALVO_UMID = 5

# distância até o alvo pra ficar laranja / vermelho
TEMP_LARANJA, TEMP_VERMELHO = 5, 10
UMID_LARANJA, UMID_VERMELHO = 10, 20

# ok, atenção e alerta. deixei o brilho baixo pq a matriz no máximo é forte demais
CORES_NIVEL = [(0, 0, 0), (40, 12, 0), (40, 0, 0)]
NOMES_NIVEL = ["OK", "ATENCAO", "ALERTA"]  # sem acento pq a fonte do oled não tem

VOLUME_BUZZER = 2000  # vai até 32768
ZONA_MORTA = 4000  # pro joystick parado não ficar mexendo no valor

T_SENSORES = b"cultivia/sensores"
T_ESTADO = b"cultivia/estado"
T_SETPOINT = b"cultivia/comandos/setpoint"

INTERVALO_ENVIO_MS = 2000
RECONEXAO_MS = 5000

# ================= Ícones =================
# cada "#" é um pixel aceso no oled
ICONE_TERMOMETRO = [
    "..###..",
    ".#...#.",
    ".#.#.#.",
    ".#.#.#.",
    ".#.#.#.",
    ".#.#.#.",
    ".#.#.#.",
    ".#.#.#.",
    ".#.#.#.",
    "#..#..#",
    "#.###.#",
    "#.###.#",
    "#.....#",
    ".#...#.",
    "..###..",
]

ICONE_GOTA = [
    "....#....",
    "....#....",
    "...#.#...",
    "...#.#...",
    "..#...#..",
    "..#...#..",
    ".#.....#.",
    ".#.....#.",
    "#.......#",
    "#.#.....#",
    "#.#.....#",
    ".#.#...#.",
    "..#...#..",
    "...###...",
]

ICONE_ALVO = [
    "..###..",
    ".#...#.",
    "#..#..#",
    "#.###.#",
    "#..#..#",
    ".#...#.",
    "..###..",
]

# ================= Estado =================
temperatura = 25.0
umidade = 50.0
alvo_temp = 25.0
alvo_umid = 50.0

NUM_TELAS = 2  # 0 = temperatura, 1 = umidade
tela_atual = 0

# o botão C troca o que o A/B faz: ATUAL troca de tela, ALVO mexe no alvo
MODOS = ["ATUAL", "ALVO"]
modo_atual = 0

joy_controla = "TEMP"  # clique do joystick troca entre TEMP e UMID

estado_anterior = {}  # usado no clicou()

mqtt_ok = False
ultimo_envio = 0
ultima_tentativa = 0
alvos_mudaram = True  # quando True publica o cultivia/estado de novo
alvo_do_site = None
acabou_de_conectar = False

# ================= Funções =================
def clicou(pino, nome):
    # só da True na hora que aperta, senão segurar o botão conta vários cliques
    apertado = pino.value() == 0
    antes = estado_anterior.get(nome, False)
    estado_anterior[nome] = apertado
    return apertado and not antes


def ler_joystick():
    # de -1 a 1, 0 é o centro. se ficar invertido é só inverter a conta
    desvio = 32768 - joy_y.read_u16()
    if abs(desvio) < ZONA_MORTA:
        return 0
    return desvio / 32768


def apertado(pino):
    return 1 if pino.value() == 0 else 0


def limitar(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def calcular_nivel(atual, alvo, limite_laranja, limite_vermelho):
    # 0 = ok, 1 = laranja, 2 = vermelho
    diferenca = abs(atual - alvo)
    if diferenca >= limite_vermelho:
        return 2
    if diferenca >= limite_laranja:
        return 1
    return 0


def piscando():
    # alterna a cada 300ms, uso pra piscar o ALERTA
    return (time.ticks_ms() // 300) % 2 == 0


def desligar_tudo():
    matriz.fill((0, 0, 0))
    matriz.write()
    buzzer.duty_u16(0)
    oled.fill(0)
    oled.show()

# ================= Desenho =================
def desenhar_icone(icone, x, y, cor=1):
    for linha, texto in enumerate(icone):
        for coluna, caractere in enumerate(texto):
            if caractere == "#":
                oled.pixel(x + coluna, y + linha, cor)


def texto_grande(texto, x, y, escala):
    # a fonte do oled só tem 8x8, então escrevo num framebuffer pequeno
    # e desenho cada pixel dele como um quadrado maior
    largura = len(texto) * 8
    buffer = bytearray(largura)
    tela_pequena = framebuf.FrameBuffer(buffer, largura, 8, framebuf.MONO_VLSB)
    tela_pequena.text(texto, 0, 0, 1)
    for px in range(largura):
        for py in range(8):
            if tela_pequena.pixel(px, py):
                oled.fill_rect(x + px * escala, y + py * escala, escala, escala, 1)


def desenhar_cabecalho(titulo):
    # faixa branca com o título e as bolinhas das telas na direita
    oled.fill_rect(0, 0, 128, 11, 1)
    oled.text(titulo, 3, 2, 0)
    for i in range(NUM_TELAS):
        x = 128 - (NUM_TELAS - i) * 7
        if i == tela_atual:
            oled.fill_rect(x, 3, 5, 5, 0)
        else:
            oled.rect(x, 3, 5, 5, 0)


def desenhar_rodape():
    oled.hline(0, 54, 128, 1)
    oled.text("MODO OP:" + MODOS[modo_atual], 15, 56)


def tela_valor(icone, atual, alvo, minimo, maximo, unidade, nivel, editando):
    # linha 1: ícone + valor grande, centralizado
    if unidade == "C":
        texto = "{:.1f}".format(atual)
    else:
        texto = "{:.0f}".format(atual)

    largura_icone = len(icone[0])
    largura_numero = len(texto) * 16  # 8px por letra * escala 2
    largura_unidade = 12 if unidade == "C" else 8
    total = largura_icone + 5 + largura_numero + 3 + largura_unidade
    x = (128 - total) // 2

    desenhar_icone(icone, x, 16)
    x += largura_icone + 5
    texto_grande(texto, x, 15, 2)
    x += largura_numero + 3
    if unidade == "C":
        oled.rect(x, 15, 3, 3, 1)  # bolinha do grau
        oled.text("C", x + 4, 15)
    else:
        oled.text("%", x, 15)

    # linha 2: alvo na esquerda, status na direita
    texto_alvo = "{:.0f}".format(alvo) + unidade
    cor = 1
    if editando:
        # fundo branco no alvo quando o A/B tá mexendo nele
        oled.fill_rect(0, 32, 7 + 3 + len(texto_alvo) * 8 + 4, 10, 1)
        cor = 0
    desenhar_icone(ICONE_ALVO, 2, 33, cor)
    oled.text(texto_alvo, 12, 33, cor)

    status = NOMES_NIVEL[nivel]
    x_status = 126 - len(status) * 8
    # OK normal, ATENCAO com fundo branco, ALERTA piscando
    if nivel == 0 or (nivel == 2 and piscando()):
        oled.text(status, x_status, 33, 1)
    else:
        oled.fill_rect(x_status - 2, 32, len(status) * 8 + 4, 10, 1)
        oled.text(status, x_status, 33, 0)

    # linha 3: barra do valor com uma setinha em cima do alvo
    oled.rect(0, 45, 128, 7, 1)
    preenchido = int((atual - minimo) / (maximo - minimo) * 124)
    oled.fill_rect(2, 47, preenchido, 3, 1)
    x_alvo = 2 + int((alvo - minimo) / (maximo - minimo) * 123)
    oled.hline(x_alvo - 2, 42, 5, 1)
    oled.hline(x_alvo - 1, 43, 3, 1)
    oled.pixel(x_alvo, 44, 1)
    oled.vline(x_alvo, 46, 5, 1)

# ================= Rede =================
def iniciar_rede():
    # não espero o wifi conectar aqui, quem cuida disso é o cuidar_da_rede()
    wlan.active(True)
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    # se a placa cair o broker publica isso no lugar dela e o site mostra offline
    cliente_mqtt.set_last_will(T_ESTADO, b'{"online": 0}', retain=True)
    cliente_mqtt.set_callback(ao_receber)


def ao_receber(topico, msg):
    # alvo novo vindo do site, ex: {"temperatura": 28, "umidade": 60}
    global alvo_temp, alvo_umid, alvos_mudaram, alvo_do_site, acabou_de_conectar
    # quando reconecta o broker manda de novo o último alvo (retido). se for o mesmo
    # que eu já apliquei ignoro, senão uma queda de wifi desfaz o que mudei no A/B
    repetido = acabou_de_conectar and msg == alvo_do_site
    acabou_de_conectar = False
    if repetido:
        return
    alvo_do_site = msg
    try:
        dados = json.loads(msg)
        if "temperatura" in dados:
            alvo_temp = limitar(float(dados["temperatura"]), TEMP_MIN, TEMP_MAX)
        if "umidade" in dados:
            alvo_umid = limitar(float(dados["umidade"]), UMID_MIN, UMID_MAX)
        alvos_mudaram = True
        print("Alvos do site:", alvo_temp, "C /", alvo_umid, "%")
    except Exception as e:
        print("Mensagem invalida:", e)


def conectar_mqtt():
    global mqtt_ok, alvos_mudaram, acabou_de_conectar
    # timeout de 2s pro display não travar se o broker não responder
    try:
        cliente_mqtt.connect(timeout=2)
    except TypeError:
        # umqtt antigo na placa não tem timeout, manda o firmware/lib de novo
        cliente_mqtt.connect()
    acabou_de_conectar = True
    cliente_mqtt.subscribe(T_SETPOINT)
    mqtt_ok = True
    alvos_mudaram = True
    print("MQTT conectado. IP da placa:", wlan.ifconfig()[0])


def publicar_estado():
    global alvos_mudaram
    estado = {"online": 1, "setpoint": {"temperatura": alvo_temp, "umidade": alvo_umid}}
    cliente_mqtt.publish(T_ESTADO, json.dumps(estado), retain=True)
    alvos_mudaram = False


def publicar_leitura():
    # as chaves tem que bater com o telegraf.conf
    leitura = {
        "modo": "joystick",
        "temperatura_simulada": round(temperatura, 2),
        "umidade_simulada": round(umidade, 2),
        "temperatura_ideal": alvo_temp,
        "umidade_ideal": alvo_umid,
        "botao_a": apertado(btn_a),
        "botao_c": apertado(btn_c),
        "joystick_sw": apertado(joy_sw),
    }
    cliente_mqtt.publish(T_SENSORES, json.dumps(leitura))


def cuidar_da_rede():
    # roda todo ciclo mas nunca fica esperando a rede, se não deu tenta de novo em 5s
    global mqtt_ok, ultima_tentativa, ultimo_envio
    agora = time.ticks_ms()

    if not mqtt_ok:
        if time.ticks_diff(agora, ultima_tentativa) < RECONEXAO_MS:
            return
        ultima_tentativa = agora
        if not wlan.isconnected():
            if wlan.status() <= 0:  # parado ou deu erro, pede pra conectar de novo
                wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
            print("Aguardando Wi-Fi...")
            return
        try:
            conectar_mqtt()
        except (OSError, MQTTException) as e:  # MQTTException normalmente é senha errada
            print("Falha no MQTT (confira o IP em config.py):", e)
            return

    try:
        cliente_mqtt.check_msg()  # se chegou algo chama o ao_receber
        if alvos_mudaram:
            publicar_estado()
        if time.ticks_diff(agora, ultimo_envio) >= INTERVALO_ENVIO_MS:
            ultimo_envio = agora
            publicar_leitura()
    except OSError as e:
        print("Conexao MQTT perdida:", e)
        mqtt_ok = False

# ================= Loop principal =================
desligar_tudo()
iniciar_rede()

try:
    while True:
        if clicou(btn_c, "C"):
            modo_atual = (modo_atual + 1) % len(MODOS)

        if clicou(joy_sw, "J"):
            joy_controla = "UMID" if joy_controla == "TEMP" else "TEMP"

        # A = -1, B = +1
        direcao = 0
        if clicou(btn_a, "A"):
            direcao = -1
        if clicou(btn_b, "B"):
            direcao = +1

        if direcao != 0:
            modo = MODOS[modo_atual]
            if modo == "ATUAL":
                tela_atual = (tela_atual + direcao) % NUM_TELAS
            elif modo == "ALVO" and tela_atual == 0:
                alvo_temp = limitar(alvo_temp + direcao * PASSO_ALVO_TEMP, TEMP_MIN, TEMP_MAX)
                alvos_mudaram = True
            elif modo == "ALVO" and tela_atual == 1:
                alvo_umid = limitar(alvo_umid + direcao * PASSO_ALVO_UMID, UMID_MIN, UMID_MAX)
                alvos_mudaram = True

        # quanto mais longe do centro mais rápido muda
        j = ler_joystick()
        if joy_controla == "TEMP":
            temperatura = limitar(temperatura + j * VEL_TEMP, TEMP_MIN, TEMP_MAX)
        else:
            umidade = limitar(umidade + j * VEL_UMID, UMID_MIN, UMID_MAX)

        cuidar_da_rede()

        # alerta vale o pior entre temperatura e umidade
        nivel_temp = calcular_nivel(temperatura, alvo_temp, TEMP_LARANJA, TEMP_VERMELHO)
        nivel_umid = calcular_nivel(umidade, alvo_umid, UMID_LARANJA, UMID_VERMELHO)
        nivel_geral = max(nivel_temp, nivel_umid)

        matriz.fill(CORES_NIVEL[nivel_geral])
        matriz.write()

        # no vermelho apita 150ms a cada 1s
        if nivel_geral == 2 and (time.ticks_ms() % 1000) < 150:
            buzzer.duty_u16(VOLUME_BUZZER)
        else:
            buzzer.duty_u16(0)

        oled.fill(0)
        if tela_atual == 0:
            desenhar_cabecalho("TEMPERATURA")
            tela_valor(ICONE_TERMOMETRO, temperatura, alvo_temp, TEMP_MIN, TEMP_MAX,
                       "C", nivel_temp, MODOS[modo_atual] == "ALVO")
        else:
            desenhar_cabecalho("UMIDADE")
            tela_valor(ICONE_GOTA, umidade, alvo_umid, UMID_MIN, UMID_MAX,
                       "%", nivel_umid, MODOS[modo_atual] == "ALVO")
        desenhar_rodape()
        oled.show()

        time.sleep(0.05)

finally:
    # pra não ficar apitando/aceso quando dou stop no Thonny
    desligar_tudo()
