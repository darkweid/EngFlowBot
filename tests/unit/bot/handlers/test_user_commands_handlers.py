from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.handlers.user_commands_handlers import (
    info_command,
    process_start_command,
    process_start_command_existing_user,
    reset_fsm_command,
)
from bot.states import UserFSM
from tests.helpers import FakeMessage, FakeState


async def test_reset_fsm_command_clears_state_and_answers():
    message = FakeMessage()
    state = FakeState({"x": "y"})

    await reset_fsm_command(message, state)

    state.clear.assert_awaited_once_with()
    message.answer.assert_awaited_once_with("Сброшено!")


async def test_process_start_command_registers_new_user_and_updates_state():
    message = FakeMessage(user_id=123, full_name="Test User", username="test_user")
    state = FakeState()
    user_service = SimpleNamespace(add_user=AsyncMock())
    daily_statistics_service = SimpleNamespace(update=AsyncMock())
    keyboard = object()

    with (
        patch(
            "bot.handlers.user_commands_handlers.keyboard_builder",
            new=AsyncMock(return_value=keyboard),
        ),
        patch(
            "bot.handlers.user_commands_handlers.send_message_to_admin", new=AsyncMock()
        ) as notify_admin,
    ):
        await process_start_command(
            message,
            state,
            user_service,
            daily_statistics_service,
        )

    user_service.add_user.assert_awaited_once_with(123, "Test User", "test_user")
    assert message.answer.await_count == 2
    notify_admin.assert_awaited_once()
    state.set_state.assert_awaited_once_with(UserFSM.existing_user)
    daily_statistics_service.update.assert_awaited_once_with("new_user")


async def test_process_start_command_existing_user_refreshes_user_and_shows_menu():
    message = FakeMessage(user_id=123, full_name="Test User", username="test_user")
    state = FakeState()
    user_service = SimpleNamespace(add_user=AsyncMock())

    with patch(
        "bot.handlers.user_commands_handlers.keyboard_builder",
        new=AsyncMock(return_value=object()),
    ):
        await process_start_command_existing_user(message, state, user_service)

    user_service.add_user.assert_awaited_once_with(123, "Test User", "test_user")
    message.answer.assert_awaited_once()
    state.set_state.assert_awaited_once_with(UserFSM.default)


async def test_info_command_sets_default_state_and_answers_with_rules():
    message = FakeMessage()
    state = FakeState()

    with patch(
        "bot.handlers.user_commands_handlers.keyboard_builder",
        new=AsyncMock(return_value=object()),
    ):
        await info_command(message, state)

    state.set_state.assert_awaited_once_with(UserFSM.default)
    message.answer.assert_awaited_once()
