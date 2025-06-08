from aiogram import Bot

from config_data.settings import settings
from loggers import get_logger
from .bot_init import get_bot_instance

logger = get_logger(__name__)


async def send_message_to_admin(text: str, to_super_admin=False):
    """
    Send a message to the admin(s) of the bot.

    Parameters:
    - text (str): The message text to send.
    - to_super_admin (bool, optional): If True, send only to the super admin (first in the list). Defaults to False.

    """
    admins: list[int] = settings.admin_ids

    bot: Bot = await get_bot_instance()

    if to_super_admin:
        await bot.send_message(admins[0], text=text)
    else:
        try:
            for admin in admins:
                await bot.send_message(admin, text=text)
        except Exception as e:
            logger.error(f'Unsuccessful attempt to send message to admin{admin}: {e}')


async def send_message_to_developer(text: str):
    """
    Send a message to the developer of the bot.

    Parameters:
    - text (str): The message text to send.
    """

    bot: Bot = await get_bot_instance()

    try:
        await bot.send_message(settings.developer_tg_id, text=text)
    except Exception as e:
        logger.error(f'Unsuccessful attempt to send message to developer: {e}')
