# Database

## Setup

1. Create database: `createdb appointment_assistant` (or via pgAdmin).
2. Apply schema: `psql -d appointment_assistant -f schema.sql`
3. Seed demo data: `cd ../backend && python manage.py seed_demo`

## Tables

| Table | Purpose |
|-------|---------|
| `businesses` | Optional multi-tenant root (`business_id` on other tables) |
| `users` | Auth + profile |
| `appointments` | Scheduled slots and status |
| `chat_sessions` | Conversation history (`messages` JSONB array) |

## Indexing

See comments at bottom of `schema.sql` — user/tenant lookups, appointment time ranges, GIN on chat messages.

## Performance notes

- Pool connections in the app (`pg.Pool`).
- Normalize `chat_messages` if sessions grow beyond ~100 messages each.
- Partition `appointments` by month at high volume.
