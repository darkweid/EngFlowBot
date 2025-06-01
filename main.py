import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from config_data.settings import settings
from db import init_db
from handlers import *
from keyboards.set_menu import set_main_menu
from loggers import get_logger
from utils import send_message_to_admin, scheduler, schedule_reminders, init_bot_instance, get_bot_instance

logger = get_logger(__name__)

BOT_TOKEN: str = settings.bot_token
REDIS_DSN: str = settings.redis_dsn
ADMINS: list[int] = settings.admin_ids


async def main():
    try:
        logger.info('Starting bot')

        storage = RedisStorage.from_url(url=REDIS_DSN)
        await init_db()
        await init_bot_instance(token=BOT_TOKEN)
        bot: Bot = await get_bot_instance()
        dp: Dispatcher = Dispatcher(storage=storage)

        dp.include_routers(user_commands_router, admin_router, user_navigation_router, user_stats_router,
                           user_reminder_router, user_testing_router, user_irr_verbs_router, user_new_words_router,
                           fallback_router)

        await set_main_menu(bot)
        await bot.delete_webhook(drop_pending_updates=True)
        await send_message_to_admin(text='🟢 Бот запущен 🟢')
        await on_startup()
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Ошибка: %s", str(e))

    finally:
        logger.info('Бот был остановлен.')
        if bot:
            await send_message_to_admin(text='🟥 Бот остановлен 🟥')
            await bot.session.close()


async def on_startup():
    scheduler.start()
    await schedule_reminders()


if __name__ == "__main__":
    asyncio.run(main())
