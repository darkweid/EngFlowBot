from unittest.mock import AsyncMock

from bot.keyboards.set_menu import set_main_menu


async def test_set_main_menu_registers_expected_bot_commands():
    bot = AsyncMock()

    await set_main_menu(bot)

    bot.set_my_commands.assert_awaited_once()
    commands = bot.set_my_commands.await_args.args[0]
    assert [command.command for command in commands] == [
        "/start",
        "/main_menu",
        "/reminder",
        "/info",
        "/admin",
    ]
