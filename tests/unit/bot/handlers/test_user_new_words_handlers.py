from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.handlers.user_new_words_handlers import (
    add_new_words_confirm,
    add_new_words_selected_section,
    correct_answer_learning_words,
    learn_new_words,
    not_correct_answer_learning_words,
    start_new_words,
    stats_new_words,
)
from bot.states import WordsLearningFSM
from tests.helpers import FakeCallback, FakeState


def _learning_exercise():
    return {
        "russian": "Дом",
        "english": "House",
        "section": "Vocabulary",
        "subsection": "Travel",
        "exercise_id": 1,
        "options": ["A", "B", "C"],
    }


async def test_start_new_words_toggles_hard_mode_in_state():
    state = FakeState()

    with patch(
        "bot.handlers.user_new_words_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    ):
        await start_new_words(FakeCallback(data="turn_on_hard_mode_words"), state)
        await start_new_words(FakeCallback(data="turn_off_hard_mode_words"), state)

    assert state._data["hard_mode_words"] is False
    assert state.set_state.await_count == 2


async def test_learn_new_words_no_words_today_does_not_enter_answer_state():
    callback = FakeCallback(user_id=123)
    state = FakeState()
    learning_service = SimpleNamespace(
        get_count_all_exercises_for_today_by_user=AsyncMock(return_value=0),
        get_count_active_learning_exercises=AsyncMock(return_value=0),
        get_count_learned_exercises=AsyncMock(return_value=0),
    )

    with (
        patch(
            "bot.handlers.user_new_words_handlers.random.choice", return_value="Right"
        ),
        patch(
            "bot.handlers.user_new_words_handlers.keyboard_builder",
            new=AsyncMock(return_value="kb"),
        ),
    ):
        await learn_new_words(callback, state, learning_service)

    callback.message.answer.assert_awaited_once()
    state.set_state.assert_not_awaited()


async def test_learn_new_words_default_mode_stores_exercise_and_shows_options():
    callback = FakeCallback(user_id=123)
    state = FakeState({"hard_mode_words": False})
    learning_service = SimpleNamespace(
        get_count_all_exercises_for_today_by_user=AsyncMock(return_value=2),
        get_count_active_learning_exercises=AsyncMock(return_value=2),
        get_count_learned_exercises=AsyncMock(return_value=5),
        get_random_word_exercise=AsyncMock(return_value=_learning_exercise()),
    )

    with (
        patch(
            "bot.handlers.user_new_words_handlers.keyboard_builder",
            new=AsyncMock(return_value="kb"),
        ),
        patch(
            "bot.handlers.user_new_words_handlers.keyboard_builder_words_learning",
            new=AsyncMock(return_value="kbw"),
        ) as words_keyboard,
        patch(
            "bot.handlers.user_new_words_handlers.word_with_youglish_link",
            return_value="House(link)",
        ),
    ):
        await learn_new_words(callback, state, learning_service)

    words_keyboard.assert_awaited_once_with(1, correct="Дом", options=["A", "B", "C"])
    state.set_state.assert_awaited_once_with(WordsLearningFSM.in_process)
    assert state._data["words_section"] == "Vocabulary"
    assert state._data["words_exercise_id"] == 1


async def test_learn_new_words_hard_mode_first_step_skips_options_keyboard():
    callback = FakeCallback(user_id=123)
    state = FakeState({"hard_mode_words": True})
    learning_service = SimpleNamespace(
        get_count_all_exercises_for_today_by_user=AsyncMock(return_value=2),
        get_count_active_learning_exercises=AsyncMock(return_value=2),
        get_count_learned_exercises=AsyncMock(return_value=5),
        get_random_word_exercise=AsyncMock(return_value=_learning_exercise()),
    )

    with (
        patch(
            "bot.handlers.user_new_words_handlers.keyboard_builder",
            new=AsyncMock(return_value="kb"),
        ),
        patch(
            "bot.handlers.user_new_words_handlers.keyboard_builder_words_learning",
            new=AsyncMock(return_value="kbw"),
        ) as words_keyboard,
        patch(
            "bot.handlers.user_new_words_handlers.word_with_youglish_link",
            return_value="House(link)",
        ),
    ):
        await learn_new_words(callback, state, learning_service)

    words_keyboard.assert_not_awaited()
    state.set_state.assert_awaited_once_with(WordsLearningFSM.in_process)


async def test_correct_answer_updates_success_progress_and_daily_stats():
    callback = FakeCallback(user_id=123)
    state = FakeState(
        {
            "words_section": "Vocabulary",
            "words_subsection": "Travel",
            "words_exercise_id": 1,
        }
    )
    learning_service = SimpleNamespace(
        set_progress=AsyncMock(),
        get_count_all_exercises_for_today_by_user=AsyncMock(return_value=0),
        get_count_active_learning_exercises=AsyncMock(return_value=0),
        get_count_learned_exercises=AsyncMock(return_value=0),
    )
    daily_statistics_service = SimpleNamespace(update=AsyncMock())

    with (
        patch(
            "bot.handlers.user_new_words_handlers.random.choice", return_value="Right"
        ),
        patch("bot.handlers.user_new_words_handlers.asyncio.sleep", new=AsyncMock()),
        patch(
            "bot.handlers.user_new_words_handlers.keyboard_builder",
            new=AsyncMock(return_value="kb"),
        ),
    ):
        await correct_answer_learning_words(
            callback,
            state,
            learning_service,
            daily_statistics_service,
        )

    learning_service.set_progress.assert_awaited_once_with(
        user_id=123,
        section="Vocabulary",
        subsection="Travel",
        exercise_id=1,
        success=True,
    )
    daily_statistics_service.update.assert_awaited_once_with("new_words")


async def test_wrong_answer_updates_failure_progress_and_daily_stats():
    callback = FakeCallback(user_id=123)
    state = FakeState(
        {
            "word_russian": "Дом",
            "word_english": "House",
            "words_section": "Vocabulary",
            "words_subsection": "Travel",
            "words_exercise_id": 1,
        }
    )
    learning_service = SimpleNamespace(
        set_progress=AsyncMock(),
        get_count_all_exercises_for_today_by_user=AsyncMock(return_value=0),
        get_count_active_learning_exercises=AsyncMock(return_value=0),
        get_count_learned_exercises=AsyncMock(return_value=0),
    )
    daily_statistics_service = SimpleNamespace(update=AsyncMock())

    with (
        patch(
            "bot.handlers.user_new_words_handlers.random.choice", return_value="Right"
        ),
        patch("bot.handlers.user_new_words_handlers.asyncio.sleep", new=AsyncMock()),
        patch(
            "bot.handlers.user_new_words_handlers.keyboard_builder",
            new=AsyncMock(return_value="kb"),
        ),
    ):
        await not_correct_answer_learning_words(
            callback,
            state,
            learning_service,
            daily_statistics_service,
        )

    learning_service.set_progress.assert_awaited_once_with(
        user_id=123,
        section="Vocabulary",
        subsection="Travel",
        exercise_id=1,
        success=False,
    )
    daily_statistics_service.update.assert_awaited_once_with("new_words")


async def test_add_new_words_selected_section_hides_already_added_subsections():
    callback = FakeCallback(data="Vocabulary")
    state = FakeState()
    learning_service = SimpleNamespace(
        get_added_subsections_by_user=AsyncMock(return_value=["Travel"])
    )
    new_words_service = SimpleNamespace(
        get_subsection_names=AsyncMock(return_value=["Travel", "Food"])
    )

    with patch(
        "bot.handlers.user_new_words_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    ) as keyboard_builder:
        await add_new_words_selected_section(
            callback,
            state,
            learning_service,
            new_words_service,
        )

    assert "Food" in keyboard_builder.await_args.args
    assert "Travel" not in keyboard_builder.await_args.args
    state.set_state.assert_awaited_once_with(WordsLearningFSM.selecting_subsection)
    assert state._data["section"] == "Vocabulary"


async def test_add_new_words_confirm_adds_words_only_on_positive_answer():
    learning_service = SimpleNamespace(add_words_to_learning=AsyncMock())

    with (
        patch(
            "bot.handlers.user_new_words_handlers.keyboard_builder",
            new=AsyncMock(return_value="kb"),
        ),
        patch(
            "bot.handlers.user_new_words_handlers.send_message_to_admin",
            new=AsyncMock(),
        ) as notify_admin,
    ):
        await add_new_words_confirm(
            FakeCallback(data="add_words", user_id=123, username="user"),
            FakeState({"section": "Vocabulary", "subsection": "Travel"}),
            learning_service,
        )
        await add_new_words_confirm(
            FakeCallback(data="do_not_add_words", user_id=123, username="user"),
            FakeState({"section": "Vocabulary", "subsection": "Food"}),
            learning_service,
        )

    learning_service.add_words_to_learning.assert_awaited_once_with(
        section="Vocabulary",
        subsection="Travel",
        user_id=123,
    )
    notify_admin.assert_awaited_once()


async def test_stats_new_words_renders_empty_short_and_long_paths():
    with patch(
        "bot.handlers.user_new_words_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    ):
        await stats_new_words(
            FakeCallback(),
            SimpleNamespace(get_user_stats=AsyncMock(return_value={})),
        )

    short_callback = FakeCallback()
    short_stats = {
        "Travel": {
            "learned": 1,
            "for_today_learning": 2,
            "active_learning": 3,
            "total_words_in_subsection": 10,
            "success_rate": 75.0,
        },
    }
    with patch(
        "bot.handlers.user_new_words_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    ):
        await stats_new_words(
            short_callback,
            SimpleNamespace(get_user_stats=AsyncMock(return_value=short_stats)),
        )
    assert "Travel" in short_callback.message.edit_text.await_args.args[0]

    long_stats = {
        f"sub_{index}": {
            "learned": 0,
            "for_today_learning": 0,
            "active_learning": 0,
            "total_words_in_subsection": 0,
            "success_rate": 0.0,
        }
        for index in range(40)
    }
    with (
        patch(
            "bot.handlers.user_new_words_handlers.keyboard_builder",
            new=AsyncMock(return_value="kb"),
        ),
        patch(
            "bot.handlers.user_new_words_handlers.send_long_message", new=AsyncMock()
        ) as send_long,
    ):
        await stats_new_words(
            FakeCallback(),
            SimpleNamespace(get_user_stats=AsyncMock(return_value=long_stats)),
        )

    send_long.assert_awaited_once()
