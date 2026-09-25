from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import mqtt
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # liga o MQTT quando a API sobe e desliga quando ela para
    mqtt.iniciar()
    yield
    mqtt.parar()


app = FastAPI(title="CultivIa API", lifespan=lifespan)
app.include_router(router)
