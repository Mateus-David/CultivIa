# firmware/esp32/main.py — programa que roda DENTRO do ESP32 (MicroPython).
#
# PAPEL: como não há sensores ligados, ele INVENTA leituras (temperatura e
# umidade) e as manda por WiFi/MQTT, igual à BitDogLab fazia. Também RECEBE
# comandos do site e reage a eles (ventilador, bomba, luz, alvos, intervalo).
#
# FLUXO DOS DADOS:
#   ESP32 --publica--> cultivia/sensores --> Mosquitto --> Telegraf --> InfluxDB --> Grafana
#                                                     \--> API (cache) --> site React
#   ESP32 --publica--> cultivia/estado   --> Mosquitto --> API (cache) --> site React
#   site React --> API --> cultivia/comandos/<nome> --> Mosquitto --> ESP32 (on_comando)
#
# ARQUIVOS: este main.py roda sozinho ao ligar a placa. Ele lê as senhas e
# endereços de config.py (cópia local de config.example.py, ignorada pelo git).
# Os dois precisam ser enviados para a placa (ver firmware/README.md).
import time
import json
import network                       # WiFi do ESP32
import random
from machine import Pin              # controle dos pinos (aqui, só o LED)
from umqtt.simple import MQTTClient  # cliente MQTT (cópia em firmware/lib/umqtt/simple.py)
import config                        # WIFI_SSID, MQTT_BROKER, MQTT_USER... (config.py)

# Tópicos MQTT. O "b" antes das aspas = bytes (é o que o umqtt espera).
# Devem ser iguais aos da API (api/app/config.py) e às permissões em mosquitto/config/acl.
T_SENSORES = b"cultivia/sensores"     # PUBLICA: leituras (o Telegraf e a API leem)
T_ESTADO = b"cultivia/estado"         # PUBLICA: "como estou" (a API/site leem)
T_COMANDOS = b"cultivia/comandos/#"   # ASSINA: comandos do site. "#" = qualquer subtópico
BOMBA_MAX_MS = 60000  # segurança: a bomba desliga sozinha após 60 s

# LED de status (GPIO 2 = LED onboard da maioria dos devkits ESP32).
# getattr(..., 2): usa config.LED_PIN se existir; senão usa 2 (config.py antigo continua funcionando).
led = Pin(getattr(config, "LED_PIN", 2), Pin.OUT)
led.value(0)


def pisca(vezes=1, ms=80):
    """Pisca o LED: aceso `ms` milissegundos, apagado `ms`, repetido `vezes`.
    1 piscada = mensagem enviada; 3 = conectou no broker (ver main/conecta_mqtt)."""
    for _ in range(vezes):
        led.value(1)
        time.sleep_ms(ms)
        led.value(0)
        time.sleep_ms(ms)


# ---------------------------------------------------------------
# Estado da placa (variáveis globais que o programa vai alterando)
# ---------------------------------------------------------------
# Valores simulados (passeio aleatório suave, dentro das faixas do projeto)
temperatura = 25.0  # 0-40 °C
umidade = 60.0      # 0-100 %
botao_a = botao_c = joystick_sw = 0   # botões "falsos", só para manter o formato antigo do payload

# Atuadores simulados: ventilador esfria, bomba aumenta a umidade (ver simula()).
# 1 = ligado, 0 = desligado. Alterado por on_comando(), lido por simula() e publica_estado().
atuadores = {"ventilador": 0, "bomba": 0, "luz": 0}
bomba_ligada_em = 0     # instante (ms) em que a bomba ligou, para o limite de 60 s
# Alvos da simulação: para onde temperatura/umidade tendem (definidos pelo site)
alvo = {"temperatura": 25.0, "umidade": 60.0}
# Controle do envio: pode ser pausado ou ter o intervalo trocado pelo site
envio = {"ativo": True, "intervalo_ms": config.INTERVALO_MS}
# Sinalizador: True = "algo mudou, publique cultivia/estado de novo"
estado_mudou = True


def clamp(v, lo, hi):
    """Limita v ao intervalo [lo, hi]. Ex.: clamp(45, 0, 40) -> 40."""
    return lo if v < lo else hi if v > hi else v


# ---------------------------------------------------------------
# Conexões
# ---------------------------------------------------------------
def conecta_wifi(timeout_s=15):
    """Conecta no WiFi com os dados de config.py. Se não conseguir em
    `timeout_s` segundos, lança OSError — o loop principal (main) captura,
    espera e tenta de novo."""
    wlan = network.WLAN(network.STA_IF)   # STA = a placa é "cliente" de um roteador
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando ao Wi-Fi...")
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        inicio = time.ticks_ms()
        while not wlan.isconnected():
            # ticks_diff: diferença segura entre tempos (o contador de ms dá a volta)
            if time.ticks_diff(time.ticks_ms(), inicio) > timeout_s * 1000:
                raise OSError("timeout Wi-Fi")
            time.sleep_ms(200)
    print("Wi-Fi conectado. IP:", wlan.ifconfig()[0])


def publica_estado(client):
    """Publica em cultivia/estado como a placa está AGORA. É o que faz o botão
    do site mudar: a API guarda esta mensagem e o React a lê em GET /estado.
    retain=True: o Mosquitto guarda a última, então a API a recebe assim que
    conecta, mesmo se a placa tiver publicado antes."""
    global estado_mudou
    d = {"online": 1, "setpoint": alvo, "envio": envio}
    d.update(atuadores)     # acrescenta "ventilador": 0/1, "bomba": ..., "luz": ...
    client.publish(T_ESTADO, json.dumps(d), retain=True)
    estado_mudou = False


def on_comando(topic, msg):
    """CHAMADA AUTOMÁTICA pelo umqtt quando chega mensagem num tópico assinado
    (acontece dentro de client.check_msg(), no loop de main()).
    Recebe o comando vindo do site (site -> API -> Mosquitto -> aqui):

      topic = b"cultivia/comandos/ventilador"   msg = b'{"estado": 1}'
      topic = b"cultivia/comandos/setpoint"     msg = b'{"temperatura": 30, "umidade": 70}'
      topic = b"cultivia/comandos/envio"        msg = b'{"ativo": true, "intervalo_ms": 5000}'

    O último pedaço do tópico (depois da última "/") diz qual comando é."""
    global bomba_ligada_em, estado_mudou
    try:
        nome = topic.decode().split("/")[-1]   # b"cultivia/comandos/bomba" -> "bomba"
        dados = json.loads(msg)                # texto JSON -> dict
        if nome in atuadores:
            atuadores[nome] = 1 if dados.get("estado") else 0
            if nome == "bomba":
                bomba_ligada_em = time.ticks_ms()   # começa a contar os 60 s
        elif nome == "setpoint":
            # clamp: mesmo que chegue lixo, respeita 0-40 °C e 0-100 %
            if "temperatura" in dados:
                alvo["temperatura"] = clamp(float(dados["temperatura"]), 0, 40)
            if "umidade" in dados:
                alvo["umidade"] = clamp(float(dados["umidade"]), 0, 100)
        elif nome == "envio":
            envio["ativo"] = bool(dados.get("ativo", True))
            envio["intervalo_ms"] = int(clamp(int(dados.get("intervalo_ms", 2000)), 500, 60000))
        else:
            return   # subtópico desconhecido: ignora
        estado_mudou = True    # avisa o loop para republicar cultivia/estado
        print("Comando:", nome, dados)
    except Exception as e:  # mensagem malformada não pode derrubar a placa
        print("Comando inválido:", e)


def conecta_mqtt():
    """Conecta no Mosquitto e devolve o cliente pronto para usar."""
    client = MQTTClient(
        config.CLIENT_ID, config.MQTT_BROKER, port=config.MQTT_PORT,
        # login do usuário "esp32" (senha = MQTT_ESP32_PASSWORD do .env do servidor;
        # o Mosquitto confere e aplica as permissões de mosquitto/config/acl)
        user=config.MQTT_USER, password=config.MQTT_PASSWORD, keepalive=30,
    )
    # LAST WILL: mensagem que o BROKER publica por nós se a placa cair sem avisar
    # (perda de WiFi, desligou da tomada...). Faz o site mostrar "offline".
    client.set_last_will(T_ESTADO, b'{"online":0}', retain=True)
    client.set_callback(on_comando)   # "quando chegar mensagem, chame on_comando"
    client.connect()
    client.subscribe(T_COMANDOS)      # começa a ouvir cultivia/comandos/#
    publica_estado(client)            # já avisa que está online
    print("Conectado ao broker MQTT")
    pisca(3, 100)  # 3 piscadas = conexão OK
    return client


# ---------------------------------------------------------------
# Simulação dos sensores
# ---------------------------------------------------------------
def simula():
    """Gera UMA nova leitura e devolve o dict que vira o JSON de cultivia/sensores.
    É chamada a cada intervalo de envio (main). Os nomes das chaves do dict
    precisam bater com telegraf/telegraf.conf (campos do InfluxDB) e com o que
    o site lê em web/src/app/(painel)/_components/LeiturasCard.tsx (temperatura_simulada, umidade_simulada)."""
    global temperatura, umidade, botao_a, botao_c, joystick_sw
    # Cada passo: anda 10% em direção ao alvo + um ruído aleatório pequeno.
    # Ventilador ligado esfria 0,8 °C por leitura; bomba ligada sobe 3 % de umidade.
    temperatura += (alvo["temperatura"] - temperatura) * 0.1 + random.uniform(-0.4, 0.4)
    umidade += (alvo["umidade"] - umidade) * 0.1 + random.uniform(-1.0, 1.0)
    if atuadores["ventilador"]:
        temperatura -= 0.8
    if atuadores["bomba"]:
        umidade += 3.0
    temperatura = clamp(temperatura, 0, 40)
    umidade = clamp(umidade, 0, 100)
    # botões: raramente mudam de estado
    if random.random() < 0.1:
        botao_a = 1 - botao_a
    if random.random() < 0.1:
        botao_c = 1 - botao_c
    if random.random() < 0.05:
        joystick_sw = 1 - joystick_sw
    d = {
        "modo": "joystick",
        "temperatura_simulada": round(temperatura, 2),
        "umidade_simulada": round(umidade, 2),
        "botao_a": botao_a,
        "botao_c": botao_c,
        "joystick_sw": joystick_sw,
    }
    d.update(atuadores)   # inclui ventilador/bomba/luz, para o Grafana poder plotá-los
    return d


# ---------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------
def main():
    """Roda para sempre. A cada volta (100 ms):
      1. (re)conecta WiFi/MQTT se preciso
      2. check_msg(): processa comandos recebidos (chama on_comando)
      3. aplica o limite de tempo da bomba e republica o estado se mudou
      4. se passou o intervalo, publica uma leitura nova
    Qualquer falha de rede (OSError) derruba `client` para None e a volta
    seguinte reconecta sozinha."""
    global estado_mudou
    client = None
    ultimo_envio = 0    # quando publicou a última leitura (ms)
    ultimo_ping = 0     # quando falou com o broker pela última vez (ms)
    while True:
        try:
            if client is None:
                conecta_wifi()
                client = conecta_mqtt()
                ultimo_ping = time.ticks_ms()

            client.check_msg()  # olha se há comando novo (não bloqueia se não houver)

            agora = time.ticks_ms()
            # Segurança: a bomba não fica ligada mais que BOMBA_MAX_MS
            if atuadores["bomba"] and time.ticks_diff(agora, bomba_ligada_em) > BOMBA_MAX_MS:
                atuadores["bomba"] = 0
                estado_mudou = True
                print("Bomba desligada por tempo máximo")
            if estado_mudou:
                publica_estado(client)   # avisa o site do novo estado

            # Envio de leitura: só se não estiver pausado E já passou o intervalo
            if envio["ativo"] and time.ticks_diff(agora, ultimo_envio) >= envio["intervalo_ms"]:
                msg = json.dumps(simula())              # dict -> texto JSON
                client.publish(T_SENSORES, msg)         # -> Mosquitto -> Telegraf/API
                print("Publicado:", msg)
                pisca()  # 1 piscada = mensagem enviada
                ultimo_envio = agora
                ultimo_ping = agora
            elif time.ticks_diff(agora, ultimo_ping) > 15000:
                # Com o envio pausado a placa ficaria muda e o broker a
                # derrubaria (keepalive). O ping mantém a conexão viva.
                client.ping()
                ultimo_ping = agora

            time.sleep_ms(100)   # respiro para não usar 100% da CPU
        except OSError as e:
            print("Erro (reconectando):", e)
            client = None
            led.value(0)  # apagado = sem conexão
            time.sleep(2)


main()
