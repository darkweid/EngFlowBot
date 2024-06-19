from aiogram import Router, F
from config_data.config import Config, load_config
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from states import AdminFSM, LearningFSM
from db import ExerciseManager, UserProgressManager
from keyboards import *
from lexicon import *
from utils import message_to_admin, update_state_data

config: Config = load_config()
BOT_TOKEN: str = config.tg_bot.token
ADMINS: list = config.tg_bot.admin_ids

admin_router: Router = Router()
exercise_manager: ExerciseManager = ExerciseManager()
user_progress_manager: UserProgressManager = UserProgressManager()


@admin_router.message(Command(commands=["admin"]))
async def admin_command(message: Message, state: FSMContext):
    if str(message.from_user.id) in ADMINS:
        await message.answer('🔘 Привет, что будем делать? 🔘',
                             reply_markup=keyboard_builder(1, AdminMenuButtons.EXERCISES,
                                                           AdminMenuButtons.SEE_ACTIVITY_DAY,
                                                           AdminMenuButtons.SEE_ACTIVITY_WEEK,
                                                           AdminMenuButtons.USERS, AdminMenuButtons.EXIT))
        await state.set_state(AdminFSM.default)
    else:
        await message.answer('🚫 Вам сюда нельзя 🚫')


@admin_router.callback_query((F.data == AdminMenuButtons.MAIN_MENU.value))
async def admin_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('🔘 Привет, что будем делать? 🔘',
                                     reply_markup=keyboard_builder(1, AdminMenuButtons.EXERCISES,
                                                                   AdminMenuButtons.SEE_ACTIVITY_DAY,
                                                                   AdminMenuButtons.SEE_ACTIVITY_WEEK,
                                                                   AdminMenuButtons.USERS, AdminMenuButtons.EXIT))
    await state.set_state(AdminFSM.default)


@admin_router.callback_query((F.data == AdminMenuButtons.CLOSE.value))
@admin_router.callback_query((F.data == AdminMenuButtons.EXIT.value))
async def admin_exit(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer('До скорых встреч 👋')
    await state.set_state(LearningFSM.default)


@admin_router.callback_query((F.data == AdminMenuButtons.EXERCISES.value), StateFilter(AdminFSM.default))
@admin_router.callback_query((F.data == BasicButtons.BACK.value), StateFilter(AdminFSM.choose_section_testing))
async def admin_exercises(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Выбери группу упражнений:',
                                     reply_markup=keyboard_builder(1, AdminMenuButtons.MAIN_MENU, AdminMenuButtons.EXIT,
                                                                   args_go_first=False,
                                                                   tests_admin=AdminMenuButtons.TESTING,
                                                                   new_words_admin=AdminMenuButtons.NEW_WORDS,
                                                                   irr_verbs_admin=AdminMenuButtons.IRR_VERBS))


@admin_router.callback_query((F.data == BasicButtons.BACK.value), StateFilter(AdminFSM.choose_subsection_testing))
@admin_router.callback_query((F.data == 'tests_admin'))
async def admin_start_testing(callback: CallbackQuery, state: FSMContext):  # выбор раздела для прохождения тесте
    await callback.answer()
    await callback.message.edit_text('Выбери раздел тестов:', reply_markup=choose_section_testing_keyboard)
    await state.set_state(AdminFSM.choose_section_testing)


@admin_router.callback_query(StateFilter(AdminFSM.choose_section_testing))  # выбор ПОДраздела теста
async def admin_choosing_section_testing(callback: CallbackQuery, state: FSMContext):
    section = testing_section_mapping.get(callback.data)
    if section is None:
        await callback.answer()
        await callback.message.edit_text(MessageTexts.ERROR)
        await state.set_state(LearningFSM.default)
        return

    await callback.message.edit_text(
        MessageTexts.CHOOSE_SUBSECTION_TEST.value,
        reply_markup=keyboard_builder(1, *[button.value for button in section], BasicButtons.BACK,
                                      BasicButtons.MAIN_MENU))
    await state.set_state(AdminFSM.choose_subsection_testing)
    await update_state_data(state, admin_section=callback.data, admin_subsection=None)
    print(await state.get_data())


@admin_router.callback_query(
    StateFilter(AdminFSM.choose_subsection_testing))  # подраздел выбран, получен в callback
async def admin_choosing_subsection_testing(callback: CallbackQuery, state: FSMContext):
    admin_subsection = callback.data
    data = await state.get_data()
    admin_section = data.get('admin_section')
    await callback.answer()
    await callback.message.edit_text(
        f'Выбран раздел\n «{admin_section} - {admin_subsection}»\n\nЧто нужно сделать?',
        reply_markup=keyboard_builder(1, AdminMenuButtons.SEE_EXERCISES_TESTING,
                                      AdminMenuButtons.ADD_EXERCISE_TESTING,
                                      AdminMenuButtons.DEL_EXERCISE_TESTING,
                                      AdminMenuButtons.MAIN_MENU,
                                      AdminMenuButtons.EXIT))
    await update_state_data(state, admin_subsection=admin_subsection)
    print(await state.get_data())
    await state.set_state(AdminFSM.choose_management_action_testing)


@admin_router.callback_query(F.data == AdminMenuButtons.SEE_EXERCISES_TESTING.value)
@admin_router.callback_query(F.data == AdminMenuButtons.ADD_EXERCISE_TESTING.value)
@admin_router.callback_query(F.data == AdminMenuButtons.DEL_EXERCISE_TESTING.value)
async def admin_testing_management(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    subsection = data.get('admin_subsection')
    section = data.get('admin_section')
    if section and callback.data == AdminMenuButtons.SEE_EXERCISES_TESTING.value:
        result = await exercise_manager.get_testing_exercises(subsection)
        if result:
            await send_long_message(callback, f'Вот все предложения из раздела\n\"{section} - {subsection}\":\n{result}',
                                    reply_markup=keyboard_builder(1, AdminMenuButtons.CLOSE))
        else:
            await callback.message.edit_text(f'В разделе \n\"{section} - {subsection}\" ещё нет упражнений',
                                             reply_markup=keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                           AdminMenuButtons.EXIT))
    elif callback.data == AdminMenuButtons.ADD_EXERCISE_TESTING.value:
        await callback.message.edit_text(f"""Введи предложения для добавления в раздел\n\"{section} - {subsection}\"\n
В формате: \nEnglish sentence=+=Answer
\nМожно отправить несколько упражнений, тогда каждое упражнение должно начинаться с новой строки
и сообщение должно содержать не более 4096 символов(лимит Telegram)""",
                                         reply_markup=keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                       AdminMenuButtons.EXIT))
        await state.set_state(AdminFSM.adding_exercise_testing)

    elif callback.data == AdminMenuButtons.DEL_EXERCISE_TESTING.value:
        await callback.message.edit_text(f'Введи номер предложения для удаления из\n\"{section}\"',
                                         reply_markup=keyboard_builder(1, AdminMenuButtons.MAIN_MENU,
                                                                       AdminMenuButtons.EXIT))
        await state.set_state(AdminFSM.deleting_exercise_testing)


@admin_router.message(StateFilter(AdminFSM.adding_exercise_testing))
async def admin_adding_sentence_grammar(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        subsection = data.get('admin_subsection')
        section = data.get('admin_section')
        sentences = message.text.split('\n')
        count_sentences = len(sentences)
        print(sentences)
        print(count_sentences)
        if count_sentences > 1:
            for group_sentences in sentences:
                test, answer = group_sentences.split('=+=')
                await exercise_manager.add_testing_exercise(section=section, subsection=subsection, test=test, answer=answer)
            await message.answer(
                f'✅Успешно добавлено {count_sentences} упражнений, можешь отправить ещё',
                reply_markup=keyboard_builder(1, AdminMenuButtons.EXIT))

        else:
            test, answer = message.text.split('=+=')
            await exercise_manager.add_testing_exercise(section=section, subsection=subsection, test=test, answer=answer)

            await message.answer('✅Упражнение успешно добавлено, можешь отправить ещё и я добавлю',
                                 reply_markup=keyboard_builder(1, AdminMenuButtons.EXIT))

    except Exception as e:
        print('\n\n\n\n' + str(e) + '\n\n\n\n')
        await message.answer('❗️Что-то пошло не так, попробуй еще раз\n\nПроверь формат текста',
                             reply_markup=keyboard_builder(1, AdminMenuButtons.EXIT))
        await message.answer(str(e))


async def send_long_message(callback, text, max_length=4000, **kwargs):
    paragraphs = text.split('\n')
    current_message = ""

    for paragraph in paragraphs:
        if len(current_message) + len(paragraph) < max_length:
            current_message += paragraph + '\n'
        else:
            await callback.message.answer(current_message, **kwargs)
            current_message = paragraph + '\n'
    print(len(current_message))
    if current_message:
        await callback.message.answer(current_message, **kwargs)
