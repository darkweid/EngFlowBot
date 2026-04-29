import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
import pytest
from sqlalchemy.exc import SQLAlchemyError

from bot.middlewares.errors import ErrorHandlingMiddleware


def _method() -> SimpleNamespace:
    return SimpleNamespace()


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


def test_user_id_returns_none_when_event_has_no_from_user():
    event = object()

    assert ErrorHandlingMiddleware._user_id(event) is None


async def test_telegram_forbidden_is_logged_and_silenced():
    middleware = ErrorHandlingMiddleware()
    middleware._safe_answer = AsyncMock()
    event = SimpleNamespace(from_user=SimpleNamespace(id=123))
    handler = AsyncMock(
        side_effect=TelegramForbiddenError(method=_method(), message="blocked")
    )

    with (
        patch(
            "bot.middlewares.errors.send_message_to_developer", new=AsyncMock()
        ) as notify,
        patch.object(
            __import__("bot.middlewares.errors").middlewares.errors.logger, "warning"
        ) as warn_log,
    ):
        await middleware(handler, event=event, data={})

    middleware._safe_answer.assert_not_awaited()
    notify.assert_not_awaited()
    warn_log.assert_called_once()


async def test_telegram_retry_after_sleeps_for_retry_window():
    middleware = ErrorHandlingMiddleware()
    middleware._safe_answer = AsyncMock()
    handler = AsyncMock(
        side_effect=TelegramRetryAfter(method=_method(), message="slow", retry_after=5)
    )

    with patch("bot.middlewares.errors.asyncio.sleep", new=AsyncMock()) as sleep_mock:
        await middleware(handler, event=object(), data={})

    sleep_mock.assert_awaited_once_with(5)
    middleware._safe_answer.assert_not_awaited()


async def test_telegram_bad_request_answers_user_with_friendly_message():
    middleware = ErrorHandlingMiddleware()
    middleware._safe_answer = AsyncMock()
    handler = AsyncMock(
        side_effect=TelegramBadRequest(method=_method(), message="cant edit")
    )

    with patch(
        "bot.middlewares.errors.send_message_to_developer", new=AsyncMock()
    ) as notify:
        await middleware(handler, event=object(), data={})

    middleware._safe_answer.assert_awaited_once_with(
        middleware._safe_answer.await_args.args[0],
        "Невозможно выполнить действие.",
    )
    notify.assert_not_awaited()


async def test_telegram_api_error_fallback_answers_user():
    middleware = ErrorHandlingMiddleware()
    middleware._safe_answer = AsyncMock()
    handler = AsyncMock(
        side_effect=TelegramAPIError(method=_method(), message="api boom")
    )

    with patch(
        "bot.middlewares.errors.send_message_to_developer", new=AsyncMock()
    ) as notify:
        await middleware(handler, event=object(), data={})

    middleware._safe_answer.assert_awaited_once_with(
        middleware._safe_answer.await_args.args[0],
        "Ошибка Telegram. Попробуйте позже.",
    )
    notify.assert_not_awaited()


async def test_safe_answer_swallows_telegram_api_error(monkeypatch):
    class FakeMessage:
        def __init__(self) -> None:
            self.answer = AsyncMock(
                side_effect=TelegramAPIError(method=_method(), message="boom")
            )

    monkeypatch.setattr("bot.middlewares.errors.Message", FakeMessage)
    event = FakeMessage()

    await ErrorHandlingMiddleware()._safe_answer(event, "text")

    event.answer.assert_awaited_once_with("text")
