# Appointment Assistant

Full-stack assessment project: **Next.js** frontend, **Django** REST/WebSocket API, **PostgreSQL** (or SQLite locally), **Mistral** AI.

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
python manage.py migrate
python manage.py seed_demo
daphne -b 0.0.0.0 -p 4000 config.asgi:application
```

API: `http://localhost:4000/api/` · Health: `http://localhost:4000/health/`

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
| `USE_SQLITE` | `True` for local SQLite (default when no `DATABASE_URL`) |
| `DJANGO_SECRET_KEY` | Django signing key |
| `MISTRAL_API_KEY` | Optional — LLM slot extraction in chat |
| `CORS_ALLOWED_ORIGINS` | Frontend origin (default `http://localhost:3000`) |

Demo login after `seed_demo`: `demo@example.com` / `Password123!`
