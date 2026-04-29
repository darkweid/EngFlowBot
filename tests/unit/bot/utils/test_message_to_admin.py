from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.utils import message_to_admin


async def test_send_message_to_admin_sends_to_all_admins():
    bot = SimpleNamespace(send_message=AsyncMock())

    with (
        patch(
            "bot.utils.message_to_admin.get_bot_instance",
            new=AsyncMock(return_value=bot),
        ),
        patch(
            "bot.utils.message_to_admin.settings",
            SimpleNamespace(admin_ids=[1, 2], developer_tg_id=99),
        ),
    ):
        await message_to_admin.send_message_to_admin("hello")

    bot.send_message.assert_any_await(1, text="hello")
    bot.send_message.assert_any_await(2, text="hello")
    assert bot.send_message.await_count == 2


async def test_send_message_to_admin_can_target_super_admin_only():
    bot = SimpleNamespace(send_message=AsyncMock())

    with (
        patch(
            "bot.utils.message_to_admin.get_bot_instance",
            new=AsyncMock(return_value=bot),
        ),
        patch(
            "bot.utils.message_to_admin.settings",
            SimpleNamespace(admin_ids=[1, 2], developer_tg_id=99),
        ),
    ):
        await message_to_admin.send_message_to_admin("hello", to_super_admin=True)

    bot.send_message.assert_awaited_once_with(1, text="hello")


async def test_send_message_to_developer_uses_configured_developer_id():
    bot = SimpleNamespace(send_message=AsyncMock())

    with (
        patch(
            "bot.utils.message_to_admin.get_bot_instance",
            new=AsyncMock(return_value=bot),
        ),
        patch(
            "bot.utils.message_to_admin.settings",
            SimpleNamespace(admin_ids=[1], developer_tg_id=99),
        ),
    ):
        await message_to_admin.send_message_to_developer("debug")

    bot.send_message.assert_awaited_once_with(99, text="debug")


async def test_send_message_to_admin_logs_error_when_send_fails():
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=RuntimeError("boom")))

    with (
        patch(
            "bot.utils.message_to_admin.get_bot_instance",
            new=AsyncMock(return_value=bot),
        ),
        patch(
            "bot.utils.message_to_admin.settings",
            SimpleNamespace(admin_ids=[1, 2], developer_tg_id=99),
        ),
        patch.object(message_to_admin.logger, "error") as error_log,
    ):
        await message_to_admin.send_message_to_admin("hi")

    bot.send_message.assert_awaited_once_with(1, text="hi")
    error_log.assert_called_once()
    msg = error_log.call_args.args[0]
    assert "admin" in msg
    assert "boom" in msg


async def test_send_message_to_developer_logs_error_when_send_fails():
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=RuntimeError("boom")))

    with (
        patch(
            "bot.utils.message_to_admin.get_bot_instance",
            new=AsyncMock(return_value=bot),
        ),
        patch(
            "bot.utils.message_to_admin.settings",
            SimpleNamespace(admin_ids=[1], developer_tg_id=99),
        ),
        patch.object(message_to_admin.logger, "error") as error_log,
    ):
        await message_to_admin.send_message_to_developer("debug")

    bot.send_message.assert_awaited_once_with(99, text="debug")
    error_log.assert_called_once()
    msg = error_log.call_args.args[0]
    assert "developer" in msg
    assert "boom" in msg
