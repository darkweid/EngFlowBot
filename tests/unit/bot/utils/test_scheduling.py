from datetime import datetime, time, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from apscheduler.triggers.date import DateTrigger

from bot.utils import scheduling


async def test_schedule_reminders_removes_old_jobs_and_schedules_configured_users():
    user_service = SimpleNamespace(
        get_all_users=AsyncMock(
            return_value=[
                {
                    "user_id": 123,
                    "tg_login": "one",
                    "reminder_time": time(9, 30),
                    "time_zone": "3",
                },
                {
                    "user_id": 456,
                    "tg_login": "two",
                    "reminder_time": None,
                    "time_zone": "3",
                },
            ]
        )
    )
    scheduler_mock = MagicMock()

    with (
        patch("bot.utils.scheduling.UserService", return_value=user_service),
        patch("bot.utils.scheduling.scheduler", scheduler_mock),
    ):
        await scheduling.schedule_reminders()

    scheduler_mock.remove_all_jobs.assert_called_once_with(jobstore="reminders")
    scheduler_mock.add_job.assert_called_once()
    kwargs = scheduler_mock.add_job.call_args.kwargs
    assert kwargs["func"] is scheduling.send_reminder_to_user
    assert kwargs["trigger"] == "cron"
    assert kwargs["hour"] == 9
    assert kwargs["minute"] == 30
    assert kwargs["timezone"] == timezone(timedelta(hours=3))
    assert kwargs["kwargs"] == {"user_id": 123}
    assert kwargs["jobstore"] == "reminders"
    assert kwargs["name"] == "Reminder for @one (123)"


async def test_schedule_broadcast_adds_date_trigger_in_utc_plus_three():
    scheduler_mock = MagicMock()

    with patch("bot.utils.scheduling.scheduler", scheduler_mock):
        await scheduling.schedule_broadcast(
            date_time=datetime(2026, 4, 28, 18, 15),
            text="Hello",
        )

    scheduler_mock.add_job.assert_called_once()
    kwargs = scheduler_mock.add_job.call_args.kwargs
    assert kwargs["func"] is scheduling.send_message_to_all_users
    assert isinstance(kwargs["trigger"], DateTrigger)
    assert kwargs["kwargs"] == {"text": "Hello"}
    assert kwargs["jobstore"] == "broadcasts"
    assert kwargs["name"] == "Broadcast 18:15 (UTC+3) 28.04.2026"


async def test_delete_scheduled_broadcasts_removes_broadcast_jobs():
    scheduler_mock = MagicMock()

    with patch("bot.utils.scheduling.scheduler", scheduler_mock):
        await scheduling.delete_scheduled_broadcasts()

    scheduler_mock.remove_all_jobs.assert_called_once_with(jobstore="broadcasts")
