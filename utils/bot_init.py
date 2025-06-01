from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

bot_instance: Bot | None = None


async def init_bot_instance(token: str) -> None:
    """
    Initialize the bot instance with the given token.

    Parameters:
    - token (str): The bot's token for authentication.
    """
    global bot_instance
    if bot_instance is None:
        bot_instance = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def get_bot_instance() -> Bot:
    """
    Retrieve the initialized bot instance.

    Returns:
    - Bot: The initialized bot instance.

    Raises:
    - Exception: If the bot instance is not initialized.
    """
    if bot_instance is None:
        raise Exception("Bot instance is not initialized")
    return bot_instance
