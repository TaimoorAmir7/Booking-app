# Deployment guide (Railway + PostgreSQL)

This project runs as **three Railway resources** (recommended):

1. **PostgreSQL** — managed database (free trial / pay-as-you-go)
2. **Backend** — Django API + WebSockets (`backend/`)
3. **Frontend** — Next.js (`frontend/`)

You do **not** install Postgres on the same VM as Django. Railway hosts Postgres for you and injects `DATABASE_URL` into the backend service.

---

## Option A: Railway (recommended)

[Railway](https://railway.com) gives you Postgres + app hosting in one project. New accounts usually get trial credits; after that you pay for usage (often a few dollars/month for a small app).

### 1. Push code to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USER/appointment-assistant.git
git push -u origin main
```

### 2. Create a Railway project

1. Go to [railway.com](https://railway.com) → **New Project**
2. **Deploy from GitHub repo** → select your repository

### 3. Add PostgreSQL

1. In the project canvas, click **+ New** → **Database** → **PostgreSQL**
2. Railway creates a Postgres instance and exposes variables like `DATABASE_URL`

You never run `CREATE DATABASE` manually — Railway provisions it.

### 4. Deploy the backend (Django)

1. **+ New** → **GitHub Repo** → same repo (second service)
2. Open the service → **Settings**:
   - **Root Directory**: `backend`
   - **Watch Paths**: `backend/**` (optional)
3. **Variables** → add or reference:

| Variable | Value |
|----------|--------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (use *Variable Reference* from your Postgres service) |
| `DJANGO_SECRET_KEY` | long random string (e.g. `openssl rand -hex 32`) |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `${{RAILWAY_PUBLIC_DOMAIN}}` (or leave empty if using default + `RAILWAY_PUBLIC_DOMAIN`) |
| `CORS_ALLOWED_ORIGINS` | `https://YOUR-FRONTEND.up.railway.app` (set after frontend deploy) |
| `MISTRAL_API_KEY` | your Mistral key (optional) |
| `MISTRAL_MODEL` | `mistral-small-latest` |

4. **Networking** → **Generate Domain** (e.g. `https://backend-xxxx.up.railway.app`)
5. Deploy. The start command runs migrations then Daphne:

   `python manage.py migrate --noinput && daphne -b 0.0.0.0 -p $PORT config.asgi:application`

6. Verify: open `https://YOUR-BACKEND.up.railway.app/health/` → `{"status":"ok"}`

7. (Optional) Seed demo user — **Settings** → run one-off command or use Railway shell:

   ```bash
   python manage.py seed_demo
   ```

### 5. Deploy the frontend (Next.js)

1. **+ New** → **GitHub Repo** → same repo (third service)
2. **Settings**:
   - **Root Directory**: `frontend`
3. **Variables** (required at **build** time for Next.js):

| Variable | Example |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | `https://backend-xxxx.up.railway.app/api` |
| `NEXT_PUBLIC_WS_URL` | `wss://backend-xxxx.up.railway.app` |

Use `wss://` (not `ws://`) in production.

4. **Generate Domain** for the frontend
5. Redeploy **backend** and set:

   `CORS_ALLOWED_ORIGINS=https://frontend-xxxx.up.railway.app`

### 6. Architecture diagram

```
Browser
   │
   ├─ HTTPS ─► Frontend (Next.js)     NEXT_PUBLIC_API_URL / WS_URL
   │
   └─ HTTPS ─► Backend (Django/Daphne) ──► PostgreSQL (Railway plugin)
                    JWT, REST, WebSockets
```

---

## Option B: Free / low-cost split (Postgres elsewhere)

If you want **cheaper Postgres** and **free frontend**:

| Piece | Service | Notes |
|-------|---------|--------|
| PostgreSQL | [Neon](https://neon.tech) free tier | Copy connection string → `DATABASE_URL` on backend |
| Backend | Railway or [Render](https://render.com) | Render free web tier sleeps after inactivity |
| Frontend | [Vercel](https://vercel.com) free | Root: `frontend`, env vars for API/WS URLs |

**Neon setup (example):**

1. Create project → copy **connection string** (pooled recommended)
2. Paste into backend `DATABASE_URL`
3. Our `parse_database_url` already sets `sslmode=require` for remote hosts

---

## Environment checklist

### Backend (production)

```env
DATABASE_URL=postgresql://...          # from Railway Postgres or Neon
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=False
CORS_ALLOWED_ORIGINS=https://your-frontend.example.com
MISTRAL_API_KEY=...                    # optional
```

### Frontend (production)

```env
NEXT_PUBLIC_API_URL=https://your-backend.example.com/api
NEXT_PUBLIC_WS_URL=wss://your-backend.example.com
```

---

## WebSockets on Railway

- Use **Daphne** (ASGI) — already configured in `railway.toml`
- Public URL must use **`wss://`** in `NEXT_PUBLIC_WS_URL`
- Chat uses in-memory channel layer (fine for **one** backend instance). For multiple replicas, add Redis + `channels_redis` later.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `DisallowedHost` | Add domain to `DJANGO_ALLOWED_HOSTS` or set `RAILWAY_PUBLIC_DOMAIN` |
| CORS errors | Set `CORS_ALLOWED_ORIGINS` to exact frontend URL (no trailing slash) |
| DB connection failed | Reference `${{Postgres.DATABASE_URL}}`; redeploy after linking Postgres |
| `postgres://` errors | Handled in `config/env.py` (auto-converts to `postgresql://`) |
| Chat works locally, not prod | Use `wss://` and same backend domain as API |
| Next.js still calls localhost | Redeploy frontend after setting `NEXT_PUBLIC_*` vars |

---

## Cost expectations (rough)

- **Railway**: Postgres + 2 services — trial credit first, then ~$5–20/mo depending on usage
- **Neon + Vercel + Railway backend**: often **$0–5/mo** for demos with free tiers
- **Render free**: backend sleeps; cold starts ~30s

For an assessment/demo, **Railway all-in-one** is the fastest path.
