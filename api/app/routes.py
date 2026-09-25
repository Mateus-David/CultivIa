from fastapi import APIRouter, HTTPException

from . import mqtt
from .schemas import ComandoSetpoint, Estado, Ok, Saude

# no site essas rotas ficam em /api/..., o next.config.ts que tira o prefixo
router = APIRouter()


@router.get("/health")
def health() -> Saude:
    return Saude(ok=True, mqtt=mqtt.conectado())


@router.get("/estado")
def estado() -> Estado:
    # o site chama isso a cada 2s, só devolve o que tá na memória
    m = mqtt.memoria
    return Estado(
        placa_online=m.placa_online(),
        mqtt=mqtt.conectado(),
        recebido_ha_s=m.idade_leitura(),
        sensores=m.sensores,
        dispositivo=m.dispositivo,
    )


@router.post("/setpoint")
def setpoint(corpo: ComandoSetpoint) -> Ok:
    dados = corpo.model_dump(exclude_none=True)
    if not dados:
        raise HTTPException(422, "Informe temperatura e/ou umidade")
    mqtt.publicar_comando("setpoint", dados, retain=True)
    return Ok()
