"""Schemas — o FORMATO dos dados que entram e saem da API.

O FastAPI usa estas classes (Pydantic) para validar sozinho o JSON que chega:
se um campo tiver tipo errado ou valor fora da faixa, ele responde 422 e a
rota nem chega a rodar.

Espelho no site: os tipos TypeScript em web/src/lib/types.ts devem bater
com estas classes.
"""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# Atuadores que existem. Se criar um novo, mexa em 3 lugares:
#   aqui, web/src/lib/atuadores.ts e o dict `atuadores` em firmware/esp32/main.py
NomeAtuador = Literal["ventilador", "bomba", "luz"]


# ---------------------------------------------------------------
# Entrada (corpo dos POST que o site envia)
# ---------------------------------------------------------------
class ComandoAtuador(BaseModel):
    estado: bool                       # true = ligar, false = desligar


class ComandoSetpoint(BaseModel):
    # Optional: dá para mandar só a temperatura, só a umidade, ou as duas.
    # ge/le = "maior/menor ou igual": limites que o site não consegue burlar.
    temperatura: Optional[float] = Field(None, ge=0, le=40)
    umidade: Optional[float] = Field(None, ge=0, le=100)


class ComandoEnvio(BaseModel):
    ativo: bool = True                                   # false = pausa o envio
    intervalo_ms: int = Field(2000, ge=500, le=60000)    # entre 0,5 s e 60 s


# ---------------------------------------------------------------
# Saída (o que as rotas devolvem)
# ---------------------------------------------------------------
class Ok(BaseModel):
    ok: bool = True


class Saude(BaseModel):
    ok: bool
    mqtt: bool


class Estado(BaseModel):
    """Resposta de GET /estado: a foto mais recente da placa."""
    placa_online: bool                  # a API já decide; o site só mostra
    mqtt: bool                          # a API está conectada ao broker?
    recebido_ha_s: Optional[float]      # idade da última leitura (None = nunca chegou)
    # Os dois abaixo são repassados como a placa mandou (dict livre):
    sensores: Optional[dict[str, Any]]      # última mensagem de cultivia/sensores
    dispositivo: Optional[dict[str, Any]]   # última mensagem de cultivia/estado
