# Single Railway service: nginx → Next.js (/) + Django (/api, /health, /ws)

FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_PUBLIC_API_URL=/api
ENV NEXT_PUBLIC_WS_URL=
RUN npm run build

FROM python:3.13-slim AS backend-deps
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx gettext-base nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=backend-deps /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=backend-deps /usr/local/bin /usr/local/bin
COPY backend/ /app/backend/

COPY --from=frontend-build /app/frontend/.next/standalone /app/frontend/
COPY --from=frontend-build /app/frontend/.next/static /app/frontend/.next/static
COPY --from=frontend-build /app/frontend/public /app/frontend/public

COPY deploy/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY deploy/start.sh /start.sh
RUN chmod +x /start.sh

ENV PYTHONUNBUFFERED=1
ENV USE_SQLITE=True
ENV SQLITE_PATH=/data/db.sqlite3
ENV DJANGO_DEBUG=False
ENV PORT=8080

EXPOSE 8080
CMD ["/start.sh"]
