# O que foi feito no CultivIa

Resumo de tudo que a gente fez no projeto até agora, na ordem em que foi acontecendo. Pra saber como rodar, ver o [README](README.md).

## A ideia

Monitorar uma estufa com IoT. Uma placa lê temperatura e umidade e manda por Wi-Fi via MQTT pro computador. Lá, o histórico fica guardado e aparece num dashboard, e um site deixa definir a temperatura e a umidade ideais que a placa deve seguir.

Ainda não temos os sensores de verdade, então por enquanto os valores são simulados: na BitDogLab pelo joystick e no ESP32 por uma função.

## Linha do tempo

### 1. Firmware inicial (14/09)

- Primeiro `main.py` da BitDogLab em MicroPython, lendo o joystick e os botões e publicando no MQTT
- No começo o broker era público (`broker.hivemq.com`), só pra testar se a mensagem chegava
- Depois colocamos o display OLED mostrando um gráfico do eixo X do joystick
- Libs usadas: `umqtt.simple` (MQTT) e `ssd1306` (OLED)

### 2. Stack TIG com Docker (14/09, PR #1)

- Trocamos o broker público por um **Mosquitto** local rodando no Docker
- Montamos a stack **Telegraf + InfluxDB + Grafana** no `docker-compose.yml`
  - Telegraf assina `cultivia/sensores` e grava no InfluxDB (measurement `estufa`)
  - Grafana já sobe com o datasource e o dashboard prontos (pasta `grafana/`)
- Senhas e tokens foram pro `.env`, com um `.env.example` de modelo
- Resultado: temperatura do joystick aparecendo no Grafana em tempo real

Problemas de rede que deram trabalho nessa parte:

- O Mosquitto 2 só aceita localhost por padrão, tivemos que colocar `listener 1883 0.0.0.0`
- O PC roda o Docker no WSL2, então usamos o modo `mirrored` pro WSL ter o mesmo IP do Windows
- Tivemos que liberar a porta 1883 no firewall do Windows
- O Mosquitto instalado pelo apt conflitava na porta 1883, então deixamos ele desligado

### 3. API e primeiro site (23/09)

- Criamos uma **API em FastAPI** pra ser a ponte entre o site (HTTP) e a placa (MQTT)
- Criamos um **site em Next.js** (React + TypeScript + Tailwind)
- Essa primeira versão tinha login com token e controle de atuadores simulados (ventilador, bomba e luz), além de pausar o envio e mudar o intervalo
- Segurança no Mosquitto: cada cliente tem usuário e senha (`esp32`, `api`, `telegraf`) e uma ACL dizendo quem pode publicar e assinar cada tópico. As senhas são geradas a partir do `.env` quando o container sobe, então não ficam no repo
- O firmware foi separado em `firmware/bitdoglab/` e `firmware/esp32/`, com as libs em `firmware/lib/`, e as credenciais foram pro `config.py` (fora do git)

### 4. Versão atual (25/09)

Simplificamos o site e deixamos a BitDogLab bem mais completa.

**BitDogLab**

- O joystick sobe e desce a temperatura (0 a 50 °C) ou a umidade (0 a 100 %), e o clique alterna entre as duas
- O OLED tem 2 telas (temperatura e umidade), cada uma com o valor, o alvo, o status (OK / ATENÇÃO / ALERTA) e uma barra com a posição do alvo
- O botão C troca o modo dos botões A/B: no modo ATUAL eles trocam de tela, no ALVO mudam o alvo (-1 / +1)
- A matriz de LED 5x5 fica laranja ou vermelha conforme a distância até o alvo, e o buzzer apita no vermelho
- A rede não trava mais o programa: o Wi-Fi conecta em segundo plano e, se cair, tenta de novo a cada 5 s
- Publica as leituras a cada 2 s e o estado (online + alvos) com retain e Last Will, pro site saber quando a placa cai

**Site e API**

- Tiramos o login: o sistema é só pra rede local
- Tiramos os atuadores. O site agora tem a logo, um card com a temperatura e a umidade ideais e o dashboard do Grafana embutido num iframe
- A API ficou com 3 rotas: `/health`, `/estado` e `/setpoint`
- O setpoint é publicado com retain, então a placa recebe o alvo mesmo se estiver desligada na hora e conectar depois
- Se o alvo mudar pelos botões da placa, o site também atualiza

**ESP32**

- Ficou como placa alternativa: simula os valores indo em direção ao alvo e recebe o setpoint do site, igual à BitDogLab

**Limpeza**

- Tiramos o código que não era mais usado (login, atuadores, campos velhos no Telegraf, props sem uso no site)
- Reescrevemos os comentários pra ficarem curtos e diretos
- Criamos a logo (`web/src/app/icon.svg`, com uma versão em `logo.png`)

## Como está funcionando agora

```
BitDogLab --MQTT--> Mosquitto --> Telegraf --> InfluxDB --> Grafana
                        ^   |
                        |   v
                   API (FastAPI) <--> Site (Next.js) <--> navegador
```

| Tópico | Quem publica | Pra quê |
|---|---|---|
| `cultivia/sensores` | placa, a cada 2 s | leituras (vai pro InfluxDB e pra API) |
| `cultivia/estado` | placa, retido | online + alvos que a placa está usando |
| `cultivia/comandos/setpoint` | API, retido | alvos definidos no site |

## O que falta / pendências

- Ligar sensores de verdade no lugar do joystick e da simulação
- Não dá pra ligar as duas placas juntas, porque as duas publicam no mesmo `cultivia/estado`
- O commit `d128d4a` ainda tem a senha antiga do Wi-Fi no histórico do git
- Site e Grafana não têm login, então só devem ser usados na rede local
