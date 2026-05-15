# Django API (Appointment Assistant)

REST + WebSocket backend using **Django 5**, **Django REST Framework**, **JWT**, and **Channels**.

## Stack

| Layer | Choice |
|-------|--------|
| Framework | Django + DRF |
| Auth | JWT (`djangorestframework-simplejwt`) |
| Real-time | Django Channels (WebSockets) |
| DB | PostgreSQL |
| AI | Mistral API (optional key) |
| Rate limiting | DRF throttles + `django-ratelimit` on auth/chat |
| Logging | `RequestLoggingMiddleware` |

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env — set DATABASE_URL, DJANGO_SECRET_KEY, MISTRAL_API_KEY (optional)
python manage.py migrate
python manage.py seed_demo
```

## Run

```powershell
# HTTP + WebSockets (recommended)
pip install daphne
daphne -b 0.0.0.0 -p 4000 config.asgi:application

# HTTP only (dev)
python manage.py runserver 4000
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/signup/` | Register `{email, password, full_name}` |
| POST | `/api/auth/login/` | Login → JWT access + refresh |
| POST | `/api/auth/refresh/` | Refresh access token |
| GET | `/api/auth/me/` | Current user (Bearer token) |
| GET/POST | `/api/appointments/` | List / create appointments |
| GET | `/api/appointments/<uuid>/` | Appointment detail |
| GET/POST | `/api/chat/sessions/` | List / create chat sessions |
| GET | `/api/chat/sessions/<uuid>/` | Session + message history |
| POST | `/api/chat/messages/` | Send message `{content, session_id?, confirm_booking?}` |
| GET | `/health/` | Health check |

### WebSocket

`ws://localhost:4000/ws/chat/<session_id>/?token=<JWT_ACCESS>`

Send JSON: `{"content": "Book me Tuesday 2pm", "confirm_booking": false}`

## Demo credentials

After `seed_demo`: **demo@example.com** / **Password123!**

## Notes

- Schema aligns with `../database/schema.sql` (Django migrations manage tables).
- Without `MISTRAL_API_KEY`, chat uses a rule-based fallback and prompts for the booking form.
- For production, use Redis channel layer and a proper ASGI server behind a reverse proxy.
