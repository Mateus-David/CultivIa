# api/Dockerfile — imagem da API (serviço `api` do docker-compose.yml).
FROM python:3.12-slim
WORKDIR /srv

# Copia SÓ o requirements primeiro: o Docker guarda cada passo em cache, então
# as dependências só são reinstaladas quando o requirements.txt muda.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# O código fica no pacote app/ (ver app/main.py para o mapa dos arquivos)
COPY app ./app

# Roda sem privilégios de root: se alguém invadir, tem menos poder no container.
USER nobody

# "app.main:app" = pacote app, arquivo main.py, variável `app`.
# 0.0.0.0 = aceita conexões de fora do container (o serviço `web`).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
