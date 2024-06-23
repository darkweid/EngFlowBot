import asyncio, random, json, csv, time

from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import LinkPreviewOptions, CallbackQuery, Message, ReplyKeyboardRemove
from states import LearningFSM
from utils import send_message_to_admin, update_state_data
from lexicon import *
from db import *
from keyboards import *

user_router: Router = Router()
exercise_manager = ExerciseManager()
user_progress_manager = UserProgressManager()
user_manager = UserManager()


@user_router.message(Command(commands=["reset_fsm"]))
async def resetFSM_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Сброшено!')


@user_router.message(Command(commands=["start"]),
                     StateFilter(default_state))  # стандартное состояние, пользователь не зарегистрирован в боте
async def process_start_command(message: Message, state: FSMContext):
    user_id = int(message.from_user.id)
    full_name = message.from_user.full_name
    tg_login = message.from_user.username
    await user_manager.add_user(user_id, full_name, tg_login)
    await message.answer(
        f'Привет, {message.from_user.full_name}\nЯ бот от <a href="http://t.me/Oprus">Оли Прус</a>😊'
        f'\n{MessageTexts.WELCOME_NEW_USER.value}',
        link_preview_options=LinkPreviewOptions(is_disabled=True))
    await message.answer(MessageTexts.WELCOME_EXISTING_USER,
                         reply_markup=await keyboard_builder(1, *[button.value for button in MainMenuButtons]))
    await send_message_to_admin(message.bot, f"""Зарегистрирован новый пользователь.
Имя: {message.from_user.full_name}\nТелеграм: @{message.from_user.username}\n""")
    await state.set_state(LearningFSM.existing_user)


@user_router.message(Command(commands=['main_menu']),
                     ~StateFilter(default_state))  # пользователь зарегистрирован в боте
@user_router.message(Command(commands=['start']), ~StateFilter(default_state))
async def process_start_command_existing_user(message: Message, state: FSMContext):
    user_id = int(message.from_user.id)
    full_name = message.from_user.full_name
    tg_login = message.from_user.username
    await user_manager.add_user(user_id, full_name, tg_login)
    await message.answer(MessageTexts.WELCOME_EXISTING_USER.value,
                         reply_markup=await keyboard_builder(1, *[button.value for button in MainMenuButtons]))
    await state.set_state(LearningFSM.choose_type_of_exercise)


@user_router.message(Command(commands=["stats"]), ~StateFilter(default_state))
async def stats_user_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    info = await user_manager.get_user_info(user_id, admin=False)

    await message.answer(f'{info}\n\n{MessageTexts.STATS_USER.value}',
                         reply_markup=await keyboard_builder(1, BasicButtons.CLOSE, args_go_first=False,
                                                             stats_today=BasicButtons.TODAY,
                                                             stats_last_week=BasicButtons.LAST_WEEK,
                                                             stats_last_month=BasicButtons.LAST_MONTH))


@user_router.callback_query(F.data == 'stats_today')
@user_router.callback_query(F.data == 'stats_last_week')
@user_router.callback_query(F.data == 'stats_last_month')
async def see_stats_user(callback: CallbackQuery, state: FSMContext):
    cbdata = callback.data
    user_id = callback.from_user.id
    if cbdata == 'stats_today':
        info = await user_progress_manager.get_activity_by_user(user_id)
    elif cbdata == 'stats_last_week':
        info = await user_progress_manager.get_activity_by_user(user_id, interval=7)
    else:
        info = await user_progress_manager.get_activity_by_user(user_id, interval=30)
    await callback.message.answer(info, reply_markup=await keyboard_builder(1, BasicButtons.CLOSE))


@user_router.callback_query(F.data == BasicButtons.BACK.value, StateFilter(LearningFSM.testing_choosing_section))
async def main_menu_existing_user(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(MessageTexts.WELCOME_EXISTING_USER.value,
                                     reply_markup=await keyboard_builder(1,
                                                                         *[button.value for button in MainMenuButtons]))
    await state.set_state(LearningFSM.choose_type_of_exercise)


@user_router.callback_query((F.data == BasicButtons.MAIN_MENU.value), ~StateFilter(default_state))
async def main_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(MessageTexts.WELCOME_EXISTING_USER.value,
                                  reply_markup=await keyboard_builder(1, *[button.value for button in MainMenuButtons]))
    await state.set_state(LearningFSM.default)


@user_router.callback_query((F.data == 'Правила тесты'))
async def rules_testing(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(MessageTexts.TEST_RULES.value,
                                     reply_markup=await keyboard_builder(1, close_rules_tests=BasicButtons.CLOSE))


@user_router.callback_query((F.data == 'close_rules_tests'))
async def close_rules_testing(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()


@user_router.callback_query((F.data == MainMenuButtons.TESTING.value))  # выбор раздела для прохождения теста
async def start_testing(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Отличный выбор!')
    await  callback.message.edit_text(MessageTexts.TESTING_HELLO,
                                      reply_markup=await keyboard_builder(1, rules_testing=BasicButtons.RULES,
                                                                          close_rules_tests=BasicButtons.CLOSE))
    # await asyncio.sleep(3)
    await callback.message.answer(MessageTexts.CHOOSE_SECTION.value,
                                  reply_markup=await keyboard_builder(1, *[button.value for button in
                                                                           TestingSections], BasicButtons.BACK,
                                                                      BasicButtons.MAIN_MENU))
    await state.set_state(LearningFSM.testing_choosing_section)


@user_router.callback_query((F.data == 'choose_other_section_training'))
async def start_testing(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Отличный выбор!')
    await callback.message.edit_text(MessageTexts.CHOOSE_SECTION.value,
                                     reply_markup=await keyboard_builder(1, *[button.value for button in
                                                                              TestingSections], BasicButtons.BACK,
                                                                         BasicButtons.MAIN_MENU))
    await state.set_state(LearningFSM.testing_choosing_section)


@user_router.callback_query((F.data == BasicButtons.BACK.value), StateFilter(LearningFSM.testing_choosing_subsection))
async def start_testing(callback: CallbackQuery, state: FSMContext):  # выбор раздела для прохождения тесте
    await callback.answer()
    await callback.message.edit_text(MessageTexts.CHOOSE_SECTION.value,
                                     reply_markup=await keyboard_builder(1, *[button.value for button in
                                                                              TestingSections], BasicButtons.BACK,
                                                                         BasicButtons.MAIN_MENU))
    await state.set_state(LearningFSM.testing_choosing_section)


@user_router.callback_query(StateFilter(LearningFSM.testing_choosing_section))  # выбор ПОДраздела для прохождения теста
async def choosing_section_testing(callback: CallbackQuery, state: FSMContext):
    section = testing_section_mapping.get(callback.data)
    if section is None:
        await callback.answer()
        await callback.message.edit_text(MessageTexts.ERROR)
        await state.set_state(LearningFSM.default)
        return

    await callback.message.edit_text(
        MessageTexts.CHOOSE_SUBSECTION_TEST.value,
        reply_markup=await keyboard_builder(1, *[button.value for button in section], BasicButtons.BACK,
                                            BasicButtons.MAIN_MENU))
    await state.set_state(LearningFSM.testing_choosing_subsection)
    await update_state_data(state, section=callback.data, subsection=None)


@user_router.callback_query(
    StateFilter(LearningFSM.testing_choosing_subsection))  # подраздел выбран, получен в callback
async def choosing_subsection_testing(callback: CallbackQuery, state: FSMContext):
    subsection = callback.data
    data = await state.get_data()
    section = data.get('section')
    await callback.answer()
    await callback.message.edit_text(f"""Отлично, ты выбрал:\n «{section} - {subsection}»\n
Готов проходить?""", reply_markup=await keyboard_builder(1, BasicButtons.MAIN_MENU, args_go_first=False,
                                                         ready_for_test=BasicButtons.READY))
    await update_state_data(state, subsection=subsection)
    await state.set_state(LearningFSM.testing_choosed_subsection)


@user_router.callback_query((F.data == 'ready_for_test'))
async def choosed_subsection_testing(callback: CallbackQuery, state: FSMContext, prev_message_delete: bool = True):
    await callback.answer()
    if prev_message_delete:
        await callback.message.delete()
    else:
        pass
    data = await state.get_data()
    subsection, section, user_id = data.get('subsection'), data.get('section'), callback.from_user.id
    exercise = await exercise_manager.get_random_testing_exercise(section=section, subsection=subsection,
                                                                  user_id=user_id)
    if exercise:
        test, answer, id = exercise
    else:
        await callback.message.answer(MessageTexts.ALL_EXERCISES_COMPLETED, reply_markup=await keyboard_builder(1,
                                                                                                                choose_other_section_training=BasicButtons.CHOOSE_OTHER_SECTION))
        return
    await callback.message.answer(test)
    await state.set_state(LearningFSM.testing_in_process)
    await update_state_data(state, current_test=test, current_answer=answer.strip(), current_id=id)


@user_router.message(StateFilter(LearningFSM.testing_in_process))  # В процессе тестирования
async def in_process_testing(message: Message, state: FSMContext):
    data = await state.get_data()
    section, subsection, exercise_id, user_id = data.get('section'), data.get('subsection'), data.get(
        'current_id'), message.from_user.id
    answer = data.get('current_answer')
    if message.text.lower() == answer.lower():

        first_try = await user_progress_manager.mark_exercise_completed(exercise_type='Testing',
                                                                        section=section,
                                                                        subsection=subsection,
                                                                        exercise_id=exercise_id, user_id=user_id,
                                                                        success=True)
        data = await state.get_data()
        subsection, section, user_id = data.get('subsection'), data.get('section'), message.from_user.id
        exercise = await exercise_manager.get_random_testing_exercise(section=section,
                                                                      subsection=subsection,
                                                                      user_id=user_id)
        if not exercise:
            await message.answer(MessageTexts.ALL_EXERCISES_COMPLETED, reply_markup=await keyboard_builder(1,
                                                                                                           choose_other_section_training=BasicButtons.CHOOSE_OTHER_SECTION))

        else:
            test, answer, id = exercise
            await update_state_data(state, current_test=test, current_answer=answer.strip(), current_id=id)
            if first_try:
                await message.answer(f'{random.choice(list_right_answers)}\nYou got it on the first try!')
                await message.answer(test)
            else:
                await message.answer(f'{random.choice(list_right_answers)}')
                await message.answer(test)

    else:
        await message.answer(MessageTexts.INCORRECT_ANSWER,
                             reply_markup=await keyboard_builder(1, see_answer_testing=BasicButtons.SEE_ANSWER))
        await user_progress_manager.mark_exercise_completed(exercise_type='Testing', section=section,
                                                            subsection=subsection,
                                                            exercise_id=exercise_id, user_id=user_id, success=False)


@user_router.callback_query((F.data == 'see_answer_testing'))  # Подсказка в тестировании
async def see_answer_testing(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    answer = data.get('current_answer')
    await callback.message.edit_text(f'Правильный ответ: {answer.capitalize()}')
    await asyncio.sleep(3)
    await choosed_subsection_testing(callback, state, prev_message_delete=False)


@user_router.message(Command(commands=["info"]))
async def info_command(message: Message, state: FSMContext):
    await state.set_state(LearningFSM.default)
    await message.answer(MessageTexts.INFO_RULES.value,
                         reply_markup=await keyboard_builder(1, BasicButtons.MAIN_MENU))


@user_router.message()
async def send_idontknow(message: Message):
    await message.reply(
        f'Hey, {message.from_user.first_name}\n{MessageTexts.ERROR.value}'
    )
