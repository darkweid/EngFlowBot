from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import LinkPreviewOptions, Message
from states import UserFSM
from utils import send_message_to_admin
from lexicon import BasicButtons, MainMenuButtons, MessageTexts
from db import UserManager, DailyStatisticsManager
from keyboards import keyboard_builder

user_commands_router: Router = Router()
user_manager = UserManager()
daily_stats_manager = DailyStatisticsManager()



@user_commands_router.message(Command(commands=["reset_fsm"]))
async def reset_fsm_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Сброшено!')


@user_commands_router.message(Command(commands=["start"]),
                              StateFilter(
                                  default_state))  # стандартное состояние, пользователь не зарегистрирован в боте
async def process_start_command(message: Message, state: FSMContext):
    user_id = int(message.from_user.id)
    full_name = message.from_user.full_name
    tg_login = message.from_user.username
    await user_manager.add_user(user_id, full_name, tg_login)
    await message.answer(MessageTexts.WELCOME_NEW_USER.value.format(user_name=full_name),
                         link_preview_options=LinkPreviewOptions(is_disabled=True),
                         reply_markup=await keyboard_builder(1, BasicButtons.TURN_ON_REMINDER))
    await message.answer(MessageTexts.WELCOME_EXISTING_USER.value,
                         reply_markup=await keyboard_builder(1, *[button.value for button in MainMenuButtons]))
    await send_message_to_admin(text=f"""Зарегистрирован новый пользователь.
Имя: {message.from_user.full_name}\nТелеграм: @{message.from_user.username}\n""")
    await state.set_state(UserFSM.existing_user)
    await daily_stats_manager.update('new_user')


@user_commands_router.message(Command(commands=['main_menu']),
                              ~StateFilter(default_state))  # пользователь зарегистрирован в боте
@user_commands_router.message(Command(commands=['start']), ~StateFilter(default_state))
async def process_start_command_existing_user(message: Message, state: FSMContext):
    user_id = int(message.from_user.id)
    full_name = message.from_user.full_name
    tg_login = message.from_user.username
    await user_manager.add_user(user_id, full_name, tg_login)
    await message.answer(MessageTexts.WELCOME_EXISTING_USER.value,
                         reply_markup=await keyboard_builder(1, *[button.value for button in MainMenuButtons]))
    await state.set_state(UserFSM.default)


@user_commands_router.message(Command(commands=["info"]))
async def info_command(message: Message, state: FSMContext):
    await state.set_state(UserFSM.default)
    await message.answer(MessageTexts.INFO_RULES.value,
                         link_preview_options=LinkPreviewOptions(is_disabled=True),
                         reply_markup=await keyboard_builder(1, BasicButtons.MAIN_MENU))
