from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from aiogram.exceptions import TelegramBadRequest

from bot.handlers.user_menu_navigation_handlers import (
    close_message,
    main_menu,
    main_menu_existing_user,
)
from bot.lexicon import MessageTexts
from bot.states import TestingFSM, UserFSM
from tests.helpers import FakeCallback, FakeState


def _bad_request() -> TelegramBadRequest:
    return TelegramBadRequest(method=SimpleNamespace(), message="cant delete")


async def test_close_message_deletes_message():
    callback = FakeCallback()

    await close_message(callback)

    callback.answer.assert_awaited_once()
    callback.message.delete.assert_awaited_once()


async def test_close_message_swallows_telegram_bad_request():
    callback = FakeCallback()
    callback.message.delete = AsyncMock(side_effect=_bad_request())

    await close_message(callback)

    callback.answer.assert_awaited_once()


async def test_main_menu_renders_welcome_and_resets_state():
    callback = FakeCallback()
    state = FakeState()

    with patch(
        "bot.handlers.user_menu_navigation_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    ):
        await main_menu(callback, state)

    callback.message.delete.assert_awaited_once()
    callback.message.answer.assert_awaited_once_with(
        MessageTexts.WELCOME_EXISTING_USER,
        reply_markup="kb",
    )
    state.set_state.assert_awaited_once_with(TestingFSM.default)


async def test_main_menu_swallows_failed_delete_and_still_renders_menu():
    callback = FakeCallback()
    callback.message.delete = AsyncMock(side_effect=_bad_request())
    state = FakeState()

    with patch(
        "bot.handlers.user_menu_navigation_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    ):
        await main_menu(callback, state)

    callback.message.answer.assert_awaited_once()
    state.set_state.assert_awaited_once_with(TestingFSM.default)


async def test_main_menu_existing_user_edits_message_and_resets_user_state():
    callback = FakeCallback()
    state = FakeState()

    with patch(
        "bot.handlers.user_menu_navigation_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    ):
        await main_menu_existing_user(callback, state)

    callback.message.edit_text.assert_awaited_once_with(
        MessageTexts.WELCOME_EXISTING_USER,
        reply_markup="kb",
    )
    state.set_state.assert_awaited_once_with(UserFSM.default)
