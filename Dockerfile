# ---- Etapa de build: instala dependencias en un venv aislado ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Dependencias del sistema necesarias solo para compilar (no viajan a la imagen final)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY src/requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# ---- Etapa final: imagen liviana, solo con lo necesario para correr ----
FROM python:3.12-slim

WORKDIR /app

# libpq5 = librería de runtime de Postgres (psycopg2-binary la necesita para conectar)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Usuario no-root por seguridad
RUN useradd --create-home appuser

COPY --from=builder /opt/venv /opt/venv
COPY src/ ./src/

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=src/app:app

WORKDIR /app/src
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python -m flask db upgrade --directory flaskapp/migrations && python -m flask seed && python -m gunicorn app:app"]