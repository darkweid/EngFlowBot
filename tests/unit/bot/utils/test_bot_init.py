import pytest

from bot.utils import bot_init


async def test_get_bot_instance_raises_when_not_initialized(monkeypatch):
    monkeypatch.setattr(bot_init, "bot_instance", None)

    with pytest.raises(Exception, match="Bot instance is not initialized"):
        await bot_init.get_bot_instance()


async def test_get_bot_instance_returns_existing_bot(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(bot_init, "bot_instance", sentinel)

    result = await bot_init.get_bot_instance()

    assert result is sentinel


async def test_init_bot_instance_skips_when_already_initialized(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(bot_init, "bot_instance", sentinel)

    await bot_init.init_bot_instance("token")

    assert bot_init.bot_instance is sentinel


async def test_init_bot_instance_creates_bot_when_uninitialized(monkeypatch):
    monkeypatch.setattr(bot_init, "bot_instance", None)
    fake_bot = object()
    captured = {}

    def fake_bot_factory(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return fake_bot

    monkeypatch.setattr(bot_init, "Bot", fake_bot_factory)

    await bot_init.init_bot_instance("1234567:abcdef")

    assert bot_init.bot_instance is fake_bot
    assert captured["kwargs"]["token"] == "1234567:abcdef"
