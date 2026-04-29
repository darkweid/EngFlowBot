from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.handlers.user_testing_handlers import (
    choosing_section_testing,
    chose_subsection_testing,
    in_process_testing,
    see_answer_testing,
    start_again_testing,
)
from bot.lexicon import MessageTexts
from bot.states import TestingFSM
from tests.helpers import FakeCallback, FakeMessage, FakeState


def make_state():
    return FakeState(
        {
            "section": "Grammar",
            "subsection": "Present Simple",
            "current_id": 7,
            "current_answer": "Do not",
        }
    )


async def test_choosing_section_stores_section_and_lists_service_subsections():
    callback = FakeCallback(data="Grammar")
    state = FakeState()
    testing_service = SimpleNamespace(
        get_subsection_names=AsyncMock(return_value=["Present Simple"])
    )

    with patch(
        "bot.handlers.user_testing_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    ):
        await choosing_section_testing(callback, state, testing_service)

    testing_service.get_subsection_names.assert_awaited_once_with(section="Grammar")
    state.set_state.assert_awaited_once_with(TestingFSM.selecting_subsection)
    assert state._data["section"] == "Grammar"
    assert state._data["subsection"] is None


async def test_chose_subsection_serves_exercise_and_saves_answer_state():
    callback = FakeCallback(user_id=123)
    state = FakeState({"section": "Grammar", "subsection": "Present Simple"})
    testing_service = SimpleNamespace(
        get_random_testing_exercise=AsyncMock(return_value=("Q?", "answer", 5))
    )
    user_progress_service = SimpleNamespace(
        get_counts_completed_exercises_testing=AsyncMock()
    )

    await chose_subsection_testing(
        callback,
        state,
        testing_service,
        user_progress_service,
    )

    testing_service.get_random_testing_exercise.assert_awaited_once_with(
        section="Grammar",
        subsection="Present Simple",
        user_id=123,
    )
    callback.message.answer.assert_awaited_once_with("Q?")
    state.set_state.assert_awaited_once_with(TestingFSM.in_process)
    assert state._data["current_answer"] == "answer"
    assert state._data["current_id"] == 5


async def test_chose_subsection_renders_completion_when_no_exercises_left():
    callback = FakeCallback()
    state = FakeState({"section": "Grammar", "subsection": "Present Simple"})
    testing_service = SimpleNamespace(
        get_random_testing_exercise=AsyncMock(return_value=None)
    )
    user_progress_service = SimpleNamespace(
        get_counts_completed_exercises_testing=AsyncMock(return_value=(1, 2, 5))
    )

    with patch(
        "bot.handlers.user_testing_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    ):
        await chose_subsection_testing(
            callback,
            state,
            testing_service,
            user_progress_service,
        )

    text = callback.message.answer.await_args.args[0]
    assert MessageTexts.ALL_EXERCISES_COMPLETED in text
    state.set_state.assert_not_awaited()


async def test_in_process_accepts_correct_answer_ignoring_case_and_spaces():
    message = FakeMessage(text="do not", user_id=123)
    state = make_state()
    testing_service = SimpleNamespace(
        get_random_testing_exercise=AsyncMock(return_value=("Next?", "works", 8))
    )
    user_progress_service = SimpleNamespace(
        mark_exercise_completed=AsyncMock(return_value=True),
        get_counts_completed_exercises_testing=AsyncMock(),
    )
    daily_statistics_service = SimpleNamespace(update=AsyncMock())

    with patch(
        "bot.handlers.user_testing_handlers.random.choice", return_value="Right"
    ):
        await in_process_testing(
            message,
            state,
            testing_service,
            user_progress_service,
            daily_statistics_service,
        )

    user_progress_service.mark_exercise_completed.assert_awaited_once_with(
        exercise_type="Testing",
        section="Grammar",
        subsection="Present Simple",
        exercise_id=7,
        user_id=123,
        success=True,
    )
    daily_statistics_service.update.assert_awaited_once_with("testing_exercises")
    assert state._data["current_test"] == "Next?"
    assert state._data["current_answer"] == "works"
    assert state._data["current_id"] == 8


async def test_in_process_marks_wrong_answer_without_loading_next_exercise():
    message = FakeMessage(text="wrong", user_id=123)
    state = make_state()
    testing_service = SimpleNamespace(get_random_testing_exercise=AsyncMock())
    user_progress_service = SimpleNamespace(mark_exercise_completed=AsyncMock())
    daily_statistics_service = SimpleNamespace(update=AsyncMock())

    with patch(
        "bot.handlers.user_testing_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    ):
        await in_process_testing(
            message,
            state,
            testing_service,
            user_progress_service,
            daily_statistics_service,
        )

    user_progress_service.mark_exercise_completed.assert_awaited_once_with(
        exercise_type="Testing",
        section="Grammar",
        subsection="Present Simple",
        exercise_id=7,
        user_id=123,
        success=False,
    )
    testing_service.get_random_testing_exercise.assert_not_awaited()
    daily_statistics_service.update.assert_awaited_once_with("testing_exercises")


async def test_in_process_reports_completion_after_last_correct_answer():
    message = FakeMessage(text="do not", user_id=123, username="test_user")
    state = make_state()
    testing_service = SimpleNamespace(
        get_random_testing_exercise=AsyncMock(return_value=None)
    )
    user_progress_service = SimpleNamespace(
        mark_exercise_completed=AsyncMock(return_value=False),
        get_counts_completed_exercises_testing=AsyncMock(return_value=(2, 4, 5)),
    )
    daily_statistics_service = SimpleNamespace(update=AsyncMock())

    with (
        patch(
            "bot.handlers.user_testing_handlers.keyboard_builder",
            new=AsyncMock(return_value="kb"),
        ),
        patch(
            "bot.handlers.user_testing_handlers.send_message_to_admin", new=AsyncMock()
        ) as notify_admin,
    ):
        await in_process_testing(
            message,
            state,
            testing_service,
            user_progress_service,
            daily_statistics_service,
        )

    user_progress_service.get_counts_completed_exercises_testing.assert_awaited_once_with(
        user_id=123,
        section="Grammar",
        subsection="Present Simple",
    )
    assert MessageTexts.ALL_EXERCISES_COMPLETED in message.answer.await_args.args[0]
    notify_admin.assert_awaited_once()


async def test_start_again_confirm_resets_progress_before_new_exercise():
    callback = FakeCallback(data="sure_start_again_test")
    state = FakeState({"section": "Grammar", "subsection": "Present Simple"})
    user_progress_service = SimpleNamespace(
        delete_progress_by_subsection=AsyncMock(),
        get_counts_completed_exercises_testing=AsyncMock(),
    )
    testing_service = SimpleNamespace(
        get_random_testing_exercise=AsyncMock(return_value=("Q?", "answer", 1))
    )

    with patch(
        "bot.handlers.user_testing_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    ):
        await start_again_testing(
            callback,
            state,
            user_progress_service,
            testing_service,
        )

    user_progress_service.delete_progress_by_subsection.assert_awaited_once_with(
        user_id=123,
        section="Grammar",
        subsection="Present Simple",
    )
    callback.message.answer.assert_awaited_once_with("Q?")


async def test_see_answer_reveals_answer_then_serves_next_exercise():
    callback = FakeCallback(data="see_answer_testing")
    state = FakeState(
        {
            "section": "Grammar",
            "subsection": "Present Simple",
            "current_answer": "do not",
        }
    )
    user_progress_service = SimpleNamespace(
        get_counts_completed_exercises_testing=AsyncMock(),
    )
    testing_service = SimpleNamespace(
        get_random_testing_exercise=AsyncMock(return_value=("Next?", "answer", 9))
    )

    with (
        patch(
            "bot.handlers.user_testing_handlers.keyboard_builder",
            new=AsyncMock(return_value="kb"),
        ),
        patch(
            "bot.handlers.user_testing_handlers.asyncio.sleep", new=AsyncMock()
        ) as sleep_mock,
    ):
        await see_answer_testing(
            callback,
            state,
            user_progress_service,
            testing_service,
        )

    sleep_mock.assert_awaited_once_with(3)
    assert "Правильный ответ" in callback.message.edit_text.await_args_list[0].args[0]
    callback.message.answer.assert_awaited_once_with("Next?")
