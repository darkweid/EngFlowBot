import asyncio
import logging
import random

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.keyboards import keyboard_builder, keyboard_builder_words_learning
from bot.lexicon import (
    BasicButtons,
    MainMenuButtons,
    MessageTexts,
    NewWordsSections,
    list_right_answers,
)
from bot.services.daily_statistics import DailyStatisticsService
from bot.services.new_words import NewWordsService
from bot.services.user_words_learning import UserWordsLearningService
from bot.states import WordsLearningFSM
from bot.utils import (
    get_word_declension,
    send_long_message,
    send_message_to_admin,
    update_state_data,
    word_with_youglish_link,
)

user_new_words_router: Router = Router()


@user_new_words_router.callback_query(F.data == MainMenuButtons.NEW_WORDS)
@user_new_words_router.callback_query(F.data == "back_to_main_menu_new_words")
@user_new_words_router.callback_query(F.data == "turn_off_hard_mode_words")
@user_new_words_router.callback_query(F.data == "turn_on_hard_mode_words")
async def start_new_words(
    callback: CallbackQuery,
    state: FSMContext,
):
    if callback.data == "turn_off_hard_mode_words":
        await callback.answer("❌Сложный режим изучения слов выключен", show_alert=True)
        await update_state_data(state, hard_mode_words=False)
    elif callback.data == "turn_on_hard_mode_words":
        await callback.answer("✅Сложный режим изучения слов включен", show_alert=True)
        await update_state_data(state, hard_mode_words=True)

    await callback.answer()
    user_data = await state.get_data()
    hard_mode = user_data.get("hard_mode_words")

    if hard_mode:
        keyboard = await keyboard_builder(
            1,
            BasicButtons.MAIN_MENU,
            args_go_first=False,
            learn_new_words=BasicButtons.LEARN_ADDED_WORDS,
            turn_off_hard_mode_words=BasicButtons.TURN_OFF_HARD_MODE,
            # Turn OFF hard mode button
            add_new_words=BasicButtons.ADD_WORDS,
            progress_new_words=BasicButtons.NEW_WORDS_PROGRESS,
        )
    else:
        keyboard = await keyboard_builder(
            1,
            BasicButtons.MAIN_MENU,
            args_go_first=False,
            learn_new_words=BasicButtons.LEARN_ADDED_WORDS,
            turn_on_hard_mode_words=BasicButtons.TURN_ON_HARD_MODE,
            # Turn ON hard mode button
            add_new_words=BasicButtons.ADD_WORDS,
            progress_new_words=BasicButtons.NEW_WORDS_PROGRESS,
        )

    await callback.message.edit_text("Выбирай:", reply_markup=keyboard)
    await state.set_state(WordsLearningFSM.default)


@user_new_words_router.callback_query(F.data == "rules_new_words")
async def rules_new_words(
    callback: CallbackQuery,
):
    await callback.answer()
    await callback.message.edit_text(
        MessageTexts.NEW_WORDS_RULES,
        reply_markup=await keyboard_builder(
            1,
            more_about_sr=BasicButtons.MORE_ABOUT_SPACED_REPETITION,
            close_rules_new_words=BasicButtons.CLOSE,
        ),
    )


@user_new_words_router.callback_query(F.data == "more_about_sr")
async def more_about_spaced_repetition_new_words(
    callback: CallbackQuery,
):
    await callback.answer()
    await callback.message.edit_text(
        MessageTexts.ABOUT_SPACED_REPETITION,
        reply_markup=await keyboard_builder(
            1, close_rules_new_words=BasicButtons.CLOSE
        ),
    )


@user_new_words_router.callback_query(F.data == "close_rules_new_words")
async def rules_new_words(
    callback: CallbackQuery,
):
    await callback.answer()
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logging.error(f"Failed to delete message: {e}")


async def send_no_words_for_today_message(
    callback: CallbackQuery,
    user_words_learning_service: UserWordsLearningService,
):
    user_id = callback.from_user.id
    count_active_exercises = (
        await user_words_learning_service.get_count_active_learning_exercises(
            user_id=user_id
        )
    )
    learned_words = await user_words_learning_service.get_count_learned_exercises(
        user_id=user_id
    )
    message_text = (
        f"{random.choice(list_right_answers)}🔥\n"
        f"{MessageTexts.NO_WORDS_TO_LEARN_TODAY}\n"
        f"Cлов в активном изучении: {count_active_exercises}\n"
        f"Изучено всего: {learned_words}"
    )
    await callback.message.answer(
        message_text,
        reply_markup=await keyboard_builder(
            1, BasicButtons.MAIN_MENU, BasicButtons.CLOSE
        ),
    )


async def send_hello_message_new_words(
    callback: CallbackQuery,
    user_id: int,
    user_words_learning_service: UserWordsLearningService,
):
    count_active_exercises = (
        await user_words_learning_service.get_count_active_learning_exercises(
            user_id=user_id
        )
    )
    count_exercises_today = (
        await user_words_learning_service.get_count_all_exercises_for_today_by_user(
            user_id=user_id
        )
    )
    learned_words = await user_words_learning_service.get_count_learned_exercises(
        user_id=user_id
    )
    message_text = (
        f"{MessageTexts.NEW_WORDS_HELLO}\n"
        f"Cлов в активном изучении: {count_active_exercises}\n"
        f"Для изучения сегодня: {count_exercises_today}\n"
        f"Изучено всего: {learned_words}"
    )
    keyboard = await keyboard_builder(
        1, rules_new_words=BasicButtons.RULES, close_rules_new_words=BasicButtons.CLOSE
    )
    await callback.message.edit_text(message_text, reply_markup=keyboard)


@user_new_words_router.callback_query(F.data == "learn_new_words")
async def learn_new_words(
    callback: CallbackQuery,
    state: FSMContext,
    user_words_learning_service: UserWordsLearningService,
    hello_message: bool = True,
    from_hard_mode: bool = False,
):
    await callback.answer()
    user_id = callback.from_user.id
    count_user_exercises_for_today = (
        await user_words_learning_service.get_count_all_exercises_for_today_by_user(
            user_id=user_id
        )
    )

    # No words for learning today
    if count_user_exercises_for_today == 0:
        await send_no_words_for_today_message(callback, user_words_learning_service)

    # The user has words for learning today
    else:
        if hello_message:
            await send_hello_message_new_words(
                callback, user_id, user_words_learning_service
            )

        # The user has already pressed button "I know this word" -> User has word to answer
        # -> get word data from state data warehouse
        if from_hard_mode:
            user_data = await state.get_data()
            word_russian, word_english, word_id, options = (
                user_data.get("word_russian"),
                user_data.get("word_english"),
                user_data.get("exercise_id"),
                user_data.get("options"),
            )

        # The user doesn't have word to answer -> get random word data
        else:
            exercise = await user_words_learning_service.get_random_word_exercise(
                user_id=user_id
            )
            word_russian, word_english, word_id, options = (
                exercise["russian"],
                exercise["english"],
                exercise["exercise_id"],
                exercise["options"],
            )
            await update_state_data(
                state,
                words_section=exercise["section"],
                words_subsection=exercise["subsection"],
                words_exercise_id=exercise["exercise_id"],
                word_russian=word_russian,
                word_english=word_english,
                options=options,
            )
        hard_mode_user = (await state.get_data()).get("hard_mode_words")

        # The user received a new word, them must decide whether them knows it or not
        if hard_mode_user and not from_hard_mode:
            await callback.message.answer(
                text=f"{word_with_youglish_link(word_english)}",
                reply_markup=await keyboard_builder(
                    1,
                    i_know_word=BasicButtons.I_KNOW,
                    i_dont_know_word=BasicButtons.I_DONT_KNOW,
                ),
            )

        # The user came from hard_mode, where them pressed "I know the word" button
        elif from_hard_mode:
            await callback.message.edit_text(
                text=f"{word_with_youglish_link(word_english)}",
                reply_markup=await keyboard_builder_words_learning(
                    1, correct=word_russian, options=options
                ),
            )

        # The user came from default mode
        else:
            await callback.message.answer(
                text=f"{word_with_youglish_link(word_english)}",
                reply_markup=await keyboard_builder_words_learning(
                    1, correct=word_russian, options=options
                ),
            )

        await state.set_state(WordsLearningFSM.in_process)


@user_new_words_router.callback_query(
    F.data == "i_know_word", StateFilter(WordsLearningFSM.in_process)
)
async def i_know_word_learning_words(
    callback: CallbackQuery,
    state: FSMContext,
    user_words_learning_service: UserWordsLearningService,
):
    await learn_new_words(
        callback,
        state,
        user_words_learning_service,
        hello_message=False,
        from_hard_mode=True,
    )


@user_new_words_router.callback_query(
    F.data == "correct", StateFilter(WordsLearningFSM.in_process)
)
async def correct_answer_learning_words(
    callback: CallbackQuery,
    state: FSMContext,
    user_words_learning_service: UserWordsLearningService,
    daily_statistics_service: DailyStatisticsService,
):
    await callback.answer()
    await callback.message.edit_text(f"🔥🔥🔥{random.choice(list_right_answers)}")
    await asyncio.sleep(0.7)
    await callback.message.delete()
    user_id = callback.from_user.id
    user_data = await state.get_data()
    section, subsection, exercise_id = (
        user_data.get("words_section"),
        user_data.get("words_subsection"),
        user_data.get("words_exercise_id"),
    )
    await user_words_learning_service.set_progress(
        user_id=user_id,
        section=section,
        subsection=subsection,
        exercise_id=exercise_id,
        success=True,
    )

    await learn_new_words(
        callback, state, user_words_learning_service, hello_message=False
    )
    await daily_statistics_service.update("new_words")


@user_new_words_router.callback_query(
    F.data == "not_correct", StateFilter(WordsLearningFSM.in_process)
)
@user_new_words_router.callback_query(
    F.data == "i_dont_know_word", StateFilter(WordsLearningFSM.in_process)
)
async def not_correct_answer_learning_words(
    callback: CallbackQuery,
    state: FSMContext,
    user_words_learning_service: UserWordsLearningService,
    daily_statistics_service: DailyStatisticsService,
):
    user_data = await state.get_data()
    word_russian, word_english = user_data.get("word_russian"), user_data.get(
        "word_english"
    )

    await callback.message.edit_text(f"😕\n{word_russian} — {word_english}")
    await asyncio.sleep(1)
    await callback.message.edit_text(f"{word_russian} — {word_english}")
    await asyncio.sleep(0.2)
    data = await state.get_data()
    user_id = callback.from_user.id
    section, subsection, exercise_id = (
        data.get("words_section"),
        data.get("words_subsection"),
        data.get("words_exercise_id"),
    )
    await user_words_learning_service.set_progress(
        user_id=user_id,
        section=section,
        subsection=subsection,
        exercise_id=exercise_id,
        success=False,
    )
    await learn_new_words(
        callback, state, user_words_learning_service, hello_message=False
    )
    await daily_statistics_service.update("new_words")


@user_new_words_router.callback_query(F.data == "add_new_words")
@user_new_words_router.callback_query(F.data == "back_to_sections")
async def add_new_words_selecting_section(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()
    await callback.message.edit_text(
        MessageTexts.SELECT_SECTION_WORDS,
        reply_markup=await keyboard_builder(
            1,
            *[button for button in NewWordsSections],
            back_to_main_menu_new_words=BasicButtons.BACK,
        ),
    )
    await state.set_state(WordsLearningFSM.add_words_to_learn)


@user_new_words_router.callback_query(StateFilter(WordsLearningFSM.add_words_to_learn))
async def add_new_words_selected_section(
    callback: CallbackQuery,
    state: FSMContext,
    user_words_learning_service: UserWordsLearningService,
    new_words_service: NewWordsService,
):
    section = callback.data
    user_id = callback.from_user.id
    user_added_subsections = (
        await user_words_learning_service.get_added_subsections_by_user(user_id=user_id)
    )
    subsections = await new_words_service.get_subsection_names(section=section)
    buttons = [
        subsection
        for subsection in subsections
        if subsection not in user_added_subsections
    ]
    if len(buttons) > 0:
        await callback.answer()
        await callback.message.edit_text(
            MessageTexts.SELECT_SUBSECTION_WORDS,
            reply_markup=await keyboard_builder(
                1,
                *buttons,  # subsection buttons
                back_to_sections=BasicButtons.BACK,
                back_to_main_menu_new_words=BasicButtons.MAIN_MENU_NEW_WORDS,
            ),
        )
        await state.set_state(WordsLearningFSM.selecting_subsection)
        await update_state_data(state, section=section, subsection=None)
    elif len(buttons) == 0:
        await callback.answer("В этом разделе больше нет тем для добавления 🧐")


@user_new_words_router.callback_query(
    StateFilter(WordsLearningFSM.selecting_subsection)
)
async def add_new_words_selecting_subsection(
    callback: CallbackQuery,
    state: FSMContext,
    new_words_service: NewWordsService,
):
    await callback.answer()
    user_data = await state.get_data()
    section = user_data.get("section")
    subsection = callback.data
    quantity = await new_words_service.get_count_new_words_exercises_in_subsection(
        section=section, subsection=subsection
    )
    word_declension = get_word_declension(count=quantity, word="слово")
    await callback.message.edit_text(
        f"""«{subsection}»\n
В теме {word_declension}
Добавить в изучаемые?""",
        reply_markup=await keyboard_builder(
            1,
            add_words=BasicButtons.YES,
            do_not_add_words=BasicButtons.NO,
            back_to_sections=BasicButtons.BACK,
            back_to_main_menu_new_words=BasicButtons.MAIN_MENU_NEW_WORDS,
        ),
    )
    await state.set_state(WordsLearningFSM.selected_subsection)
    await update_state_data(state, subsection=subsection)


@user_new_words_router.callback_query(StateFilter(WordsLearningFSM.selected_subsection))
async def add_new_words_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    user_words_learning_service: UserWordsLearningService,
):
    await callback.answer()
    user_data = await state.get_data()
    section, subsection, user_id = (
        user_data.get("section"),
        user_data.get("subsection"),
        callback.from_user.id,
    )
    user_answer = callback.data

    if user_answer == "add_words":
        await user_words_learning_service.add_words_to_learning(
            section=section, subsection=subsection, user_id=user_id
        )
        await callback.message.edit_text(
            "Добавлено",
            reply_markup=await keyboard_builder(
                1,
                learn_new_words=BasicButtons.LEARN_ADDED_WORDS,
                back_to_main_menu_new_words=BasicButtons.MAIN_MENU_NEW_WORDS,
            ),
        )
        username = callback.from_user.username or callback.from_user.full_name
        await send_message_to_admin(text=f"""Пользователь @{username} добавил себе
набор слов «{section} – {subsection}»""")

    elif user_answer == "do_not_add_words":
        await callback.message.edit_text(
            "Слова не добавлены",
            reply_markup=await keyboard_builder(
                1, back_to_main_menu_new_words=BasicButtons.MAIN_MENU_NEW_WORDS
            ),
        )
        await update_state_data(state, section=None, subsection=None)


@user_new_words_router.callback_query(F.data == "progress_new_words")
async def stats_new_words(
    callback: CallbackQuery,
    user_words_learning_service: UserWordsLearningService,
):
    await callback.answer()
    user_id = callback.from_user.id
    stats = await user_words_learning_service.get_user_stats(user_id=user_id)
    stats_text = ""
    for subsection, data in stats.items():
        if subsection.isdigit():
            subsection = "Personal Words"
        learned = data["learned"]
        for_today_learning = data["for_today_learning"]
        total_words_in_subsection = data["total_words_in_subsection"]
        active_learning = data["active_learning"]
        success_rate = data["success_rate"]
        stats_text += (
            f"Тема <b>«{subsection}»</b>\n"
            f"Для изучения сегодня: {for_today_learning}\n"
            f"Всего слов в теме: {total_words_in_subsection}\n"
            f"В активном изучении: {active_learning}\n"
            f"Изучено: {learned}\n"
            f"Правильных ответов: {success_rate:.0f}%\n\n"
        )
    if len(stats_text) == 0:
        await callback.message.edit_text(
            "У тебя еще нет статистики в изучении слов",
            reply_markup=await keyboard_builder(
                1, back_to_main_menu_new_words=BasicButtons.BACK
            ),
        )
    elif len(stats_text) > 4000:
        await send_long_message(
            callback=callback,
            text=stats_text,
            delimiter="\n\n",
            reply_markup=await keyboard_builder(1, close_message=BasicButtons.CLOSE),
        )
    else:
        await callback.message.edit_text(
            stats_text,
            reply_markup=await keyboard_builder(
                1, back_to_main_menu_new_words=BasicButtons.BACK
            ),
        )
