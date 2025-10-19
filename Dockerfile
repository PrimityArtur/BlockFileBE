# ============================
#  STAGE 1: BUILDER
# ============================
FROM python:3.13-slim AS builder

# Configuración base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Instala dependencias necesarias para compilar paquetes
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependencias en formato wheel
COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --wheel-dir=/wheels -r requirements.txt


# ============================
#  STAGE 2: RUNTIME
# ============================
FROM python:3.13-slim

# Variables de entorno para Python y Django
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Instala dependencias del sistema necesarias para runtime
# - libmagic1: para python-magic
# - libpq5: driver PostgreSQL
# - file: binario que provee las definiciones de libmagic
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    libpq5 \
    file \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo requirements y los wheels construidos
COPY requirements.txt .
COPY --from=builder /wheels /wheels

# Instala dependencias usando los wheels (más rápido)
RUN pip install --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels

# Copia el código del proyecto Django y el entrypoint
COPY . .
COPY entrypoint.sh /app/entrypoint.sh

# Da permisos de ejecución al entrypoint
RUN chmod +x /app/entrypoint.sh

# Expone el puerto de la aplicación
EXPOSE 8000

# Comando de inicio (ejecuta migraciones y luego arranca Gunicorn)
CMD ["/app/entrypoint.sh", \
     "gunicorn", "BlockFileBE.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120"]
