import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from bot.middlewares.errors import ErrorHandlingMiddleware


async def test_value_error_is_answered_without_developer_notification():
    middleware = ErrorHandlingMiddleware()
    middleware._safe_answer = AsyncMock()
    event = object()
    handler = AsyncMock(side_effect=ValueError("bad input"))

    with patch(
        "bot.middlewares.errors.send_message_to_developer", new=AsyncMock()
    ) as notify:
        result = await middleware(handler, event=event, data={})

    assert result is None
    middleware._safe_answer.assert_awaited_once_with(
        event,
        "Неправильный формат данных.",
    )
    notify.assert_not_awaited()


async def test_sqlalchemy_error_notifies_developer():
    middleware = ErrorHandlingMiddleware()
    middleware._safe_answer = AsyncMock()
    event = object()
    handler = AsyncMock(side_effect=SQLAlchemyError("db down"))

    with patch(
        "bot.middlewares.errors.send_message_to_developer", new=AsyncMock()
    ) as notify:
        await middleware(handler, event=event, data={})

    middleware._safe_answer.assert_awaited_once_with(
        event,
        "Ошибка базы данных. Попробуйте позже.",
    )
    notify.assert_awaited_once()
    assert "DB error" in notify.await_args.args[0]


async def test_unknown_error_answers_user_and_notifies_developer():
    middleware = ErrorHandlingMiddleware()
    middleware._safe_answer = AsyncMock()
    event = object()
    handler = AsyncMock(side_effect=RuntimeError("boom"))

    with patch(
        "bot.middlewares.errors.send_message_to_developer", new=AsyncMock()
    ) as notify:
        await middleware(handler, event=event, data={})

    middleware._safe_answer.assert_awaited_once_with(
        event,
        "Неизвестная ошибка. Мы уже разбираемся.",
    )
    notify.assert_awaited_once()
    assert "Unhandled error" in notify.await_args.args[0]


async def test_cancelled_error_is_not_swallowed():
    middleware = ErrorHandlingMiddleware()
    handler = AsyncMock(side_effect=asyncio.CancelledError)

    with pytest.raises(asyncio.CancelledError):
        await middleware(handler, event=object(), data={})


async def test_safe_answer_sends_message_answer(monkeypatch):
    class FakeMessage:
        def __init__(self) -> None:
            self.answer = AsyncMock()

    monkeypatch.setattr("bot.middlewares.errors.Message", FakeMessage)
    event = FakeMessage()

    await ErrorHandlingMiddleware()._safe_answer(event, "text")

    event.answer.assert_awaited_once_with("text")


async def test_safe_answer_sends_callback_answer_and_message(monkeypatch):
    class FakeCallbackQuery:
        def __init__(self) -> None:
            self.answer = AsyncMock()
            self.message = SimpleNamespace(answer=AsyncMock())

    monkeypatch.setattr("bot.middlewares.errors.CallbackQuery", FakeCallbackQuery)
    event = FakeCallbackQuery()

    await ErrorHandlingMiddleware()._safe_answer(event, "text")

    event.answer.assert_awaited_once_with()
    event.message.answer.assert_awaited_once_with("text")


def test_user_id_reads_direct_message_user():
    event = SimpleNamespace(from_user=SimpleNamespace(id=123))

    result = ErrorHandlingMiddleware._user_id(event)

    assert result == 123


def test_user_id_reads_callback_message_user():
    event = SimpleNamespace(message=SimpleNamespace(from_user=SimpleNamespace(id=456)))

    result = ErrorHandlingMiddleware._user_id(event)

    assert result == 456
