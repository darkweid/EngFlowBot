from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from states import UserFSM
from utils import time_zones, schedule_reminders
from lexicon import BasicButtons, MessageTexts
from db import UserManager
from keyboards import keyboard_builder

user_reminder_router: Router = Router()
user_manager = UserManager()


@user_reminder_router.message(Command(commands=["reminder"]), ~StateFilter(default_state))
async def reminder_command(message: Message):
    user_id = message.from_user.id
    info = await user_manager.get_user(user_id)
    reminder_time = info.get('reminder_time')
    time_zone = info.get('time_zone')
    if time_zone and reminder_time:
        await message.answer(
            f"""<b>Твой часовой пояс : UTC{time_zone}
Установленное время напоминаний: {reminder_time.strftime("%H:%M")}</b>
\nЕсли нужно - можешь установить другие""",
            reply_markup=await keyboard_builder(1, BasicButtons.CHANGE_TIME_ZONE,
                                                BasicButtons.CHANGE_REMINDER_TIME,
                                                BasicButtons.TURN_OFF_REMINDER,
                                                BasicButtons.CLOSE))
    elif time_zone and not reminder_time:
        await message.answer(f"""<b>Твой часовой пояс : UTC{time_zone}\nНапоминания выключены</b>
\nЕсли нужно - можешь изменить часовой пояс или установить время напоминаний""",
                             reply_markup=await keyboard_builder(1, BasicButtons.CHANGE_TIME_ZONE,
                                                                 BasicButtons.CHANGE_REMINDER_TIME,
                                                                 BasicButtons.CLOSE))
    elif not time_zone and not reminder_time:
        await message.answer(f"""<b>Часовой пояс не установлен\nНапоминания выключены</b>
\nМожешь установить свой часовой пояс и затем время напоминаний""",
                             reply_markup=await keyboard_builder(1, BasicButtons.CHANGE_TIME_ZONE,
                                                                 BasicButtons.CLOSE))


@user_reminder_router.callback_query(F.data == BasicButtons.CHANGE_TIME_ZONE)
@user_reminder_router.callback_query(F.data == 'set_tz_new_user')

async def choose_timezone(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(MessageTexts.CHOOSE_TIMEZONE,
                                  reply_markup=await keyboard_builder(4, BasicButtons.CLOSE, args_go_first=False,
                                                                      **time_zones))


@user_reminder_router.callback_query(F.data.startswith('tz_UTC'))
async def set_timezone(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(f"""Установлен часовой пояс {time_zones.get(callback.data)}
Теперь ты можешь установить время напоминаний""",
                                     reply_markup=await keyboard_builder(1, BasicButtons.CHANGE_REMINDER_TIME,
                                                                         BasicButtons.CLOSE))
    await user_manager.set_timezone(user_id=callback.from_user.id, timezone=callback.data.split('|')[1])
    await schedule_reminders()


@user_reminder_router.callback_query(F.data == BasicButtons.CHANGE_REMINDER_TIME)
async def set_reminder(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(f"""В какое время тебе напоминать заниматься?
Введи время в формате <b>HH:MM</b>
Например - 10:35""", reply_markup=await keyboard_builder(1, BasicButtons.CLOSE))
    await state.set_state(UserFSM.set_reminder_time)


@user_reminder_router.callback_query(F.data == BasicButtons.TURN_OFF_REMINDER)
async def turn_off_reminder(callback: CallbackQuery):
    await callback.answer()
    await user_manager.set_reminder_time(user_id=callback.from_user.id, time=None)
    await schedule_reminders()
    await callback.message.answer("""Напоминания выключены,
ты всегда можешь их включить нажав команду /reminder в меню""",
                                  reply_markup=await keyboard_builder(1, BasicButtons.CLOSE))


@user_reminder_router.message(StateFilter(UserFSM.set_reminder_time))
async def set_reminder_time(message: Message):
    try:
        time = datetime.strptime(message.text, "%H:%M").time()
        await user_manager.set_reminder_time(user_id=message.from_user.id, time=time)
        await schedule_reminders()
        await message.delete()
        await message.answer(f'Отлично, буду напоминать тебе заниматься каждый день в {time.strftime("%H:%M")}')
    except Exception as e:
        await message.delete()
        await message.answer(f'\"{message.text}\" не соответствует формату HH:MM')

