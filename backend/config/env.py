import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


def parse_database_url(url: str) -> dict:
    # Railway/Heroku often provide postgres:// — Django/psycopg2 need postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    parsed = urlparse(url)
    config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/").split("?")[0],
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or 5432),
    }
    # Managed Postgres (Railway, Neon, Render) usually requires SSL
    if parsed.hostname and parsed.hostname not in ("localhost", "127.0.0.1"):
        config.setdefault("OPTIONS", {})["sslmode"] = "require"
    return config
