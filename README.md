# Appointment Assistant

Full-stack assessment project: **Next.js** frontend, **Django** REST/WebSocket API, **PostgreSQL**, **Mistral** AI.

## Project layout

```
assessment/
├── backend/          # Django + DRF + Channels (JWT, chat, appointments)
├── frontend/         # Next.js — auth, chat, appointments UI
└── database/         # PostgreSQL DDL + performance notes
```

## Quick start (backend)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Default: SQLite (USE_SQLITE=True) — no Postgres needed for local testing
python manage.py migrate
python manage.py seed_demo
pip install daphne
daphne -b 0.0.0.0 -p 4000 config.asgi:application
```

API base: `http://localhost:4000/api/`  
Health: `http://localhost:4000/health/`

See [backend/README.md](backend/README.md) for API details and [frontend/README.md](frontend/README.md) for the UI.

## Quick start (frontend)

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

App: `http://localhost:3000`

## Environment

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `DJANGO_SECRET_KEY` | Django signing key |
| `MISTRAL_API_KEY` | Optional — enables LLM slot extraction |
| `CORS_ALLOWED_ORIGINS` | Frontend origin (default `http://localhost:3000`) |

## Deploy to Railway

**Short assessment (SQLite, ~2 days, no Postgres):** [docs/RAILWAY-SQLITE.md](docs/RAILWAY-SQLITE.md)

**Production-style (PostgreSQL):** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

**Short version:**

1. Railway project → **Add PostgreSQL** (database service)
2. Deploy **backend** with root directory `backend`, variable `DATABASE_URL=${{Postgres.DATABASE_URL}}`
3. Deploy **frontend** with root directory `frontend`, set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` to your backend public URL
4. Set backend `CORS_ALLOWED_ORIGINS` to your frontend URL

Free alternatives: **Neon** (Postgres) + **Vercel** (frontend) + **Railway/Render** (backend) — see the deployment doc.
