from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import LinkPreviewOptions, Message

from config_data.settings import settings
from keyboards import keyboard_builder
from lexicon import BasicButtons, MainMenuButtons, MessageTexts
from services.daily_statistics import DailyStatisticsService
from services.user import UserService
from states import UserFSM
from utils import send_message_to_admin

user_commands_router: Router = Router()


@user_commands_router.message(Command(commands=["reset_fsm"]))
async def reset_fsm_command(message: Message,
                            state: FSMContext,
                            ):
    await state.clear()
    await message.answer('Сброшено!')


@user_commands_router.message(Command(commands=["start"]),
                              StateFilter(
                                  default_state))  # default state, user is not registered yet
async def process_start_command(message: Message,
                                state: FSMContext,
                                user_service: UserService,
                                daily_statistics_service: DailyStatisticsService,
                                ):
    user_id = int(message.from_user.id)
    full_name = message.from_user.full_name
    tg_login = message.from_user.username
    await user_service.add_user(user_id, full_name, tg_login)
    await message.answer(MessageTexts.WELCOME_NEW_USER.format(user_name=full_name,
                                                              owner_tg_link=settings.owner_tg_link,
                                                              owner_name=settings.owner_name),
                         link_preview_options=LinkPreviewOptions(is_disabled=True),
                         reply_markup=await keyboard_builder(1, set_tz_new_user=BasicButtons.TURN_ON_REMINDER))
    await message.answer(MessageTexts.WELCOME_EXISTING_USER,
                         reply_markup=await keyboard_builder(1, *[button for button in MainMenuButtons]))
    await send_message_to_admin(
        text=f"""Зарегистрирован новый пользователь.
Имя: {message.from_user.full_name}
{'telegram: @' + message.from_user.username if tg_login else 'У пользователя нет ника'}"""
    )

    await state.set_state(UserFSM.existing_user)
    await daily_statistics_service.update('new_user')


@user_commands_router.message(Command(commands=['main_menu']),
                              ~StateFilter(default_state))  # user already registered
@user_commands_router.message(Command(commands=['start']), ~StateFilter(default_state))
async def process_start_command_existing_user(message: Message,
                                              state: FSMContext,
                                              user_service: UserService,
                                              ):
    user_id = int(message.from_user.id)
    full_name = message.from_user.full_name
    tg_login = message.from_user.username
    await user_service.add_user(user_id, full_name, tg_login)
    await message.answer(MessageTexts.WELCOME_EXISTING_USER,
                         reply_markup=await keyboard_builder(1, *[button for button in MainMenuButtons]))
    await state.set_state(UserFSM.default)


@user_commands_router.message(Command(commands=["info"]))
async def info_command(message: Message,
                       state: FSMContext,
                       ):
    await state.set_state(UserFSM.default)
    await message.answer(MessageTexts.INFO_RULES.format(owner_tg_link=settings.owner_tg_link),
                         link_preview_options=LinkPreviewOptions(is_disabled=True),
                         reply_markup=await keyboard_builder(1, BasicButtons.MAIN_MENU))
