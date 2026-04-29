from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.utils.send_long_message import send_long_message


def make_callback():
    return SimpleNamespace(message=SimpleNamespace(answer=AsyncMock()))


async def test_send_long_message_sends_short_text_once():
    callback = make_callback()

    await send_long_message(
        callback,
        "short text",
        parse_mode="HTML",
    )

    callback.message.answer.assert_awaited_once_with(
        "short text\n",
        parse_mode="HTML",
    )


async def test_send_long_message_splits_text_by_delimiter():
    callback = make_callback()

    await send_long_message(callback, "one\ntwo\nthree", max_length=8)

    assert callback.message.answer.await_count == 2
    callback.message.answer.assert_any_await("one\ntwo\n")
    callback.message.answer.assert_any_await("three\n")
