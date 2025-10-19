# ========= BUILDER =========
FROM python:3.13-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Paquetes de compilación para dependencias (psycopg, Pillow, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --wheel-dir=/wheels -r requirements.txt


# ========= RUNTIME =========
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Libs del sistema que necesitamos en runtime:
# - libmagic1: para python-magic
# - libpq5: cliente PostgreSQL (psycopg)
# - file: util (también provee firmas de libmagic en algunas distros)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 libpq5 file \
    && rm -rf /var/lib/apt/lists/*

# Instala dependencias ya compiladas
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels -r /wheels/requirements.txt && \
    rm -rf /wheels

# Copia el proyecto
COPY . .

# Entrypoint que corre migrate/collectstatic y luego Gunicorn
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Exponer puerto (informativo para algunos runtimes)
EXPOSE 8000

# Comando final: Gunicorn
CMD ["/app/entrypoint.sh", \
     "gunicorn", "BlockFileBE.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120"]
