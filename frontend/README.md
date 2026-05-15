# Frontend (Next.js)

Appointment Assistant UI wired to the Django API.

## Setup

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Ensure the backend runs on port **4000** with CORS enabled.

## Pages

| Route | Description |
|-------|-------------|
| `/` | Redirects to dashboard or login |
| `/login` | JWT login |
| `/signup` | Register |
| `/dashboard` | Chat + booking form + appointments |

## Features

- JWT stored in `localStorage` with refresh on 401
- Real-time chat via WebSocket (`/ws/chat/<session_id>/`)
- REST fallback when WebSocket is unavailable
- Booking form pre-filled from AI-extracted slots when incomplete

## Environment

| Variable | Default |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:4000/api` |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:4000` |
