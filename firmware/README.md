# Firmware

Programas MicroPython das placas. Cada pasta é **uma placa**; `lib/` é
compartilhada e espelha a pasta `/lib` que fica dentro da placa.

```
firmware/
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

## Enviar para a placa

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
