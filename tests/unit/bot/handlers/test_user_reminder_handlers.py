from datetime import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.handlers.user_reminder_handlers import (
    reminder_command,
    set_reminder,
    set_reminder_time,
    set_timezone,
    turn_off_reminder,
)
from bot.states import UserFSM
from tests.helpers import FakeCallback, FakeMessage, FakeState


async def test_reminder_command_shows_current_timezone_and_reminder():
    message = FakeMessage(user_id=123)
    user_service = SimpleNamespace(
        get_user=AsyncMock(
            return_value={"time_zone": "+3", "reminder_time": time(9, 30)}
        )
    )

    with patch(
        "bot.handlers.user_reminder_handlers.keyboard_builder",
        new=AsyncMock(return_value=object()),
    ):
        await reminder_command(message, user_service)

    user_service.get_user.assert_awaited_once_with(123)
    message.answer.assert_awaited_once()
    assert "UTC+3" in message.answer.await_args.args[0]
    assert "09:30" in message.answer.await_args.args[0]


async def test_set_timezone_saves_offset_and_reschedules_reminders():
    callback = FakeCallback(data="tz_UTC+3|+3", user_id=123)
    user_service = SimpleNamespace(set_timezone=AsyncMock())

    with (
        patch(
            "bot.handlers.user_reminder_handlers.keyboard_builder",
            new=AsyncMock(return_value=object()),
        ),
        patch(
            "bot.handlers.user_reminder_handlers.schedule_reminders", new=AsyncMock()
        ) as schedule,
    ):
        await set_timezone(callback, user_service)

    callback.answer.assert_awaited_once_with()
    user_service.set_timezone.assert_awaited_once_with(user_id=123, timezone="+3")
    schedule.assert_awaited_once_with()


async def test_set_reminder_prompts_for_time_and_sets_state():
    callback = FakeCallback()
    state = FakeState()

    with patch(
        "bot.handlers.user_reminder_handlers.keyboard_builder",
        new=AsyncMock(return_value=object()),
    ):
        await set_reminder(callback, state)

    callback.answer.assert_awaited_once_with()
    callback.message.answer.assert_awaited_once()
    state.set_state.assert_awaited_once_with(UserFSM.set_reminder_time)


async def test_turn_off_reminder_clears_time_and_reschedules():
    callback = FakeCallback(user_id=123)
    user_service = SimpleNamespace(set_reminder_time=AsyncMock())

    with (
        patch(
            "bot.handlers.user_reminder_handlers.keyboard_builder",
            new=AsyncMock(return_value=object()),
        ),
        patch(
            "bot.handlers.user_reminder_handlers.schedule_reminders", new=AsyncMock()
        ) as schedule,
    ):
        await turn_off_reminder(callback, user_service)

    user_service.set_reminder_time.assert_awaited_once_with(user_id=123, time=None)
    schedule.assert_awaited_once_with()
    callback.message.answer.assert_awaited_once()


async def test_set_reminder_time_accepts_hh_mm_and_reschedules():
    message = FakeMessage(text="09:30", user_id=123)
    user_service = SimpleNamespace(set_reminder_time=AsyncMock())

    with patch(
        "bot.handlers.user_reminder_handlers.schedule_reminders", new=AsyncMock()
    ) as schedule:
        await set_reminder_time(message, user_service)

    user_service.set_reminder_time.assert_awaited_once_with(
        user_id=123,
        time=time(9, 30),
    )
    schedule.assert_awaited_once_with()
    message.delete.assert_awaited_once_with()
    message.answer.assert_awaited_once()


async def test_set_reminder_time_rejects_invalid_time_without_service_call():
    message = FakeMessage(text="bad", user_id=123)
    user_service = SimpleNamespace(set_reminder_time=AsyncMock())

    with patch(
        "bot.handlers.user_reminder_handlers.schedule_reminders", new=AsyncMock()
    ) as schedule:
        await set_reminder_time(message, user_service)

    user_service.set_reminder_time.assert_not_awaited()
    schedule.assert_not_awaited()
    message.delete.assert_awaited_once_with()
    message.answer.assert_awaited_once_with('"bad" не соответствует формату HH:MM')
