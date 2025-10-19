#!/usr/bin/env bash
set -e

# Espera breve por la DB en ambientes lentos (opcional)
# sleep 2

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Ejecuta el comando que pase Docker (CMD)
exec "$@"
