"""Entry-point for Telegram bot.

Creates DB session, starts Aiogram dispatcher and background jobs.
"""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from config_data.settings import settings
from db.init import init_async_session
from handlers import (
    user_commands_router,
    admin_router,
    user_navigation_router,
    user_stats_router,
    user_reminder_router,
    user_testing_router,
    user_irr_verbs_router,
    user_new_words_router,
    fallback_router,
)
from keyboards.set_menu import set_main_menu
from lexicon.lexicon_ru import ServiceMessages
from loggers import get_logger
from middlewares.errors import ErrorHandlingMiddleware
from middlewares.services import ServicesMiddleware
from utils import (
    send_message_to_admin,
    scheduler,
    schedule_reminders, get_bot_instance, init_bot_instance,
)

logger = get_logger(__name__)


async def startup() -> tuple[Bot, Dispatcher]:
    init_async_session()

    storage = RedisStorage.from_url(settings.redis_dsn)
    await init_bot_instance(token=settings.bot_token)
    bot: Bot = await get_bot_instance()
    dp = Dispatcher(storage=storage)

    dp.update.middleware.register(ServicesMiddleware())
    dp.update.middleware.register(ErrorHandlingMiddleware())
    dp.include_routers(
        user_commands_router,
        admin_router,
        user_navigation_router,
        user_stats_router,
        user_reminder_router,
        user_testing_router,
        user_irr_verbs_router,
        user_new_words_router,
        fallback_router,
    )

    await set_main_menu(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    scheduler.start()
    await schedule_reminders()
    await send_message_to_admin(ServiceMessages.BOT_ON)

    logger.info("Bot started")
    return bot, dp


async def shutdown(bot: Bot) -> None:
    logger.info("Shutting down...")
    await send_message_to_admin(ServiceMessages.BOT_OFF)
    scheduler.shutdown(wait=False)
    await bot.session.close()
    logger.info("Bot stopped")


async def main() -> None:
    bot: Bot | None = None
    try:
        bot, dp = await startup()

        await dp.start_polling(bot, handle_signals=True)
    except asyncio.CancelledError:
        logger.info("Polling cancelled")
    except Exception as e:
        logger.error(f"Unhandled exception:\n{e}")
    finally:
        if bot:
            await shutdown(bot)


if __name__ == "__main__":
    asyncio.run(main())
