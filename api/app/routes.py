"""Rotas HTTP — o que o site pode chamar.

No navegador elas aparecem com o prefixo /api; o Next.js remove o prefixo
antes de repassar para cá (ver `rewrites` em web/next.config.ts):
    navegador GET /api/estado  ->  Next.js  ->  http://api:8000/estado

Dois routers:
  publico     sem login (só /health)
  protegido   todas as rotas exigem o token (dependência exige_token)
"""
from fastapi import APIRouter, Depends, HTTPException

from . import mqtt
from .auth import exige_token
from .schemas import (
    ComandoAtuador,
    ComandoEnvio,
    ComandoSetpoint,
    Estado,
    NomeAtuador,
    Ok,
    Saude,
)

publico = APIRouter()
protegido = APIRouter(dependencies=[Depends(exige_token)])


# ---------------------------------------------------------------
# Públicas
# ---------------------------------------------------------------
@publico.get("/health")
def health() -> Saude:
    """A API está viva? E conectada ao broker?"""
    return Saude(ok=True, mqtt=mqtt.conectado())


# ---------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------
@protegido.get("/login")
def login() -> Ok:
    """Não faz nada além de passar pela autenticação.
    A tela de login usa isto para testar o token: 200 = certo, 401 = errado."""
    return Ok()


@protegido.get("/estado")
def estado() -> Estado:
    """O site chama a cada 2 s (polling). Devolve o que está na memória,
    sem consultar o Mosquitto na hora."""
    m = mqtt.memoria
    return Estado(
        placa_online=m.placa_online(),
        mqtt=mqtt.conectado(),
        recebido_ha_s=m.idade_leitura(),
        sensores=m.sensores,
        dispositivo=m.dispositivo,
    )


# ---------------------------------------------------------------
# Comandos (site -> placa)
# ---------------------------------------------------------------
@protegido.post("/atuadores/{nome}")
def atuador(nome: NomeAtuador, corpo: ComandoAtuador) -> Ok:
    """Liga/desliga um atuador. `nome` vem da URL e só aceita os valores de
    NomeAtuador (qualquer outro dá 422)."""
    # A bomba NÃO é retida: se a placa reiniciar, ela não volta ligada
    # sozinha lendo um comando antigo. Segurança.
    mqtt.publicar_comando(nome, {"estado": int(corpo.estado)}, retain=nome != "bomba")
    return Ok()


@protegido.post("/setpoint")
def setpoint(corpo: ComandoSetpoint) -> Ok:
    """Define os alvos da simulação (a placa tende a esses valores)."""
    dados = corpo.model_dump(exclude_none=True)   # só os campos enviados
    if not dados:
        raise HTTPException(422, "Informe temperatura e/ou umidade")
    mqtt.publicar_comando("setpoint", dados, retain=True)
    return Ok()


@protegido.post("/envio")
def envio(corpo: ComandoEnvio) -> Ok:
    """Pausa/retoma o envio de leituras e/ou muda o intervalo."""
    mqtt.publicar_comando("envio", corpo.model_dump(), retain=True)
    return Ok()
