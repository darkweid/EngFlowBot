from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.handlers.user_stats_handlers import see_stats_user, stats_user_command
from bot.lexicon import MessageTexts
from tests.helpers import FakeCallback, FakeMessage


async def test_stats_user_command_sends_user_info_and_period_keyboard():
    message = FakeMessage(user_id=123)
    user_service = SimpleNamespace(get_user_info_text=AsyncMock(return_value="info"))

    with patch(
        "bot.handlers.user_stats_handlers.keyboard_builder",
        new=AsyncMock(return_value=object()),
    ):
        await stats_user_command(message, user_service)

    user_service.get_user_info_text.assert_awaited_once_with(123, admin=False)
    message.answer.assert_awaited_once()
    assert "info" in message.answer.await_args.args[0]
    assert MessageTexts.STATS_USER in message.answer.await_args.args[0]


async def test_see_stats_user_uses_default_interval_for_today():
    callback = FakeCallback(data="stats_today", user_id=123)
    user_progress_service = SimpleNamespace(
        get_activity_by_user=AsyncMock(return_value="today stats")
    )

    with patch(
        "bot.handlers.user_stats_handlers.keyboard_builder",
        new=AsyncMock(return_value=object()),
    ):
        await see_stats_user(callback, user_progress_service)

    callback.answer.assert_awaited_once_with()
    user_progress_service.get_activity_by_user.assert_awaited_once_with(123)
    callback.message.answer.assert_awaited_once()


async def test_see_stats_user_uses_month_interval_for_month_button():
    callback = FakeCallback(data="stats_last_month", user_id=123)
    user_progress_service = SimpleNamespace(
        get_activity_by_user=AsyncMock(return_value="month stats")
    )

    with patch(
        "bot.handlers.user_stats_handlers.keyboard_builder",
        new=AsyncMock(return_value=object()),
    ):
        await see_stats_user(callback, user_progress_service)

    user_progress_service.get_activity_by_user.assert_awaited_once_with(
        123, interval=30
    )


async def test_see_stats_user_uses_week_interval_for_week_button():
    callback = FakeCallback(data="stats_last_week", user_id=123)
    user_progress_service = SimpleNamespace(
        get_activity_by_user=AsyncMock(return_value="week stats")
    )

    with patch(
        "bot.handlers.user_stats_handlers.keyboard_builder",
        new=AsyncMock(return_value=object()),
    ):
        await see_stats_user(callback, user_progress_service)

    user_progress_service.get_activity_by_user.assert_awaited_once_with(123, interval=7)
