from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.db.models import NewWords
from bot.services.new_words import NewWordsService
from tests.factories import build_new_word


def make_repo(**overrides):
    defaults = {
        "get_max_exercise_id": AsyncMock(return_value=0),
        "add_exercise": AsyncMock(),
        "delete_exercise": AsyncMock(),
        "update_exercise": AsyncMock(),
        "count_exercises": AsyncMock(return_value=0),
        "list_exercises": AsyncMock(return_value=[]),
        "get_subsection_names": AsyncMock(return_value=[]),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


async def test_add_new_words_exercise_uses_next_id():
    repo = make_repo(get_max_exercise_id=AsyncMock(return_value=4))
    service = NewWordsService(repository=repo)

    await service.add_new_words_exercise(
        section="Vocabulary",
        subsection="Travel",
        russian="поезд",
        english="train",
    )

    repo.get_max_exercise_id.assert_awaited_once_with("Vocabulary", "Travel")
    repo.add_exercise.assert_awaited_once()
    exercise = repo.add_exercise.await_args.args[0]
    assert isinstance(exercise, NewWords)
    assert exercise.section == "Vocabulary"
    assert exercise.subsection == "Travel"
    assert exercise.id == 5
    assert exercise.russian == "поезд"
    assert exercise.english == "train"


async def test_get_new_words_exercises_formats_text_and_casts_subsection():
    repo = make_repo(
        list_exercises=AsyncMock(
            return_value=[
                build_new_word(exercise_id=1, russian="поезд", english="train"),
                build_new_word(exercise_id=2, russian="самолет", english="plane"),
            ]
        )
    )
    service = NewWordsService(repository=repo)

    result = await service.get_new_words_exercises(123)

    repo.list_exercises.assert_awaited_once_with("123")
    assert result == "1) поезд – train\n2) самолет – plane\n"


async def test_count_and_subsections_delegate_to_repository():
    repo = make_repo(
        count_exercises=AsyncMock(return_value=8),
        get_subsection_names=AsyncMock(return_value=["Travel"]),
    )
    service = NewWordsService(repository=repo)

    count = await service.get_count_new_words_exercises_in_subsection(
        "Vocabulary",
        "Travel",
    )
    subsections = await service.get_subsection_names("Vocabulary")

    assert count == 8
    assert subsections == ["Travel"]
    repo.count_exercises.assert_awaited_once_with("Vocabulary", "Travel")
    repo.get_subsection_names.assert_awaited_once_with("Vocabulary")


async def test_edit_and_delete_delegate_to_repository():
    repo = make_repo()
    service = NewWordsService(repository=repo)

    await service.edit_new_words_exercise(
        "Vocabulary",
        "Travel",
        "корабль",
        "ship",
        2,
    )
    await service.delete_new_words_exercise("Vocabulary", "Travel", 2)

    repo.update_exercise.assert_awaited_once_with(
        "Vocabulary",
        "Travel",
        2,
        "корабль",
        "ship",
    )
    repo.delete_exercise.assert_awaited_once_with("Vocabulary", "Travel", 2)
