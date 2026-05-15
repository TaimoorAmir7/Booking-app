#!/bin/sh
set -e

mkdir -p /data

cd /app/backend
python manage.py migrate --noinput

daphne -b 127.0.0.1 -p 8000 config.asgi:application &

cd /app/frontend
HOSTNAME=127.0.0.1 PORT=3000 node server.js &

export PORT="${PORT:-8080}"
envsubst '${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
