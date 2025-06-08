from __future__ import annotations

import asyncio
from typing import Any

from aiogram import BaseMiddleware
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramForbiddenError,  # user blocked the bot
    TelegramBadRequest,  # chat not found, message can't be edited etc.
    TelegramRetryAfter,  # rate-limit
)
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import SQLAlchemyError

from loggers import get_logger
from utils.message_to_admin import send_message_to_developer

logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Catch common exceptions from handlers and convert them to
    user-friendly messages or silent logging.
    """

    async def __call__(
            self,
            handler: Any,
            event: Any,
            data: dict[str, Any],
    ):
        try:
            return await handler(event, data)

        # ────────────── BUSINESS / VALIDATION ────────────── #
        except ValueError as exc:
            await self._safe_answer(event, "Неправильный формат данных.")
            logger.info("Validation error: %s", exc)

        # ────────────── DATABASE ────────────── #
        except SQLAlchemyError as exc:
            await self._safe_answer(event, "Ошибка базы данных. Попробуйте позже.")
            logger.exception("DB error")
            await send_message_to_developer(f"DB error\n{exc}")

        # ────────────── TELEGRAM API ────────────── #
        except TelegramForbiddenError:
            logger.warning("Bot blocked by user %s", self._user_id(event))

        except TelegramRetryAfter as exc:
            logger.warning("Rate-limit: sleeping %s s", exc.retry_after)
            await asyncio.sleep(exc.retry_after)

        except TelegramBadRequest as exc:
            await self._safe_answer(event, "Невозможно выполнить действие.")
            logger.warning("Bad request: %s", exc.message)

        # other Telegram errors
        except TelegramAPIError as exc:
            await self._safe_answer(event, "Ошибка Telegram. Попробуйте позже.")
            logger.error("Telegram API error: %s", exc.message)

        # ────────────── UNKNOWN ────────────── #
        except asyncio.CancelledError:
            raise

        except Exception as exc:  # noqa: BLE001
            await self._safe_answer(event, "Неизвестная ошибка. Мы уже разбираемся.")
            logger.exception("Unhandled error")
            await send_message_to_developer(f"Unhandled error\n{exc}")

    # ────────────────── helpers ────────────────── #
    async def _safe_answer(self, event: Any, text: str) -> None:
        """
        Try to send answer, ignore failures (user may have blocked the bot).
        Works for Message & CallbackQuery.
        """
        try:
            if isinstance(event, CallbackQuery):
                await event.answer()
                await event.message.answer(text)
            elif isinstance(event, Message):
                await event.answer(text)
        except TelegramAPIError:
            pass

    @staticmethod
    def _user_id(event: Any) -> int | None:
        if hasattr(event, "from_user"):
            return event.from_user.id
        if hasattr(event, "message") and event.message.from_user:
            return event.message.from_user.id
        return None
