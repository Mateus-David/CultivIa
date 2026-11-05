# Firmware

Programas das placas. Cada pasta é **uma placa**. A `estufa/` é a placa de
verdade (Arduino IDE); as outras são MicroPython e usam a `lib/`, que espelha a
pasta `/lib` que fica dentro da placa.

```
firmware/
├── estufa/               ESP32 da estufa: sensores reais, fans e bomba (Arduino IDE)
│   ├── estufa.ino
│   └── config.example.h
├── bitdoglab/            BitDogLab (RP2350 W): joystick + OLED
│   ├── main.py
│   └── config.example.py
├── esp32/                ESP32: simula sensores e recebe comandos do site
│   ├── main.py
│   └── config.example.py
└── lib/                  bibliotecas (vão para /lib na placa)
    ├── umqtt/simple.py   cliente MQTT
    └── ssd1306.py        driver do OLED (só a BitDogLab usa)
```

## Placa da estufa (ESP32 + Arduino IDE)

A ESP e o PC que roda o Docker entram na mesma rede Wi-Fi (ex.: hotspot do
celular). A ESP controla a estufa sozinha e manda os dados pro broker no PC.

```
           mesma rede Wi-Fi (hotspot)
ESP32 ──MQTT──> PC (Docker: Mosquitto, API, site, Grafana)
```

**Ligações**

| Peça | Pino |
|---|---|
| AHT10 (temperatura e umidade do ar) | SDA 21, SCL 22 |
| Sensor capacitivo de solo | 34 (ADC1; o ADC2 não funciona com o Wi-Fi ligado) |
| Fans de ventilação 1 e 2 (PWM) | 32 e 33 |
| Bomba d'água (PWM) | 13 |

**Controle** (roda na placa, funciona mesmo sem o PC)

- **Fans:** ligam quando a temperatura passa de alvo + 0,5 °C, com velocidade
  30 % + 20 % por °C acima do alvo, e desligam ao chegar no alvo. Se o AHT10
  falhar, vão a 100 %.
- **Bomba:** liga quando o solo fica 5 pontos abaixo do alvo, em pulsos de 5 s
  com velocidade 50 % + 5 % por ponto abaixo do alvo, e depois espera 30 s pra
  água infiltrar antes de medir de novo. Com o sensor de solo em falha não liga.
- Os alvos vêm do site (o "Umidade ideal" é a umidade do **solo**) ou da Serial.

**Gravar**

1. Copie o modelo e preencha (o `config.h` é ignorado pelo git):

   ```bash
   cp firmware/estufa/config.example.h firmware/estufa/config.h
   ```

   `MQTT_PASSWORD` é a `MQTT_ESP32_PASSWORD` do `.env`.

2. Na Arduino IDE:
   - Placa: instale o pacote **esp32** da Espressif (Gerenciador de Placas) e
     escolha **ESP32 Dev Module**
   - Bibliotecas (Gerenciador de Bibliotecas): **Adafruit AHTX0**,
     **PubSubClient** (Nick O'Leary) e **ArduinoJson** (Benoit Blanchon, versão 7)
   - Abra o `firmware/estufa/estufa.ino`, escolha a porta COM e clique em Carregar
   - Monitor Serial a 115200

3. Conecte o PC na mesma rede, veja o IP dele com `ipconfig` e coloque no
   `MQTT_BROKER` do `config.h` antes de gravar. A rede tem que ser 2.4GHz.

4. Libere a porta 1883 (e 8080/3000 se outros aparelhos forem abrir o site) no
   Firewall do Windows. Uma rede nova entra como "Pública", e o Windows
   costuma bloquear o Docker nela. Uma opção é marcar a rede como **Privada**.

Na Serial aparece `mqtt=ok` quando a placa conectou no broker. Se aparecer
`Falha no MQTT (estado -2)`, o PC não respondeu (IP ou firewall); estado 4 ou 5
é usuário/senha.

**Comandos pela Serial:** `T26.5` muda o alvo de temperatura, `S55` o de umidade
do solo, `D` grava a leitura atual do solo como seca e `W` como molhada. A
calibração `D`/`W` se perde ao reiniciar, então anote os valores e grave em
`SOIL_DRY`/`SOIL_WET` no `estufa.ino`.

## Placas MicroPython (BitDogLab e ESP32 simulada)

1. Copie o modelo e preencha (o `config.py` é ignorado pelo git):

   ```bash
   cp firmware/esp32/config.example.py firmware/esp32/config.py
   ```

   A senha `MQTT_PASSWORD` é a `MQTT_ESP32_PASSWORD` do `.env` do servidor.

2. Envie com o [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html)
   (`pip install mpremote`), a partir da pasta `firmware/`:

   ```bash
   cd firmware
   mpremote cp -r lib :                               # bibliotecas -> /lib
   mpremote cp esp32/main.py esp32/config.py :        # troque esp32 por bitdoglab
   mpremote reset
   ```

   No Thonny é o mesmo: crie `/lib` na placa e suba os arquivos nas mesmas posições.
