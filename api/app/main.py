"""API do CultivIa — ponto de entrada (o uvicorn roda `app.main:app`).

PAPEL: é a "ponte" entre o site e a placa. O navegador só fala HTTP;
a placa só fala MQTT. Esta API traduz um para o outro.

  COMANDAR (site -> placa)
    site --HTTP POST--> [API] --MQTT--> Mosquitto --> ESP32

  LER (placa -> site)
    ESP32 --MQTT--> Mosquitto --> [API guarda na memória] --HTTP GET /estado--> site

MAPA DOS ARQUIVOS (app/):
  main.py     este: cria o app e liga/desliga o MQTT
  config.py   variáveis de ambiente e nomes dos tópicos
  mqtt.py     cliente MQTT, memória da última leitura, publicar_comando()
  auth.py     confere o token (Authorization: Bearer ...)
  schemas.py  formato dos JSON que entram e saem (validação)
  routes.py   as rotas HTTP
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import mqtt
from .routes import protegido, publico


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Roda ao SUBIR (antes do yield) e ao DESLIGAR (depois do yield)."""
    mqtt.iniciar()
    yield
    mqtt.parar()


app = FastAPI(title="CultivIa API", lifespan=lifespan)
app.include_router(publico)
app.include_router(protegido)
