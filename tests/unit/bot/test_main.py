from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from bot import main


class DummyDispatcher:
    def __init__(self, *, storage):
        self.storage = storage
        self.update = SimpleNamespace(
            middleware=SimpleNamespace(register=MagicMock()),
        )
        self.include_routers = MagicMock()


async def test_startup_logs_reminder_scheduling_error_and_continues():
    bot = SimpleNamespace(delete_webhook=AsyncMock())
    scheduler = SimpleNamespace(start=MagicMock())

    with (
        patch("bot.main.init_async_session") as init_async_session,
        patch("bot.main.RedisStorage.from_url", return_value=object()),
        patch("bot.main.init_bot_instance", new=AsyncMock()),
        patch("bot.main.get_bot_instance", new=AsyncMock(return_value=bot)),
        patch("bot.main.Dispatcher", new=DummyDispatcher),
        patch("bot.main.ServicesMiddleware", return_value=object()),
        patch("bot.main.ErrorHandlingMiddleware", return_value=object()),
        patch("bot.main.set_main_menu", new=AsyncMock()),
        patch("bot.main.scheduler", new=scheduler),
        patch(
            "bot.main.schedule_reminders",
            new=AsyncMock(side_effect=RuntimeError("users table missing")),
        ),
        patch("bot.main.send_message_to_admin", new=AsyncMock()),
        patch("bot.main.logger") as logger,
    ):
        startup_bot, dispatcher = await main.startup()

    assert startup_bot is bot
    assert isinstance(dispatcher, DummyDispatcher)
    init_async_session.assert_called_once()
    scheduler.start.assert_called_once()
    logger.exception.assert_called_once_with(
        "Failed to schedule reminders during startup"
    )
