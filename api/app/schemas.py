from typing import Any, Optional

from pydantic import BaseModel, Field

# se mudar algo aqui tem que mudar no web/src/lib/types.ts também


class ComandoSetpoint(BaseModel):
    # pode mandar só um dos dois. as faixas são as mesmas da placa
    temperatura: Optional[float] = Field(None, ge=0, le=50)
    umidade: Optional[float] = Field(None, ge=0, le=100)


class Ok(BaseModel):
    ok: bool = True


class Saude(BaseModel):
    ok: bool
    mqtt: bool


class Estado(BaseModel):
    placa_online: bool
    mqtt: bool
    recebido_ha_s: Optional[float]  # None = nunca chegou leitura
    sensores: Optional[dict[str, Any]]  # último cultivia/sensores
    dispositivo: Optional[dict[str, Any]]  # último cultivia/estado
