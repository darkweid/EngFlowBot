from aiogram import Bot
from aiogram.types import BotCommand


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        # BotCommand(command='/reset_fsm', description='Cброс машины состояний'),
        BotCommand(command="/start", description="Перезапустить бота"),
        BotCommand(command="/main_menu", description="Главное меню"),
        # BotCommand(command='/stats', description='Посмотреть мою статистику'),
        BotCommand(command="/reminder", description="Установить напоминания"),
        BotCommand(command="/info", description="Как пользоваться ботом"),
        BotCommand(command="/admin", description="Административная панель"),
    ]
    await bot.set_my_commands(main_menu_commands)
