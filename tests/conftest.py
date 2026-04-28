"""Shared pytest configuration for EngFlowBot tests.

Keep global fixtures intentionally small. Prefer module-local fixtures until a
helper is useful in at least two test modules.
"""

import os

os.environ.setdefault("BOT_TOKEN", "1234567890:test-token")
os.environ.setdefault("REDIS_DSN", "redis://localhost")
os.environ.setdefault("ADMIN_IDS", "[123456789]")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("LOG_LEVEL_FILE", "WARNING")
os.environ.setdefault("DB_ECHO", "False")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("OWNER_NAME", "Test Owner")
os.environ.setdefault("OWNER_TG_LINK", "https://t.me/test")
os.environ.setdefault("DEVELOPER_TG_ID", "123456789")
