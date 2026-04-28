from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.lexicon import MessageTexts
from bot.utils import message_to_users


async def test_send_message_to_all_users_sends_text_to_each_user():
    bot = SimpleNamespace(send_message=AsyncMock())
    user_service = SimpleNamespace(
        get_all_users=AsyncMock(
            return_value=[
                {"user_id": 123},
                {"user_id": 456},
            ]
        )
    )

    with (
        patch(
            "bot.utils.message_to_users.get_bot_instance",
            new=AsyncMock(return_value=bot),
        ),
        patch("bot.utils.message_to_users.UserService", return_value=user_service),
    ):
        await message_to_users.send_message_to_all_users("hello")

    bot.send_message.assert_any_await(123, text="hello")
    bot.send_message.assert_any_await(456, text="hello")
    assert bot.send_message.await_count == 2


async def test_send_message_to_user_without_learning_button_sends_plain_text():
    bot = SimpleNamespace(send_message=AsyncMock())

    with patch(
        "bot.utils.message_to_users.get_bot_instance",
        new=AsyncMock(return_value=bot),
    ):
        await message_to_users.send_message_to_user(123, "hello")

    bot.send_message.assert_awaited_once_with(123, text="hello")


async def test_send_message_to_user_with_learning_button_uses_keyboard():
    bot = SimpleNamespace(send_message=AsyncMock())
    keyboard = object()

    with (
        patch(
            "bot.utils.message_to_users.get_bot_instance",
            new=AsyncMock(return_value=bot),
        ),
        patch(
            "bot.utils.message_to_users.keyboard_builder",
            new=AsyncMock(return_value=keyboard),
        ) as keyboard_builder,
    ):
        await message_to_users.send_message_to_user(
            123,
            "hello",
            learning_button=True,
        )

    keyboard_builder.assert_awaited_once()
    bot.send_message.assert_awaited_once_with(
        123,
        text="hello",
        reply_markup=keyboard,
    )


async def test_send_reminder_to_user_skips_message_when_no_words_due():
    bot = SimpleNamespace(send_message=AsyncMock())
    learning_service = SimpleNamespace(
        get_count_all_exercises_for_today_by_user=AsyncMock(return_value=0)
    )

    with (
        patch(
            "bot.utils.message_to_users.get_bot_instance",
            new=AsyncMock(return_value=bot),
        ),
        patch(
            "bot.utils.message_to_users.UserWordsLearningService",
            return_value=learning_service,
        ),
    ):
        await message_to_users.send_reminder_to_user(123)

    bot.send_message.assert_not_awaited()


async def test_send_reminder_to_user_sends_due_words_message_with_keyboard():
    bot = SimpleNamespace(send_message=AsyncMock())
    keyboard = object()
    learning_service = SimpleNamespace(
        get_count_all_exercises_for_today_by_user=AsyncMock(return_value=3)
    )

    with (
        patch(
            "bot.utils.message_to_users.get_bot_instance",
            new=AsyncMock(return_value=bot),
        ),
        patch(
            "bot.utils.message_to_users.UserWordsLearningService",
            return_value=learning_service,
        ),
        patch(
            "bot.utils.message_to_users.keyboard_builder",
            new=AsyncMock(return_value=keyboard),
        ),
    ):
        await message_to_users.send_reminder_to_user(123)

    bot.send_message.assert_awaited_once_with(
        123,
        text=MessageTexts.REMINDER_WORDS_TO_LEARN.format("3 слова"),
        reply_markup=keyboard,
    )
