FROM python:3.12-slim
WORKDIR /srv

# copio o requirements antes pra não reinstalar tudo toda vez que mudar o código
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

USER nobody

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
