from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.handlers.user_testing_handlers import in_process_testing
from bot.lexicon import MessageTexts
from tests.helpers import FakeMessage, FakeState


def make_state():
    return FakeState(
        {
            "section": "Grammar",
            "subsection": "Present Simple",
            "current_id": 7,
            "current_answer": "Do not",
        }
    )


async def test_in_process_testing_accepts_answer_ignoring_case_and_spaces():
    message = FakeMessage(text="do not", user_id=123)
    state = make_state()
    testing_service = SimpleNamespace(
        get_random_testing_exercise=AsyncMock(
            return_value=("Next ... sentence", "works", 8)
        )
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

    daily_statistics_service.update.assert_awaited_once_with("testing_exercises")
    user_progress_service.mark_exercise_completed.assert_awaited_once_with(
        exercise_type="Testing",
        section="Grammar",
        subsection="Present Simple",
        exercise_id=7,
        user_id=123,
        success=True,
    )
    testing_service.get_random_testing_exercise.assert_awaited_once_with(
        section="Grammar",
        subsection="Present Simple",
        user_id=123,
    )
    assert state._data["current_test"] == "Next ... sentence"
    assert state._data["current_answer"] == "works"
    assert state._data["current_id"] == 8
    assert message.answer.await_count == 2


async def test_in_process_testing_sends_completion_when_no_exercises_left():
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
    keyboard = object()

    with (
        patch(
            "bot.handlers.user_testing_handlers.keyboard_builder",
            new=AsyncMock(return_value=keyboard),
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
    message.answer.assert_awaited_once()
    assert MessageTexts.ALL_EXERCISES_COMPLETED in message.answer.await_args.args[0]
    notify_admin.assert_awaited_once()


async def test_in_process_testing_marks_wrong_answer_and_shows_retry_keyboard():
    message = FakeMessage(text="wrong", user_id=123)
    state = make_state()
    testing_service = SimpleNamespace(get_random_testing_exercise=AsyncMock())
    user_progress_service = SimpleNamespace(mark_exercise_completed=AsyncMock())
    daily_statistics_service = SimpleNamespace(update=AsyncMock())
    keyboard = object()

    with patch(
        "bot.handlers.user_testing_handlers.keyboard_builder",
        new=AsyncMock(return_value=keyboard),
    ):
        await in_process_testing(
            message,
            state,
            testing_service,
            user_progress_service,
            daily_statistics_service,
        )

    daily_statistics_service.update.assert_awaited_once_with("testing_exercises")
    message.answer.assert_awaited_once_with(
        MessageTexts.INCORRECT_ANSWER,
        reply_markup=keyboard,
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
