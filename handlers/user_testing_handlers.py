import asyncio
import logging
import random

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import DailyStatisticsManager
from keyboards import keyboard_builder
from lexicon import (MessageTexts, BasicButtons, MainMenuButtons, list_right_answers,
                     PrepositionsSections)
from services.daily_statistics import DailyStatisticsService
from services.testing import TestingService
from services.user_progress import UserProgressService
from states import TestingFSM
from utils import send_message_to_admin, update_state_data

user_testing_router: Router = Router()

testing_service: TestingService = TestingService()
user_progress_service: UserProgressService = UserProgressService()
daily_statistics_service:DailyStatisticsService = DailyStatisticsService()


@user_testing_router.callback_query((F.data == 'rules_testing'))
async def rules_testing(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(MessageTexts.TEST_RULES,
                                     reply_markup=await keyboard_builder(1, close_rules_tests=BasicButtons.CLOSE))


@user_testing_router.callback_query((F.data == 'close_rules_tests'))
async def close_rules_testing(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logging.error(f"Failed to delete message: {e}")


@user_testing_router.callback_query((F.data == MainMenuButtons.TESTING))  # выбор раздела для прохождения теста
async def start_testing_with_rules(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(MessageTexts.TESTING_HELLO,
                                     reply_markup=await keyboard_builder(1, rules_testing=BasicButtons.RULES,
                                                                         close_rules_tests=BasicButtons.CLOSE))
    # await asyncio.sleep(3)
    sections = await testing_service.get_section_names()
    await callback.message.answer(MessageTexts.CHOOSE_SECTION,
                                  reply_markup=await keyboard_builder(1, *[section for section in sections],
                                                                      BasicButtons.MAIN_MENU))
    await state.set_state(TestingFSM.selecting_section)


@user_testing_router.callback_query((F.data == BasicButtons.BACK),
                                    StateFilter(TestingFSM.selecting_subsection))
@user_testing_router.callback_query((F.data == 'choose_other_section_training'))
async def start_testing(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    sections = await testing_service.get_section_names()
    await callback.message.edit_text(MessageTexts.CHOOSE_SECTION,
                                     reply_markup=await keyboard_builder(1, *[section for section in sections],
                                                                         BasicButtons.MAIN_MENU))
    await state.set_state(TestingFSM.selecting_section)


@user_testing_router.callback_query(StateFilter(TestingFSM.selecting_section))  # выбор подраздела для прохождения теста
async def choosing_section_testing(callback: CallbackQuery, state: FSMContext):
    section = callback.data
    await callback.answer()
    subsections = await testing_service.get_subsection_names(section=section)
    await callback.message.edit_text(
        MessageTexts.CHOOSE_SUBSECTION_TEST,
        reply_markup=await keyboard_builder(1, *[subsection for subsection in subsections], BasicButtons.BACK,
                                            BasicButtons.MAIN_MENU))
    await state.set_state(TestingFSM.selecting_subsection)
    await update_state_data(state, section=callback.data, subsection=None)


@user_testing_router.callback_query(
    StateFilter(TestingFSM.selecting_subsection))  # подраздел выбран, получен в callback
async def choosing_subsection_testing(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    subsection = callback.data
    additional_rules = ''
    if subsection == PrepositionsSections.PREPOSITIONS_OF_THE_TIME:
        additional_rules = '\n' + MessageTexts.PREPOSITIONS_OF_THE_TIME_RULES + '\n'

    await callback.message.edit_text(f"""<b>«{subsection}»</b>{additional_rules}
Are you ready?""", reply_markup=await keyboard_builder(1, BasicButtons.MAIN_MENU, args_go_first=False,
                                                       ready_for_test=BasicButtons.READY))
    await update_state_data(state, subsection=subsection)
    await state.set_state(TestingFSM.selected_subsection)


@user_testing_router.callback_query((F.data == 'ready_for_test'))
async def chose_subsection_testing(callback: CallbackQuery, state: FSMContext, prev_message_delete: bool = True):
    await callback.answer()
    if prev_message_delete:
        try:
            await callback.message.delete()
        except TelegramBadRequest as e:
            logging.error(f"Failed to delete message: {e}")
    else:
        pass
    data = await state.get_data()
    subsection, section, user_id = data.get('subsection'), data.get('section'), callback.from_user.id
    exercise = await testing_service.get_random_testing_exercise(section=section, subsection=subsection,
                                                                 user_id=user_id)

    if exercise:
        test, answer, id_exercise = exercise
    else:
        first_try_count, success_count, total_exercises_count = await user_progress_service.get_counts_completed_exercises_testing(
            user_id=user_id, section=section,
            subsection=subsection)
        await callback.message.answer(f"""{MessageTexts.ALL_EXERCISES_COMPLETED}
Всего заданий выполнено: <b>{success_count} из {total_exercises_count}</b>
С первой попытки: <b>{first_try_count}</b>""",
                                      reply_markup=await keyboard_builder(1,
                                                                          choose_other_section_training=BasicButtons.CHOOSE_OTHER_SECTION,
                                                                          start_again_test=BasicButtons.START_AGAIN))
        return
    await callback.message.answer(test)
    await state.set_state(TestingFSM.in_process)
    await update_state_data(state, current_test=test, current_answer=answer.strip(), current_id=id_exercise)


@user_testing_router.message(StateFilter(TestingFSM.in_process))  # В процессе тестирования
async def in_process_testing(message: Message, state: FSMContext):
    await daily_statistics_service.update('testing_exercises')
    data = await state.get_data()
    section, subsection, exercise_id, user_id = data.get('section'), data.get('subsection'), data.get(
        'current_id'), message.from_user.id
    answer = data.get('current_answer')
    if message.text.lower().replace(' ', '') == answer.lower().replace(' ', ''):
        first_try = await user_progress_service.mark_exercise_completed(exercise_type='Testing',
                                                                        section=section,
                                                                        subsection=subsection,
                                                                        exercise_id=exercise_id, user_id=user_id,
                                                                        success=True)
        data = await state.get_data()
        subsection, section, user_id = data.get('subsection'), data.get('section'), message.from_user.id

        exercise = await testing_service.get_random_testing_exercise(section=section,
                                                                     subsection=subsection,
                                                                     user_id=user_id)

        if not exercise:
            first_try_count, success_count, total_exercises_count = await user_progress_service.get_counts_completed_exercises_testing(
                user_id=user_id, section=section,
                subsection=subsection)
            await message.answer(f"""{MessageTexts.ALL_EXERCISES_COMPLETED}
Всего заданий выполнено: <b>{success_count} из {total_exercises_count}</b>
С первой попытки: <b>{first_try_count}</b>""",
                                 reply_markup=await keyboard_builder(1, start_again_test=BasicButtons.START_AGAIN,
                                                                     choose_other_section_training=BasicButtons.CHOOSE_OTHER_SECTION))
            username = message.from_user.username or message.from_user.full_name
            await send_message_to_admin(f"""Пользователь @{username} выполнил тест
<b>{section} – {subsection}</b>\nС первой попытки <b>{first_try_count} из {success_count}</b>""")
        else:
            test, answer, id_exercise = exercise
            await update_state_data(state, current_test=test, current_answer=answer.strip(), current_id=id_exercise)
            if first_try:
                await message.answer(f'{random.choice(list_right_answers)}\nYou got it on the first try!')
                await message.answer(test)
            else:
                await message.answer(f'{random.choice(list_right_answers)}')
                await message.answer(test)
    else:
        await message.answer(MessageTexts.INCORRECT_ANSWER,
                             reply_markup=await keyboard_builder(1, see_answer_testing=BasicButtons.SEE_ANSWER))
        await user_progress_service.mark_exercise_completed(exercise_type='Testing', section=section,
                                                            subsection=subsection,
                                                            exercise_id=exercise_id, user_id=user_id, success=False)


@user_testing_router.callback_query((F.data == 'start_again_test'))
async def start_again_testing(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(MessageTexts.ARE_YOU_SURE_START_AGAIN,
                                     reply_markup=await keyboard_builder(1, BasicButtons.CLOSE, args_go_first=False,
                                                                         sure_start_again_test=BasicButtons.START_AGAIN))


@user_testing_router.callback_query((F.data == 'sure_start_again_test'))
async def start_again_testing(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    subsection, section, user_id = data.get('subsection'), data.get('section'), callback.from_user.id
    await user_progress_service.delete_progress_by_subsection(user_id=user_id, section=section, subsection=subsection)
    await callback.message.edit_text(f'Прогресс по тесту {section} – {subsection} сброшен')
    await chose_subsection_testing(callback, state, prev_message_delete=False)


@user_testing_router.callback_query((F.data == 'see_answer_testing'))  # Подсказка в тестировании
async def see_answer_testing(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    answer = data.get('current_answer')
    await callback.message.edit_text(f'Правильный ответ: {answer.capitalize()}')
    await asyncio.sleep(3)
    await chose_subsection_testing(callback, state, prev_message_delete=False)
