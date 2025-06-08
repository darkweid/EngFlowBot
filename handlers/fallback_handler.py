from aiogram import Router
from aiogram.types import Message

from lexicon import MessageTexts

fallback_router: Router = Router()


@fallback_router.message()
async def send_fallback_message(message: Message):
    await message.reply(
        f'Hey, {message.from_user.first_name}\n{MessageTexts.ERROR}')
