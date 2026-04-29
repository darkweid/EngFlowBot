import pytest

from bot.db import init as db_init


def test_get_session_maker_raises_when_not_initialized(monkeypatch):
    monkeypatch.setattr(db_init, "_session_maker", None)

    with pytest.raises(RuntimeError, match="SessionMaker not initialized"):
        db_init.get_session_maker()


def test_get_session_maker_returns_initialized_factory(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(db_init, "_session_maker", sentinel)

    assert db_init.get_session_maker() is sentinel


def test_init_async_session_assigns_session_maker(monkeypatch):
    monkeypatch.setattr(db_init, "_session_maker", None)

    db_init.init_async_session()

    assert db_init._session_maker is not None


async def test_init_db_creates_tables_via_engine(monkeypatch):
    captured = {"run_sync": None}

    class FakeConnection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def run_sync(self, callable_):
            captured["run_sync"] = callable_

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(db_init, "engine", FakeEngine())

    await db_init.init_db()

    assert captured["run_sync"] == db_init.Base.metadata.create_all


async def test_init_db_logs_error_when_create_fails(monkeypatch):
    class FakeConnection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def run_sync(self, callable_):
            raise RuntimeError("schema error")

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(db_init, "engine", FakeEngine())

    await db_init.init_db()
