from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.db.models import TestingExercise as _TestingExercise
from bot.services.testing import TestingService as _TestingService
from tests.factories import build_testing_exercise


def make_repo(**overrides):
    defaults = {
        "get_max_exercise_id": AsyncMock(return_value=0),
        "add_exercise": AsyncMock(),
        "list_exercises": AsyncMock(return_value=[]),
        "count_exercises": AsyncMock(return_value=0),
        "get_available_exercises": AsyncMock(return_value=[]),
        "get_section_names": AsyncMock(return_value=[]),
        "get_subsection_names": AsyncMock(return_value=[]),
        "update_exercise": AsyncMock(),
        "delete_exercise": AsyncMock(),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


async def test_add_testing_exercise_uses_next_id_and_strips_nbsp():
    repo = make_repo(get_max_exercise_id=AsyncMock(return_value=7))
    service = _TestingService(repository=repo)

    await service.add_testing_exercise(
        section="Grammar",
        subsection="Present Simple",
        test="She ... English",
        answer="speaks\u00a0",
    )

    repo.get_max_exercise_id.assert_awaited_once_with("Grammar", "Present Simple")
    repo.add_exercise.assert_awaited_once()
    exercise = repo.add_exercise.await_args.args[0]
    assert isinstance(exercise, _TestingExercise)
    assert exercise.section == "Grammar"
    assert exercise.subsection == "Present Simple"
    assert exercise.id == 8
    assert exercise.test == "She ... English"
    assert exercise.answer == "speaks"


async def test_get_testing_exercises_formats_human_readable_text():
    repo = make_repo(
        list_exercises=AsyncMock(
            return_value=[
                build_testing_exercise(exercise_id=1, test="I ...", answer="am"),
                build_testing_exercise(exercise_id=2, test="He ...", answer="is"),
            ]
        )
    )
    service = _TestingService(repository=repo)

    result = await service.get_testing_exercises("Present Simple")

    repo.list_exercises.assert_awaited_once_with("Present Simple")
    assert result == "1) I .... Ответ: am\n\n2) He .... Ответ: is\n\n"


async def test_get_random_testing_exercise_returns_none_when_empty():
    repo = make_repo(get_available_exercises=AsyncMock(return_value=[]))
    service = _TestingService(repository=repo)

    result = await service.get_random_testing_exercise("Grammar", "Past Simple", 123)

    assert result is None
    repo.get_available_exercises.assert_awaited_once_with(
        "Grammar",
        "Past Simple",
        123,
    )


async def test_get_random_testing_exercise_returns_selected_exercise():
    first = build_testing_exercise(exercise_id=1, test="I ...", answer="am")
    second = build_testing_exercise(exercise_id=2, test="He ...", answer="is")
    repo = make_repo(get_available_exercises=AsyncMock(return_value=[first, second]))
    service = _TestingService(repository=repo)

    with patch("bot.services.testing.random.choice", return_value=second):
        result = await service.get_random_testing_exercise(
            "Grammar",
            "Present Simple",
            123,
        )

    assert result == ("He ...", "is", 2)


async def test_count_and_names_delegate_to_repository():
    repo = make_repo(
        count_exercises=AsyncMock(return_value=5),
        get_section_names=AsyncMock(return_value=["Grammar"]),
        get_subsection_names=AsyncMock(return_value=["Present Simple"]),
    )
    service = _TestingService(repository=repo)

    count = await service.get_count_testing_exercises_in_subsection(
        "Grammar",
        "Present Simple",
    )
    sections = await service.get_section_names()
    subsections = await service.get_subsection_names("Grammar")

    assert count == 5
    assert sections == ["Grammar"]
    assert subsections == ["Present Simple"]
    repo.count_exercises.assert_awaited_once_with("Grammar", "Present Simple")
    repo.get_section_names.assert_awaited_once_with()
    repo.get_subsection_names.assert_awaited_once_with("Grammar")


async def test_edit_and_delete_delegate_to_repository():
    repo = make_repo()
    service = _TestingService(repository=repo)

    await service.edit_testing_exercise(
        "Grammar",
        "Present Simple",
        "She ...",
        "speaks",
        3,
    )
    await service.delete_testing_exercise("Grammar", "Present Simple", 3)

    repo.update_exercise.assert_awaited_once_with(
        "Grammar",
        "Present Simple",
        3,
        "She ...",
        "speaks",
    )
    repo.delete_exercise.assert_awaited_once_with("Grammar", "Present Simple", 3)
