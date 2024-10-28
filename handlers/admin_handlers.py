import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram import Router, F
from config_data.config import Config, load_config
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from states import AdminFSM, UserFSM
from db import TestingManager, UserProgressManager, UserManager, NewWordsExerciseManager, UserWordsLearningManager, \
    DailyStatisticsManager
from datetime import datetime, date, timedelta
from keyboards import keyboard_builder, keyboard_builder_users
from lexicon import (AdminMenuButtons, MessageTexts, BasicButtons, TestingSections, testing_section_mapping,
                     NewWordsSections)
from utils import (update_state_data, delete_scheduled_broadcasts, schedule_broadcast, send_message_to_user,
                   send_long_message)

config: Config = load_config()
ADMINS: list = config.tg_bot.admin_ids

admin_router: Router = Router()
testing_manager: TestingManager = TestingManager()
user_progress_manager: UserProgressManager = UserProgressManager()
user_manager: UserManager = UserManager()
words_manager: NewWordsExerciseManager = NewWordsExerciseManager()
user_words_learning_manager: UserWordsLearningManager = UserWordsLearningManager()
daily_progress_manager: DailyStatisticsManager = DailyStatisticsManager()


@admin_router.message(Command(commands=["admin"]))
async def admin_command(message: Message, state: FSMContext):
    if str(message.from_user.id) in ADMINS:
        await message.answer('🔘 Привет, что будем делать? 🔘',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.EXERCISES,
                                                                 AdminMenuButtons.SEE_ACTIVITY_DAY,
                                                                 AdminMenuButtons.SEE_ACTIVITY_WEEK,
                                                                 AdminMenuButtons.SEE_ACTIVITY_MONTH,
                                                                 AdminMenuButtons.USERS, AdminMenuButtons.BROADCAST,
                                                                 AdminMenuButtons.EXIT))
        await state.set_state(AdminFSM.default)
    else:
        await message.answer('🚫 Вам сюда нельзя 🚫')


@admin_router.callback_query((F.data == AdminMenuButtons.MAIN_MENU.value))
async def admin_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('🔘 Привет, что будем делать? 🔘',
                                     reply_markup=await keyboard_builder(1, AdminMenuButtons.EXERCISES,
                                                                         AdminMenuButtons.SEE_ACTIVITY_DAY,
                                                                         AdminMenuButtons.SEE_ACTIVITY_WEEK,
                                                                         AdminMenuButtons.SEE_ACTIVITY_MONTH,
                                                                         AdminMenuButtons.USERS,
                                                                         AdminMenuButtons.BROADCAST,
                                                                         AdminMenuButtons.EXIT))
    await state.set_state(AdminFSM.default)


@admin_router.callback_query((F.data == 'close_message_admin'), ~StateFilter(AdminFSM.see_user_info))
@admin_router.callback_query((F.data == AdminMenuButtons.EXIT.value))
async def admin_exit(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logging.error(f"Failed to delete message: {e}")
    await callback.answer('До скорых встреч 👋')
    await update_state_data(state, admin_section=None, admin_subsection=None, index_testing_edit=None,
                            index_testing_delete=None)
    await state.set_state(UserFSM.default)


@admin_router.callback_query((F.data == 'admin_close_without_state_changes'))  # close without change state
async def close_message_without_state_changes(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logging.error(f"Failed to delete message: {e}")


@admin_router.callback_query((F.data == AdminMenuButtons.EXERCISES.value), StateFilter(AdminFSM.default))
@admin_router.callback_query((F.data == BasicButtons.BACK.value), StateFilter(AdminFSM.select_section_testing))
async def admin_exercises(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Выбери группу упражнений:',
                                     reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                         AdminMenuButtons.EXIT,
                                                                         args_go_first=False,
                                                                         tests_admin=AdminMenuButtons.TESTING,
                                                                         new_words_admin=AdminMenuButtons.NEW_WORDS,
                                                                         irr_verbs_admin=AdminMenuButtons.IRR_VERBS))
    await state.set_state(AdminFSM.default)


# Testing
@admin_router.callback_query((F.data == BasicButtons.BACK.value), StateFilter(AdminFSM.select_subsection_testing))
@admin_router.callback_query((F.data == 'tests_admin'))
async def admin_start_testing(callback: CallbackQuery, state: FSMContext):  # выбор раздела тестов
    await callback.answer()
    await callback.message.edit_text('Выбери раздел тестов:',
                                     reply_markup=await keyboard_builder(1, *[button.value for button in
                                                                              TestingSections], BasicButtons.BACK,
                                                                         BasicButtons.MAIN_MENU))
    await state.set_state(AdminFSM.select_section_testing)


@admin_router.callback_query(StateFilter(AdminFSM.select_section_testing))  # выбор ПОДраздела теста
async def admin_choosing_section_testing(callback: CallbackQuery, state: FSMContext):
    section = testing_section_mapping.get(callback.data)
    if section is None:
        await callback.answer()
        await callback.message.edit_text(MessageTexts.ERROR.value)
        await state.set_state(UserFSM.default)
        return

    await callback.message.edit_text(
        MessageTexts.CHOOSE_SUBSECTION_TEST.value,
        reply_markup=await keyboard_builder(1, *[button.value for button in section], BasicButtons.BACK,
                                            BasicButtons.MAIN_MENU))
    await state.set_state(AdminFSM.select_subsection_testing)
    await update_state_data(state, admin_section=callback.data, admin_subsection=None)


@admin_router.callback_query(
    StateFilter(AdminFSM.select_subsection_testing))  # подраздел выбран, получен в callback
async def admin_choosing_subsection_testing(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    admin_subsection = callback.data
    data = await state.get_data()
    admin_section = data.get('admin_section')
    await callback.message.edit_text(
        f'Выбран раздел\n «{admin_section} - {admin_subsection}»\n\nЧто нужно сделать?',
        reply_markup=await keyboard_builder(1, AdminMenuButtons.SEE_EXERCISES_TESTING,
                                            AdminMenuButtons.ADD_EXERCISE_TESTING,
                                            AdminMenuButtons.EDIT_EXERCISE_TESTING,
                                            AdminMenuButtons.DEL_EXERCISE_TESTING,
                                            AdminMenuButtons.MAIN_MENU,
                                            AdminMenuButtons.EXIT))
    await update_state_data(state, admin_subsection=admin_subsection)
    await state.set_state(AdminFSM.select_management_action_testing)


@admin_router.callback_query(F.data == AdminMenuButtons.SEE_EXERCISES_TESTING.value)
@admin_router.callback_query(F.data == AdminMenuButtons.ADD_EXERCISE_TESTING.value)
@admin_router.callback_query(F.data == AdminMenuButtons.EDIT_EXERCISE_TESTING.value)
@admin_router.callback_query(F.data == AdminMenuButtons.DEL_EXERCISE_TESTING.value)
async def admin_testing_management(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    subsection, section = data.get('admin_subsection'), data.get('admin_section')
    exercise_name = f'\"{section} - {subsection}\"'

    if section and callback.data == AdminMenuButtons.SEE_EXERCISES_TESTING.value:
        result = await testing_manager.get_testing_exercises(subsection)
        if result:
            await callback.answer()
            await send_long_message(callback, f'Вот все предложения из раздела\n{exercise_name}:\n{result}',
                                    reply_markup=await keyboard_builder(1, close_message_admin=AdminMenuButtons.CLOSE))
        else:
            await callback.answer()
            await callback.message.edit_text(f'В разделе \n{exercise_name} ещё нет упражнений',
                                             reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                                 AdminMenuButtons.EXIT))


    elif callback.data == AdminMenuButtons.ADD_EXERCISE_TESTING.value:
        await callback.message.edit_text(f"""Введи предложение и ответ к нему для добавления в раздел\n{exercise_name}\n
В формате: \nEnglish sentence=+=Answer
\nМожно отправить несколько упражнений, тогда каждое упражнение должно начинаться с новой строки
и сообщение должно содержать не более 4096 символов(лимит Telegram)""",
                                         reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                             AdminMenuButtons.EXIT))
        await state.set_state(AdminFSM.adding_exercise_testing)

    elif callback.data == AdminMenuButtons.EDIT_EXERCISE_TESTING.value:
        await callback.message.edit_text(f'Введи номер предложения для редактирования в разделе\n{exercise_name}\n',
                                         reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                             AdminMenuButtons.EXIT))
        await state.set_state(AdminFSM.editing_exercise_testing)


    elif callback.data == AdminMenuButtons.DEL_EXERCISE_TESTING.value:
        await callback.message.edit_text(f"""Введи номер предложения для удаления из\n{exercise_name}\n
Если нужно удалить одно предложение - введи номер предложения,
если несколько - введи номера предложений через запятую""",
                                         reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                             AdminMenuButtons.EXIT))
        await state.set_state(AdminFSM.deleting_exercise_testing)


@admin_router.message(StateFilter(AdminFSM.adding_exercise_testing))  # ADD
async def admin_adding_sentence_testing(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        subsection, section = data.get('admin_subsection'), data.get('admin_section')
        sentences = message.text.split('\n')
        count_sentences = len(sentences)
        if count_sentences > 1:
            for group_sentences in sentences:
                test, answer = group_sentences.split('=+=')
                await testing_manager.add_testing_exercise(section=section, subsection=subsection, test=test,
                                                           answer=answer)
            await message.answer(
                f'✅Успешно добавлено {count_sentences} упражнений, можешь отправить ещё',
                reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU, AdminMenuButtons.EXIT))

        else:
            test, answer = message.text.split('=+=')
            await testing_manager.add_testing_exercise(section=section, subsection=subsection, test=test,
                                                       answer=answer)

            await message.answer('✅Упражнение успешно добавлено, можешь отправить ещё и я добавлю',
                                 reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                     AdminMenuButtons.EXIT))

    except Exception as e:
        await message.answer('❗️Что-то пошло не так, попробуй еще раз\n\nПроверь формат текста',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.EXIT))
        await message.answer(str(e))


@admin_router.message(StateFilter(AdminFSM.editing_exercise_testing))  # EDIT
async def admin_editing_sentence_testing(message: Message, state: FSMContext):
    if message.text.isdigit():
        index = int(message.text)
        await update_state_data(state, index_testing_edit=index)
        data = await state.get_data()
        subsection, section, index_testing_edit = data.get('admin_subsection'), data.get('admin_section'), data.get(
            'index_testing_edit')
        exercise_name = f'\"{section} - {subsection}\"'
        await message.answer(f"""Отлично, будем изменять \nпредложение № {index_testing_edit}\nВ разделе {exercise_name} 
Введи предложение и ответ к нему в формате: \nEnglish sentence=+=Answer""")
        await state.set_state(AdminFSM.ready_to_edit_exercise_testing)
    else:
        await message.answer('❌Что-то пошло не так, попробуй еще раз',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU, AdminMenuButtons.EXIT))


@admin_router.message(StateFilter(AdminFSM.ready_to_edit_exercise_testing))  # EDIT
async def admin_edit_sentence_testing(message: Message, state: FSMContext):
    data = await state.get_data()
    subsection, section, index_testing_edit = data.get('admin_subsection'), data.get('admin_section'), data.get(
        'index_testing_edit')
    try:
        test, answer = message.text.split('=+=')
        await testing_manager.edit_testing_exercise(section=section, subsection=subsection, test=test, answer=answer,
                                                    index=index_testing_edit)
        await message.answer('✅Успешно изменено',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU))
        await state.set_state(AdminFSM.default)
        await update_state_data(state, admin_section=None, admin_subsection=None, index_testing_edit=None)
    except Exception as e:
        await message.answer('❌Что-то пошло не так, попробуй еще раз',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.EXIT))


@admin_router.message(StateFilter(AdminFSM.deleting_exercise_testing))  # DELETE
async def admin_deleting_sentence_testing(message: Message, state: FSMContext):
    data = await state.get_data()
    subsection, section = data.get('admin_subsection'), data.get('admin_section')
    exercise_name = f'\"{section} - {subsection}\"'
    indexes = []
    try:
        indexes = [int(num) for num in message.text.split(',')]
    except ValueError:
        await message.answer('❌Неправильный формат, попробуй еще раз ввести номер предложения',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU, AdminMenuButtons.EXIT))

    if len(indexes) == 1:
        index = indexes[0]
        await message.answer(f"""✅Предложение № {index}\n<b>Удалено</b> из раздела \n{exercise_name}""",
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU, AdminMenuButtons.EXIT))
        await testing_manager.delete_testing_exercise(section=section, subsection=subsection, index=index)
    elif len(indexes) > 1:
        await message.answer(f"""✅Предложения № {str(indexes)}\n <b>Удалены</b> из раздела \n{exercise_name}""",
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU, AdminMenuButtons.EXIT))
        for index in indexes:
            await testing_manager.delete_testing_exercise(section=section, subsection=subsection, index=index)


# Users

@admin_router.callback_query(F.data == AdminMenuButtons.USERS.value)
async def admin_users(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    users = await user_manager.get_all_users()
    users_ranks_and_points = await user_progress_manager.get_all_users_ranks_and_points(medals_rank=True)
    rank_info = f"""<pre>Рейтинг всех пользователей:\n
[{'№'.center(6)}] [{'Баллы'.center(7)}] [{'Имя'.center(20)}]\n"""
    count = 0
    for user in users_ranks_and_points:
        if count < 3:
            rank_info += \
                f"[{user.get('rank').center(5)}] [{user.get('points').center(7)}] [{user.get('full_name').center(20)}]\n"
        else:
            rank_info += \
                f"[{user.get('rank').center(6)}] [{user.get('points').center(7)}] [{user.get('full_name').center(20)}]\n"
        count += 1
    rank_info += "</pre>"

    await callback.message.answer(rank_info,
                                  reply_markup=await keyboard_builder(1,
                                                                      admin_close_without_state_changes=AdminMenuButtons.CLOSE))
    await callback.message.answer('Выбери пользователя:',
                                  reply_markup=await keyboard_builder_users(users))
    await state.set_state(AdminFSM.see_user_management)


@admin_router.callback_query(F.data == AdminMenuButtons.CLOSE.value, StateFilter(AdminFSM.see_user_management))
async def admin_see_user_info_close_message(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logging.error(f"Failed to delete message: {e}")


@admin_router.callback_query(StateFilter(AdminFSM.see_user_management))
@admin_router.callback_query(F.data == 'dont_delete_user')
async def admin_see_user_info(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = int(callback.data)
    await update_state_data(state, admin_user_id_management=user_id)
    info = await user_manager.get_user_info_text(user_id)
    await callback.message.answer(info,
                                  reply_markup=await keyboard_builder(1,
                                                                      AdminMenuButtons.ADD_WORDS_TO_USER_LEARNING,
                                                                      AdminMenuButtons.SEE_INDIVIDUAL_WORDS,
                                                                      AdminMenuButtons.DEL_INDIVIDUAL_WORDS,
                                                                      AdminMenuButtons.DEL_USER,
                                                                      AdminMenuButtons.CLOSE))
    await state.set_state(AdminFSM.user_managing)


@admin_router.callback_query(F.data == AdminMenuButtons.ADD_WORDS_TO_USER_LEARNING.value,
                             StateFilter(AdminFSM.user_managing))
async def admin_add_words_to_user(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = (await state.get_data()).get('admin_user_id_management')
    user_full_name = (await user_manager.get_user(user_id=user_id)).get('full_name')
    await callback.message.edit_text(
        f"""Добавление слов пользователю <b><i>{user_full_name}</i></b>\n
Введи слово и перевод к нему <b><i>в формате: \nСлово=+=Word</i></b>
\nМожно отправить несколько упражнений, тогда каждое упражнение должно начинаться с новой строки
и сообщение должно содержать не более 4096 символов(лимит Telegram)""",
        reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                            AdminMenuButtons.EXIT))
    await state.set_state(AdminFSM.adding_words_to_user)


@admin_router.message(StateFilter(AdminFSM.adding_words_to_user))
async def admin_adding_words_to_user(message: Message, state: FSMContext):
    try:
        user_id = (await state.get_data()).get('admin_user_id_management')
        user_full_name = (await user_manager.get_user(user_id=user_id)).get('full_name')
        exercises = message.text.split('\n')
        count_exercises = len(exercises)
        if count_exercises > 1:
            for exercise in exercises:
                word_declension = await get_word_declension(count_exercises)
                russian, english = exercise.split('=+=')
                await user_words_learning_manager.admin_add_words_to_learning(user_id=user_id, russian=russian,
                                                                              english=english)
            await message.answer(
                f"""✅Успешно добавлено {word_declension} 
пользователю <b><i>{user_full_name}</i></b>, можешь отправить ещё и я добавлю""",
                reply_markup=await keyboard_builder(1, AdminMenuButtons.EXIT))

            await send_message_to_user(user_id=user_id,
                                       text=f"""Тебе добавили {word_declension}
для изучения. Заходи учить 😊""", learning_button=True)

        else:
            russian, english = message.text.split('=+=')
            await user_words_learning_manager.admin_add_words_to_learning(user_id=user_id, russian=russian,
                                                                          english=english)

            await message.answer(
                f"""✅Слово успешно добавлено пользователю 
<b><i>{user_full_name}</i></b>, можешь отправить ещё и я добавлю""",
                reply_markup=await keyboard_builder(1, AdminMenuButtons.EXIT))
            await send_message_to_user(user_id=user_id,
                                       text=f"""Тебе добавили 1 слово
для изучения. Заходи учить 😊""", learning_button=True)

    except Exception as e:
        await message.answer('❗️Что-то пошло не так, попробуй еще раз\n\nПроверь формат текста',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.EXIT))
        await message.answer(str(e))


@admin_router.callback_query(F.data == AdminMenuButtons.SEE_INDIVIDUAL_WORDS.value,
                             StateFilter(AdminFSM.user_managing))
async def admin_see_individual_words(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    user_id = data.get('admin_user_id_management')
    result = await words_manager.get_new_words_exercises(user_id)
    if result:
        await callback.answer()
        await send_long_message(callback,
                                f'Вот все слова пользователя:\n{result}',
                                reply_markup=await keyboard_builder(1,
                                                                    admin_close_without_state_changes=AdminMenuButtons.CLOSE))
    else:
        await callback.answer()
        await callback.message.edit_text('У пользователя еще нет индивидуальных слов',
                                         reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                             AdminMenuButtons.EXIT))


@admin_router.callback_query(F.data == AdminMenuButtons.DEL_INDIVIDUAL_WORDS.value,
                             StateFilter(AdminFSM.user_managing))
async def admin_del_individual_words(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        f"""Введи номер слова для удаления у пользователя
Если хочешь удалить несколько слов - введи номера слов через запятую""",
        reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                            AdminMenuButtons.EXIT))
    data = await state.get_data()
    user_id = data.get('admin_user_id_management')
    await update_state_data(state, admin_subsection=user_id, admin_section=user_id)
    await state.set_state(AdminFSM.deleting_exercise_words)


async def get_word_declension(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} слово"
    elif 2 <= count % 10 <= 4 and not (12 <= count % 100 <= 14):
        return f"{count} слова"
    else:
        return f"{count} слов"


@admin_router.callback_query(F.data == AdminMenuButtons.DEL_USER.value)
async def admin_delete_user(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Удалить пользователя?",
                                     reply_markup=await keyboard_builder(1, delete_user=AdminMenuButtons.YES,
                                                                         dont_delete_user=AdminMenuButtons.NO))


@admin_router.callback_query(F.data == 'delete_user')
async def admin_delete_user(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    user_id = data.get('admin_user_id_management')
    await user_manager.delete_user(user_id=user_id)
    await callback.message.edit_text('Пользователь удалён',
                                     reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                         AdminMenuButtons.CLOSE))


# New words

@admin_router.callback_query(F.data == 'new_words_admin')
@admin_router.callback_query(F.data == 'back_to_sections_new_words_admin')
async def new_words_selecting_section_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(MessageTexts.SELECT_SECTION_WORDS.value,
                                     reply_markup=await keyboard_builder(1, *[button.value for button in
                                                                              NewWordsSections],
                                                                         AdminMenuButtons.MAIN_MENU))
    await state.set_state(AdminFSM.select_section_words)


@admin_router.callback_query(StateFilter(AdminFSM.select_section_words))
async def new_words_selected_section_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    section = callback.data
    subsections = await words_manager.get_subsection_names(section=section)
    buttons = [subsection for subsection in subsections]

    await callback.message.edit_text(
        MessageTexts.SELECT_SUBSECTION_WORDS.value,
        reply_markup=await keyboard_builder(1, *buttons,  # subsection buttons
                                            AdminMenuButtons.ADD_NEW_SECTION,
                                            AdminMenuButtons.MAIN_MENU,
                                            back_to_sections_new_words_admin=BasicButtons.BACK))
    await state.set_state(AdminFSM.select_subsection_words)
    await update_state_data(state, admin_section=section, admin_subsection=None)


@admin_router.callback_query(StateFilter(AdminFSM.select_subsection_words))
async def selected_subsection_new_words_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data != AdminMenuButtons.ADD_NEW_SECTION.value:
        await update_state_data(state, admin_subsection=callback.data)
        await state.set_state(AdminFSM.select_management_action_words)
        await callback.message.edit_text('Что хочешь делать?',
                                         reply_markup=await keyboard_builder(1, AdminMenuButtons.SEE_NEW_WORDS,
                                                                             AdminMenuButtons.ADD_NEW_WORDS,
                                                                             AdminMenuButtons.DEL_NEW_WORDS,
                                                                             AdminMenuButtons.EDIT_NEW_WORDS,
                                                                             AdminMenuButtons.MAIN_MENU,
                                                                             AdminMenuButtons.EXIT))
    elif callback.data == AdminMenuButtons.ADD_NEW_SECTION.value:
        await callback.message.edit_text("""Введи название нового раздела, обращай внимание на регистр букв
После добавления нового раздела нужно будет добавить хотя бы одно упражнение""",
                                         reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                             AdminMenuButtons.EXIT))
        await state.set_state(AdminFSM.adding_new_section)


@admin_router.message(StateFilter(AdminFSM.adding_new_section))
async def adding_new_section_to_words_admin(message: Message, state: FSMContext):
    new_subsection = message.text
    await update_state_data(state, admin_subsection=new_subsection)
    section = (await state.get_data()).get('admin_section')
    await message.answer(f'Добавить «{new_subsection}» в раздел «{section}»',
                         reply_markup=await keyboard_builder(1, AdminMenuButtons.YES,
                                                             AdminMenuButtons.EXIT))


@admin_router.callback_query(F.data == AdminMenuButtons.SEE_NEW_WORDS.value,
                             StateFilter(AdminFSM.select_management_action_words))
@admin_router.callback_query(F.data == AdminMenuButtons.ADD_NEW_WORDS.value,
                             StateFilter(AdminFSM.select_management_action_words))
@admin_router.callback_query(F.data == AdminMenuButtons.YES.value,
                             StateFilter(AdminFSM.adding_new_section))
@admin_router.callback_query(F.data == AdminMenuButtons.EDIT_NEW_WORDS.value,
                             StateFilter(AdminFSM.select_management_action_words))
@admin_router.callback_query(F.data == AdminMenuButtons.DEL_NEW_WORDS.value,
                             StateFilter(AdminFSM.select_management_action_words))
async def admin_words_management(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    subsection, section = data.get('admin_subsection'), data.get('admin_section')
    exercise_name = f'\"{section} - {subsection}\"'

    if section and callback.data == AdminMenuButtons.SEE_NEW_WORDS.value:
        result = await words_manager.get_new_words_exercises(subsection)
        if result:
            await callback.answer()
            await send_long_message(callback,
                                    f'Вот все {"идиомы" if section == "Idioms" else "слова"} из раздела\n{exercise_name}:\n{result}',
                                    reply_markup=await keyboard_builder(1, close_message_admin=AdminMenuButtons.CLOSE))
        else:
            await callback.answer()
            await callback.message.edit_text(f'В разделе \n{exercise_name} ещё нет упражнений',
                                             reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                                 AdminMenuButtons.EXIT))


    elif callback.data == AdminMenuButtons.ADD_NEW_WORDS.value or callback.data == AdminMenuButtons.YES.value:
        await callback.message.edit_text(
            f"""Введи {'идиому' if section == 'Idioms' else 'слово'} и ответ к нему для добавления в раздел\n{exercise_name}\n
В формате: \nСлово=+=Word
\nМожно отправить несколько упражнений, тогда каждое упражнение должно начинаться с новой строки
и сообщение должно содержать не более 4096 символов(лимит Telegram)""",
            reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                AdminMenuButtons.EXIT))
        await state.set_state(AdminFSM.adding_exercise_words)

    elif callback.data == AdminMenuButtons.EDIT_NEW_WORDS.value:
        await callback.message.edit_text(
            f'Введи номер {"идиомы" if section == "Idioms" else "слова"} для редактирования в разделе\n{exercise_name}\n',
            reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                AdminMenuButtons.EXIT))
        await state.set_state(AdminFSM.editing_exercise_words)


    elif callback.data == AdminMenuButtons.DEL_NEW_WORDS.value:
        await callback.message.edit_text(
            f"""Введи номер {"идиомы" if section == "Idioms" else "слова"} для удаления из\n{exercise_name}\n
Если нужно удалить одно упражнение - введи номер предложения,
если несколько - введи номера упражнений через запятую""",
            reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                AdminMenuButtons.EXIT))
        await state.set_state(AdminFSM.deleting_exercise_words)


@admin_router.message(StateFilter(AdminFSM.adding_exercise_words))  # ADD word
async def admin_adding_words(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        subsection, section = data.get('admin_subsection'), data.get('admin_section')
        sentences = message.text.split('\n')
        count_sentences = len(sentences)
        if count_sentences > 1:
            for group_sentences in sentences:
                russian, english = group_sentences.split('=+=')
                await words_manager.add_new_words_exercise(section=section, subsection=subsection, russian=russian,
                                                           english=english)
            await message.answer(
                f'✅Успешно добавлено {count_sentences} упражнений, можешь отправить ещё',
                reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU, AdminMenuButtons.EXIT))

        else:
            russian, english = message.text.split('=+=')
            await words_manager.add_new_words_exercise(section=section, subsection=subsection, russian=russian,
                                                       english=english)

            await message.answer('✅Упражнение успешно добавлено, можешь отправить ещё и я добавлю',
                                 reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                     AdminMenuButtons.EXIT))

    except Exception as e:
        await message.answer('❗️Что-то пошло не так, попробуй еще раз\n\nПроверь формат текста',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.EXIT))
        await message.answer(str(e))


@admin_router.message(StateFilter(AdminFSM.editing_exercise_words))  # EDIT words
async def admin_editing_words(message: Message, state: FSMContext):
    if message.text.isdigit():
        index = int(message.text)
        await update_state_data(state, index_words_edit=index)
        data = await state.get_data()
        subsection, section, index_testing_edit = data.get('admin_subsection'), data.get('admin_section'), data.get(
            'index_testing_edit')
        exercise_name = f'\"{section} - {subsection}\"'
        await message.answer(
            f"""Отлично, будем изменять \n{"идиому" if section == "Idioms" else "слово"} № {index_testing_edit}\nВ разделе {exercise_name} 
Введи предложение и ответ к нему в формате: \nEnglish sentence=+=Answer""")
        await state.set_state(AdminFSM.ready_to_edit_exercise_words)
    else:
        await message.answer('❌Что-то пошло не так, попробуй еще раз',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU, AdminMenuButtons.EXIT))


@admin_router.message(StateFilter(AdminFSM.ready_to_edit_exercise_words))  # EDIT words
async def admin_edit_words(message: Message, state: FSMContext):
    data = await state.get_data()
    subsection, section, index_words_edit = data.get('admin_subsection'), data.get('admin_section'), data.get(
        'index_words_edit')
    try:
        russian, english = message.text.split('=+=')
        await words_manager.edit_new_words_exercise(section=section, subsection=subsection, russian=russian,
                                                    english=english,
                                                    index=index_words_edit)
        await message.answer('✅Успешно изменено',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU))
        await state.set_state(AdminFSM.default)
        await update_state_data(state, admin_section=None, admin_subsection=None, index_words_edit=None)
    except Exception as e:
        await message.answer('❌Что-то пошло не так, попробуй еще раз',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.EXIT))


@admin_router.message(StateFilter(AdminFSM.deleting_exercise_words))  # DELETE
async def admin_deleting_words(message: Message, state: FSMContext):
    data = await state.get_data()
    subsection, section = str(data.get('admin_subsection')), str(data.get('admin_section'))
    exercise_name = f'«{section} - {subsection}»'
    indexes = []
    try:
        indexes = [int(num) for num in message.text.split(',')]
    except ValueError:
        await message.answer('❌Неправильный формат, попробуй еще раз ввести номер предложения',
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU, AdminMenuButtons.EXIT))

    if len(indexes) == 1:
        index = indexes[0]
        await message.answer(
            f"""✅Слово № {index}\n<b>Удалено</b> из раздела \n{exercise_name}""",
            reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU, AdminMenuButtons.EXIT))
        await words_manager.delete_new_words_exercise(section=section, subsection=subsection, index=index)
    elif len(indexes) > 1:
        await message.answer(f"""✅Слова № {str(indexes)}\n <b>Удалены</b> из раздела \n{exercise_name}""",
                             reply_markup=await keyboard_builder(1, AdminMenuButtons.MAIN_MENU, AdminMenuButtons.EXIT))
        for index in indexes:
            await words_manager.delete_new_words_exercise(section=section, subsection=subsection, index=index)


# Activity
@admin_router.callback_query(F.data == AdminMenuButtons.SEE_ACTIVITY_DAY.value)
@admin_router.callback_query(F.data == AdminMenuButtons.SEE_ACTIVITY_WEEK.value)
@admin_router.callback_query(F.data == AdminMenuButtons.SEE_ACTIVITY_MONTH.value)
async def admin_activity(callback: CallbackQuery):
    cbdata = callback.data
    today = date.today()
    if cbdata == AdminMenuButtons.SEE_ACTIVITY_DAY.value:
        stats = await daily_progress_manager.get(start_date=today, end_date=today)
        period = 'сегодня'
    elif cbdata == AdminMenuButtons.SEE_ACTIVITY_WEEK.value:
        stats = await daily_progress_manager.get(start_date=today - timedelta(days=7), end_date=today)
        period = 'неделю'
    elif cbdata == AdminMenuButtons.SEE_ACTIVITY_MONTH.value:
        stats = await daily_progress_manager.get(start_date=today - timedelta(days=30), end_date=today)
        period = 'месяц'

    info = f"""Статистика по всем пользователям за {period}:
Тестирование: <b>{stats.get('testing_exercises')}</b>
Изучение новых слов: <b>{stats.get('new_words')}</b>
Неправильные глаголы: <b>{stats.get('irregular_verbs')}</b>
Новых пользователей: <b>{stats.get('new_users')}</b>"""
    await callback.message.answer(info,
                                  reply_markup=await keyboard_builder(1, close_message_admin=AdminMenuButtons.CLOSE))


# Broadcast
@admin_router.callback_query((F.data == AdminMenuButtons.BROADCAST.value))
async def start_broadcast(callback: CallbackQuery):
    await callback.message.edit_text(text=AdminMenuButtons.BROADCAST.value,
                                     reply_markup=await keyboard_builder(
                                         1,
                                         AdminMenuButtons.ADD_BROADCAST,
                                         AdminMenuButtons.MAIN_MENU,
                                         AdminMenuButtons.CLOSE, args_go_first=False,
                                         del_scheduled_broadcast=AdminMenuButtons.DEL_BROADCASTS))


@admin_router.callback_query((F.data == 'del_scheduled_broadcast'))
async def delete_broadcast(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text('Ты уверен, что нужно удалить все запланированные рассылки?',
                                     reply_markup=await keyboard_builder(1, AdminMenuButtons.CLOSE,
                                                                         args_go_first=False,
                                                                         sure_delete_broadcast=AdminMenuButtons.YES))


@admin_router.callback_query((F.data == 'sure_delete_broadcast'))
async def sure_delete_broadcast(callback: CallbackQuery):
    await callback.answer()
    await delete_scheduled_broadcasts()
    await callback.message.edit_text('Все запланированные рассылки удалены',
                                     reply_markup=await keyboard_builder(1, AdminMenuButtons.CLOSE))


@admin_router.callback_query((F.data == AdminMenuButtons.ADD_BROADCAST.value))
async def add_broadcast_date_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("""Введи дату и время в формате\nHH:MM dd.mm.yyyy\nЧасовой пояс UTC+3(Мск)""")
    await state.set_state(AdminFSM.broadcasting_set_date_time)


@admin_router.message(StateFilter(AdminFSM.broadcasting_set_date_time))
async def adding_broadcast_date_time(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text, '%H:%M %d.%m.%Y')
        await state.update_data(broadcast_date_time=message.text)
        await state.set_state(AdminFSM.broadcasting_set_text)
        await message.delete()
        await message.answer(
            f'Хорошо, я сделаю рассылку\n{message.text}\n\nТеперь отправь мне текст, который нужно будет разослать')
    except Exception as e:
        await message.answer('Что-то пошло не так, введи еще раз в формате \nHH:MM dd.mm.yyyy')
        await message.answer(str(e))


@admin_router.message(StateFilter(AdminFSM.broadcasting_set_text))
async def adding_broadcast_text(message: Message, state: FSMContext):
    data = await state.get_data()
    date_time = datetime.strptime(data.get('broadcast_date_time'), '%H:%M %d.%m.%Y')
    text = message.text
    await schedule_broadcast(date_time=date_time, text=text)
    await message.answer('Отлично. Рассылка будет отправлена в указанное время')
    await state.set_state(AdminFSM.default)
