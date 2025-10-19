#!/usr/bin/env bash
set -e

echo "Ejecutando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando aplicación..."
exec "$@"
