"""Autenticação — quem pode chamar a API.

O site manda o token no cabeçalho "Authorization: Bearer <token>".
A função `exige_token` é usada como dependência do router protegido em
routes.py: toda rota dele passa por aqui antes de rodar.
"""
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import config

# auto_error=False: se o cabeçalho faltar, quem responde o 401 sou eu
# (com a minha mensagem), e não o FastAPI.
_bearer = HTTPBearer(auto_error=False)


def exige_token(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)):
    """Barra com 401 se o token não bater com o API_TOKEN.

    compare_digest compara em tempo constante: evita que alguém descubra o
    token medindo quanto tempo a resposta demora.
    """
    if cred is None or not secrets.compare_digest(cred.credentials, config.API_TOKEN):
        raise HTTPException(401, "Token inválido")
