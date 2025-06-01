import logging

from aiogram import Bot

from config_data.settings import settings
from .bot_init import get_bot_instance

logger = logging.getLogger(__name__)

ADMINS: list = settings.admin_ids


async def send_message_to_admin(text: str, to_super_admin=False):
    """
    Send a message to the admin(s) of the bot.

    Parameters:
    - text (str): The message text to send.
    - to_super_admin (bool, optional): If True, send only to the super admin (first in the list). Defaults to False.

    """
    bot: Bot = await get_bot_instance()

    if to_super_admin:
        await bot.send_message(ADMINS[0], text=text)
    else:
        try:
            for admin in ADMINS:
                await bot.send_message(admin, text=text)
        except Exception as e:
            logger.error(f'Unsuccessful attempt to send message to admin{admin}: {e}')
