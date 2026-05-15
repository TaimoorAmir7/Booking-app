# Railway deploy (SQLite, short assessment)

For a **2-day demo** with few users — **no PostgreSQL service required**.

## Important caveats

| Topic | What to know |
|-------|----------------|
| **No Postgres** | Set `USE_SQLITE=True` and **do not** add Railway Postgres (its `DATABASE_URL` would switch you to Postgres). |
| **Redeploy without volume** | `db.sqlite3` on the container disk can be **wiped** → users/appointments gone. |
| **Volume (recommended)** | Mount Railway volume at `/data`, set `SQLITE_PATH=/data/db.sqlite3` → data survives redeploys for your 2 days. |
| **After 2 days** | Delete the Railway project to stop charges. |

---

## Services (2 only — no database plugin)

1. **Backend** (root: `backend`)
2. **Frontend** (root: `frontend`)

---

## 1. Push to GitHub

Same repo with `backend/` and `frontend/`.

---

## 2. Backend on Railway

1. New Project → Deploy from GitHub.
2. Add service → same repo → **Root Directory**: `backend`.
3. **Variables**:

| Variable | Value |
|----------|--------|
| `USE_SQLITE` | `True` |
| `SQLITE_PATH` | `/data/db.sqlite3` (if using volume; else omit) |
| `DJANGO_SECRET_KEY` | long random string |
| `DJANGO_DEBUG` | `False` |
| `MISTRAL_API_KEY` | your key |
| `CORS_ALLOWED_ORIGINS` | `https://YOUR-FRONTEND.up.railway.app` (after frontend deploy) |

**Do not set** `DATABASE_URL`.

4. **Volume (recommended for 2 days)**  
   - Backend service → **Volumes** → Add volume  
   - Mount path: `/data`  
   - Keeps SQLite file across redeploys  

5. **Networking** → Generate domain → e.g. `https://backend-xxx.up.railway.app`

6. Deploy. Check: `https://backend-xxx.up.railway.app/health/`

7. **Seed demo user** (Railway shell on backend service once):

   ```bash
   python manage.py seed_demo
   ```

   Login: `demo@example.com` / `Password123!`

---

## 3. Frontend on Railway

1. **+ New** → same repo → **Root Directory**: `frontend`
2. **Variables** (set before/at build):

| Variable | Value |
|----------|--------|
| `NEXT_PUBLIC_API_URL` | `https://backend-xxx.up.railway.app/api` |
| `NEXT_PUBLIC_WS_URL` | `wss://backend-xxx.up.railway.app` |

3. Generate domain → redeploy **backend** with `CORS_ALLOWED_ORIGINS` = frontend URL.

---

## 4. Tear down after assessment

Railway project → **Settings** → Delete project (stops billing).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Still using Postgres | Remove `DATABASE_URL` from backend variables; set `USE_SQLITE=True` |
| Empty DB after deploy | Add volume at `/data` + `SQLITE_PATH=/data/db.sqlite3`, run `seed_demo` again |
| CORS errors | Exact frontend URL in `CORS_ALLOWED_ORIGINS`, no trailing slash |
| Chat WebSocket | Use `wss://` in `NEXT_PUBLIC_WS_URL` |
