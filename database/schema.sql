-- =============================================================================
-- Appointment Assistant — PostgreSQL schema
-- =============================================================================
-- Tables: businesses (optional SaaS), users, appointments, chat_sessions
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

-- -----------------------------------------------------------------------------
-- businesses — optional multi-tenancy root
-- -----------------------------------------------------------------------------
CREATE TABLE businesses (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE businesses IS 'Optional tenant root; link users/appointments/sessions via business_id.';

-- -----------------------------------------------------------------------------
-- users — authentication + profile
-- -----------------------------------------------------------------------------
CREATE TABLE users (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id     UUID NULL REFERENCES businesses (id) ON DELETE SET NULL,
  email           CITEXT NOT NULL,
  password_hash   TEXT NOT NULL,
  full_name       TEXT NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One email per tenant; global uniqueness when not in a business
CREATE UNIQUE INDEX users_email_per_business_unique
  ON users (email, COALESCE(business_id, '00000000-0000-0000-0000-000000000000'::uuid));

COMMENT ON TABLE users IS 'Auth + profile. business_id NULL = default tenant.';
COMMENT ON COLUMN users.business_id IS 'Scopes rows for multi-tenant SaaS.';

-- -----------------------------------------------------------------------------
-- appointments — scheduling + status
-- -----------------------------------------------------------------------------
CREATE TYPE appointment_status AS ENUM ('pending', 'scheduled', 'cancelled', 'completed');

CREATE TABLE appointments (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  business_id     UUID NULL REFERENCES businesses (id) ON DELETE SET NULL,
  title           TEXT NOT NULL,
  starts_at       TIMESTAMPTZ NOT NULL,
  ends_at         TIMESTAMPTZ NOT NULL,
  status          appointment_status NOT NULL DEFAULT 'scheduled',
  notes           TEXT,
  source          TEXT DEFAULT 'form',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT appointments_time_range CHECK (ends_at > starts_at)
);

COMMENT ON TABLE appointments IS 'Booked slots; source = form | chat_ai.';
COMMENT ON COLUMN appointments.source IS 'How the booking was created (audit / product analytics).';

-- -----------------------------------------------------------------------------
-- chat_sessions — conversation history + metadata (messages in JSONB)
-- -----------------------------------------------------------------------------
CREATE TABLE chat_sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  business_id     UUID NULL REFERENCES businesses (id) ON DELETE SET NULL,
  title           TEXT,
  messages        JSONB NOT NULL DEFAULT '[]'::jsonb,
  metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
  last_message_at TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chat_sessions_messages_is_array CHECK (jsonb_typeof(messages) = 'array')
);

COMMENT ON TABLE chat_sessions IS 'Multi-turn chat; messages = [{role, content, ts}, ...].';
COMMENT ON COLUMN chat_sessions.metadata IS 'e.g. extracted_slots, model, last_error for debugging.';

-- =============================================================================
-- Indexing strategy
-- =============================================================================
-- users: login by email within tenant
CREATE INDEX idx_users_business_email ON users (business_id, email);

-- appointments: list by user + time window queries (calendar)
CREATE INDEX idx_appointments_user_starts ON appointments (user_id, starts_at DESC);
CREATE INDEX idx_appointments_business_starts ON appointments (business_id, starts_at DESC)
  WHERE business_id IS NOT NULL;
CREATE INDEX idx_appointments_status ON appointments (status) WHERE status IN ('pending', 'scheduled');

-- chat_sessions: recent sessions per user
CREATE INDEX idx_chat_sessions_user_updated ON chat_sessions (user_id, updated_at DESC);
CREATE INDEX idx_chat_sessions_messages_gin ON chat_sessions USING gin (messages jsonb_path_ops);

-- =============================================================================
-- updated_at trigger (reuse pattern)
-- =============================================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

CREATE TRIGGER trg_appointments_updated_at
  BEFORE UPDATE ON appointments FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

CREATE TRIGGER trg_chat_sessions_updated_at
  BEFORE UPDATE ON chat_sessions FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

-- =============================================================================
-- Sample data (optional — prefer `python manage.py seed_demo` in backend)
-- =============================================================================

INSERT INTO businesses (id, name) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Acme Dental Demo Org')
  ON CONFLICT (id) DO NOTHING;

-- Users with real bcrypt hashes: run backend `npm run db:seed` after migrations.
-- Example appointment row (requires user id from seed):
-- INSERT INTO appointments (user_id, title, starts_at, ends_at, notes, source)
-- VALUES ('<user_uuid>', 'Consultation', '2026-05-20 10:00:00+00', '2026-05-20 10:30:00+00', 'First visit', 'form');

-- =============================================================================
-- Performance & scalability notes
-- =============================================================================
-- 1. Partition appointments by starts_at (monthly) when row count exceeds ~5–10M.
-- 2. Move chat message arrays to chat_messages normalized table if history grows large;
--    keep JSONB for MVP/simple memory as required.
-- 3. BRIN index on appointments(starts_at) for append-only time-series if mostly sequential inserts.
-- 4. Connection pooling (PgBouncer) in front of app servers at scale.
-- 5. business_id partial indexes keep single-tenant queries cheap when NULL is common.
