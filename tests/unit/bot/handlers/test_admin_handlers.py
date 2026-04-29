from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from aiogram.exceptions import TelegramBadRequest

from bot.handlers import admin_handlers
from bot.handlers.admin_handlers import (
    adding_broadcast_date_time,
    adding_broadcast_text,
    admin_activity,
    admin_adding_sentence_testing,
    admin_adding_words,
    admin_adding_words_to_user,
    admin_command,
    admin_delete_user,
    admin_deleting_sentence_testing,
    admin_deleting_words,
    admin_edit_sentence_testing,
    admin_edit_words,
    admin_exit,
    admin_testing_management,
    admin_words_management,
    sure_delete_broadcast,
)
from bot.lexicon import AdminMenuButtons
from bot.states import AdminFSM, UserFSM
from tests.helpers import FakeCallback, FakeMessage, FakeState


def _message_admin_command():
    handlers = admin_handlers.admin_router.observers["message"].handlers
    return next(h.callback for h in handlers if h.callback.__name__ == "admin_command")


def _kb_patch():
    return patch(
        "bot.handlers.admin_handlers.keyboard_builder",
        new=AsyncMock(return_value="kb"),
    )


async def test_admin_command_allows_configured_admin_and_rejects_others():
    admin_message = FakeMessage(user_id=999)
    other_message = FakeMessage(user_id=42)
    admin_state = FakeState()
    other_state = FakeState()

    with patch(
        "bot.handlers.admin_handlers.settings", SimpleNamespace(admin_ids=[999])
    ):
        with _kb_patch():
            await _message_admin_command()(admin_message, admin_state)
        await _message_admin_command()(other_message, other_state)

    admin_state.set_state.assert_awaited_once_with(AdminFSM.default)
    other_state.set_state.assert_not_awaited()
    other_message.answer.assert_awaited_once_with("🚫 Вам сюда нельзя 🚫")


async def test_admin_main_menu_callback_resets_admin_state():
    callback = FakeCallback()
    state = FakeState()

    with _kb_patch():
        await admin_command(callback, state)

    callback.message.edit_text.assert_awaited_once()
    state.set_state.assert_awaited_once_with(AdminFSM.default)


async def test_admin_exit_resets_user_state_even_when_delete_fails():
    callback = FakeCallback()
    callback.message.delete = AsyncMock(
        side_effect=TelegramBadRequest(method=SimpleNamespace(), message="cant delete")
    )
    state = FakeState({"admin_section": "x", "admin_subsection": "y"})

    await admin_exit(callback, state)

    state.set_state.assert_awaited_once_with(UserFSM.default)
    assert state._data["admin_section"] is None
    assert state._data["admin_subsection"] is None


async def test_admin_testing_management_routes_crud_actions_to_expected_states():
    state = FakeState({"admin_section": "Tenses", "admin_subsection": "Present Simple"})
    testing_service = SimpleNamespace(get_testing_exercises=AsyncMock())

    for callback_data, expected_state in [
        (AdminMenuButtons.ADD_EXERCISE_TESTING, AdminFSM.adding_exercise_testing),
        (AdminMenuButtons.EDIT_EXERCISE_TESTING, AdminFSM.editing_exercise_testing),
        (AdminMenuButtons.DEL_EXERCISE_TESTING, AdminFSM.deleting_exercise_testing),
    ]:
        state.set_state.reset_mock()
        with _kb_patch():
            await admin_testing_management(
                FakeCallback(data=callback_data), state, testing_service
            )

        state.set_state.assert_awaited_once_with(expected_state)


async def test_admin_adding_sentence_testing_parses_multiline_input():
    message = FakeMessage(text="He works=+=works\nShe runs=+=runs")
    state = FakeState({"admin_section": "Tenses", "admin_subsection": "Present Simple"})
    testing_service = SimpleNamespace(add_testing_exercise=AsyncMock())

    with _kb_patch():
        await admin_adding_sentence_testing(message, state, testing_service)

    assert testing_service.add_testing_exercise.await_count == 2
    testing_service.add_testing_exercise.assert_any_await(
        section="Tenses",
        subsection="Present Simple",
        test="He works",
        answer="works",
    )


async def test_admin_edit_sentence_testing_uses_selected_index_and_resets_state():
    message = FakeMessage(text="He runs=+=runs")
    state = FakeState(
        {
            "admin_section": "Tenses",
            "admin_subsection": "Present Simple",
            "index_testing_edit": 7,
        }
    )
    testing_service = SimpleNamespace(edit_testing_exercise=AsyncMock())

    with _kb_patch():
        await admin_edit_sentence_testing(message, state, testing_service)

    testing_service.edit_testing_exercise.assert_awaited_once_with(
        section="Tenses",
        subsection="Present Simple",
        test="He runs",
        answer="runs",
        index=7,
    )
    state.set_state.assert_awaited_once_with(AdminFSM.default)


async def test_admin_deleting_sentence_testing_accepts_comma_separated_indexes():
    message = FakeMessage(text="1,2,3")
    state = FakeState({"admin_section": "Tenses", "admin_subsection": "Present Simple"})
    testing_service = SimpleNamespace(delete_testing_exercise=AsyncMock())

    with _kb_patch():
        await admin_deleting_sentence_testing(message, state, testing_service)

    assert testing_service.delete_testing_exercise.await_count == 3
    testing_service.delete_testing_exercise.assert_any_await(
        section="Tenses",
        subsection="Present Simple",
        index=2,
    )


async def test_admin_delete_user_confirm_deletes_selected_user():
    callback = FakeCallback(data="delete_user")
    state = FakeState({"admin_user_id_management": 555})
    user_service = SimpleNamespace(delete_user=AsyncMock())

    with _kb_patch():
        await admin_delete_user(callback, state, user_service)

    user_service.delete_user.assert_awaited_once_with(user_id=555)


async def test_admin_adding_words_to_user_parses_and_notifies_user():
    message = FakeMessage(text="дом=+=house")
    state = FakeState({"admin_user_id_management": 555})
    user_service = SimpleNamespace(
        get_user=AsyncMock(return_value={"full_name": "John"})
    )
    learning_service = SimpleNamespace(admin_add_words_to_learning=AsyncMock())

    with (
        _kb_patch(),
        patch(
            "bot.handlers.admin_handlers.send_message_to_user", new=AsyncMock()
        ) as notify,
        patch(
            "bot.handlers.admin_handlers.check_line",
            return_value=SimpleNamespace(russian="дом", english="house"),
        ),
    ):
        await admin_adding_words_to_user(message, state, user_service, learning_service)

    learning_service.admin_add_words_to_learning.assert_awaited_once_with(
        user_id=555,
        russian="дом",
        english="house",
    )
    notify.assert_awaited_once()


async def test_admin_words_management_routes_crud_actions_to_expected_states():
    state = FakeState({"admin_section": "Vocabulary", "admin_subsection": "Travel"})
    new_words_service = SimpleNamespace(get_new_words_exercises=AsyncMock())

    for callback_data, expected_state in [
        (AdminMenuButtons.ADD_NEW_WORDS, AdminFSM.adding_exercise_words),
        (AdminMenuButtons.YES, AdminFSM.adding_exercise_words),
        (AdminMenuButtons.EDIT_NEW_WORDS, AdminFSM.editing_exercise_words),
        (AdminMenuButtons.DEL_NEW_WORDS, AdminFSM.deleting_exercise_words),
    ]:
        state.set_state.reset_mock()
        with _kb_patch():
            await admin_words_management(
                FakeCallback(data=callback_data), state, new_words_service
            )

        state.set_state.assert_awaited_once_with(expected_state)


async def test_admin_adding_words_parses_multiline_input():
    message = FakeMessage(text="дом=+=house\nкот=+=cat")
    state = FakeState({"admin_section": "Vocabulary", "admin_subsection": "Travel"})
    new_words_service = SimpleNamespace(add_new_words_exercise=AsyncMock())

    with (
        _kb_patch(),
        patch(
            "bot.handlers.admin_handlers.check_line",
            side_effect=[
                SimpleNamespace(russian="дом", english="house"),
                SimpleNamespace(russian="кот", english="cat"),
            ],
        ),
    ):
        await admin_adding_words(message, state, new_words_service)

    assert new_words_service.add_new_words_exercise.await_count == 2


async def test_admin_edit_words_uses_selected_index_and_resets_state():
    message = FakeMessage(text="дом=+=house")
    state = FakeState(
        {
            "admin_section": "Vocabulary",
            "admin_subsection": "Travel",
            "index_words_edit": 9,
        }
    )
    new_words_service = SimpleNamespace(edit_new_words_exercise=AsyncMock())

    with (
        _kb_patch(),
        patch(
            "bot.handlers.admin_handlers.check_line",
            return_value=SimpleNamespace(russian="дом", english="house"),
        ),
    ):
        await admin_edit_words(message, state, new_words_service)

    new_words_service.edit_new_words_exercise.assert_awaited_once_with(
        section="Vocabulary",
        subsection="Travel",
        russian="дом",
        english="house",
        index=9,
    )
    state.set_state.assert_awaited_once_with(AdminFSM.default)


async def test_admin_deleting_words_rejects_invalid_indexes():
    message = FakeMessage(text="abc")
    state = FakeState({"admin_section": "Vocabulary", "admin_subsection": "Travel"})
    new_words_service = SimpleNamespace(delete_new_words_exercise=AsyncMock())

    with _kb_patch():
        await admin_deleting_words(message, state, new_words_service)

    new_words_service.delete_new_words_exercise.assert_not_awaited()


async def test_admin_broadcast_date_validation_and_scheduling():
    state = FakeState()
    invalid_message = FakeMessage(text="not a date")
    valid_message = FakeMessage(text="09:30 28.04.2026")

    await adding_broadcast_date_time(invalid_message, state)
    state.set_state.assert_not_awaited()

    await adding_broadcast_date_time(valid_message, state)
    state.set_state.assert_awaited_once_with(AdminFSM.broadcasting_set_text)
    assert state._data["broadcast_date_time"] == "09:30 28.04.2026"

    with patch(
        "bot.handlers.admin_handlers.schedule_broadcast", new=AsyncMock()
    ) as schedule:
        await adding_broadcast_text(
            FakeMessage(text="Hello users"),
            FakeState({"broadcast_date_time": "09:30 28.04.2026"}),
        )

    schedule.assert_awaited_once_with(
        date_time=datetime(2026, 4, 28, 9, 30),
        text="Hello users",
    )


async def test_sure_delete_broadcast_calls_scheduler_cleanup():
    callback = FakeCallback()

    with (
        _kb_patch(),
        patch(
            "bot.handlers.admin_handlers.delete_scheduled_broadcasts", new=AsyncMock()
        ) as delete_func,
    ):
        await sure_delete_broadcast(callback)

    delete_func.assert_awaited_once()


async def test_admin_activity_uses_injected_daily_statistics_service():
    callback = FakeCallback(data=AdminMenuButtons.SEE_ACTIVITY_DAY)
    stats = {
        "testing_exercises": 1,
        "new_words": 2,
        "irregular_verbs": 3,
        "new_users": 4,
    }
    daily_statistics_service = SimpleNamespace(get=AsyncMock(return_value=stats))

    with _kb_patch():
        await admin_activity(
            callback,
            daily_statistics_service=daily_statistics_service,
        )

    today = date.today()
    daily_statistics_service.get.assert_awaited_once_with(
        start_date=today,
        end_date=today,
    )
    callback.message.answer.assert_awaited_once()
