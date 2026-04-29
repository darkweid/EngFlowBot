from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.db.models import NewWords, UserWordsLearning
from bot.services.user_words_learning import UserWordsLearningService
from tests.factories import build_new_word, build_user_word_learning


def make_repo(**overrides):
    defaults = {
        "words_to_learn_today": AsyncMock(return_value=[]),
        "all_words_by_section_subsection": AsyncMock(return_value=[]),
        "all_words_by_user": AsyncMock(return_value=[]),
        "count_active_learning": AsyncMock(return_value=0),
        "count_learned": AsyncMock(return_value=0),
        "count_all_by_user": AsyncMock(return_value=0),
        "count_all_today_by_user": AsyncMock(return_value=0),
        "distinct_subsections": AsyncMock(return_value=[]),
        "count_learned_in_subsection": AsyncMock(return_value=0),
        "count_active_in_subsection": AsyncMock(return_value=0),
        "count_today_in_subsection": AsyncMock(return_value=0),
        "count_total_in_subsection": AsyncMock(return_value=0),
        "sum_success_in_subsection": AsyncMock(return_value=0),
        "sum_attempts_in_subsection": AsyncMock(return_value=0),
        "learning_info": AsyncMock(return_value=None),
        "update_user_points": AsyncMock(),
        "update_learning_progress": AsyncMock(),
        "list_new_words": AsyncMock(return_value=[]),
        "add_user_words_learning_entries": AsyncMock(),
        "max_custom_word_id": AsyncMock(return_value=0),
        "add_new_word": AsyncMock(),
        "add_user_words_learning_entry": AsyncMock(),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def learning_entry(
    *,
    exercise_id: int,
    russian: str,
    english: str,
    section: str = "Vocabulary",
    subsection: str = "Travel",
    success: int = 0,
    attempts: int = 0,
) -> UserWordsLearning:
    word = build_new_word(
        section=section,
        subsection=subsection,
        exercise_id=exercise_id,
        russian=russian,
        english=english,
    )
    return build_user_word_learning(
        section=section,
        subsection=subsection,
        exercise_id=exercise_id,
        success=success,
        attempts=attempts,
        new_word=word,
    )


async def test_get_random_word_exercise_returns_none_when_no_words_today():
    repo = make_repo(words_to_learn_today=AsyncMock(return_value=[]))
    service = UserWordsLearningService(repository=repo)

    result = await service.get_random_word_exercise(123)

    assert result is None
    repo.words_to_learn_today.assert_awaited_once_with(123)
    repo.all_words_by_section_subsection.assert_not_awaited()


async def test_get_random_word_exercise_uses_same_subsection_options():
    target = learning_entry(exercise_id=1, russian="дом", english="house")
    same_subsection_words = [
        target,
        learning_entry(exercise_id=2, russian="поезд", english="train"),
        learning_entry(exercise_id=3, russian="самолет", english="plane"),
        learning_entry(exercise_id=4, russian="корабль", english="ship"),
    ]
    repo = make_repo(
        words_to_learn_today=AsyncMock(return_value=[target]),
        all_words_by_section_subsection=AsyncMock(return_value=same_subsection_words),
    )
    service = UserWordsLearningService(repository=repo)

    with (
        patch("bot.services.user_words_learning.random.choice", return_value=target),
        patch(
            "bot.services.user_words_learning.random.sample",
            side_effect=lambda options, k: options[:k],
        ),
    ):
        result = await service.get_random_word_exercise(123)

    assert result == {
        "russian": "Дом",
        "english": "House",
        "section": "Vocabulary",
        "subsection": "Travel",
        "exercise_id": 1,
        "options": ["Поезд", "Самолет", "Корабль"],
    }
    repo.all_words_by_user.assert_not_awaited()


async def test_get_random_word_exercise_falls_back_to_all_user_words():
    target = learning_entry(exercise_id=1, russian="дом", english="house")
    same_subsection_words = [
        target,
        learning_entry(exercise_id=2, russian="поезд", english="train"),
    ]
    all_words = same_subsection_words + [
        learning_entry(
            exercise_id=3,
            russian="яблоко",
            english="apple",
            section="Vocabulary",
            subsection="Food",
        ),
        learning_entry(
            exercise_id=4,
            russian="молоко",
            english="milk",
            section="Vocabulary",
            subsection="Food",
        ),
    ]
    repo = make_repo(
        words_to_learn_today=AsyncMock(return_value=[target]),
        all_words_by_section_subsection=AsyncMock(return_value=same_subsection_words),
        all_words_by_user=AsyncMock(return_value=all_words),
    )
    service = UserWordsLearningService(repository=repo)

    with (
        patch("bot.services.user_words_learning.random.choice", return_value=target),
        patch(
            "bot.services.user_words_learning.random.sample",
            side_effect=lambda options, k: options[:k],
        ),
    ):
        result = await service.get_random_word_exercise(123)

    assert result["options"] == ["Поезд", "Яблоко", "Молоко"]
    repo.all_words_by_user.assert_awaited_once_with(123)


async def test_get_added_subsections_by_user_delegates_to_repo():
    repo = make_repo(distinct_subsections=AsyncMock(return_value=["Travel", "Food"]))
    service = UserWordsLearningService(repository=repo)

    result = await service.get_added_subsections_by_user(123)

    assert result == ["Travel", "Food"]
    repo.distinct_subsections.assert_awaited_once_with(123)


async def test_count_methods_delegate_with_learning_rates():
    repo = make_repo(
        count_active_learning=AsyncMock(return_value=3),
        count_learned=AsyncMock(return_value=4),
        count_all_by_user=AsyncMock(return_value=10),
        count_all_today_by_user=AsyncMock(return_value=2),
    )
    service = UserWordsLearningService(repository=repo)

    active = await service.get_count_active_learning_exercises(123)
    learned = await service.get_count_learned_exercises(123)
    total = await service.get_count_all_exercises_by_user(123)
    today = await service.get_count_all_exercises_for_today_by_user(123)

    assert (active, learned, total, today) == (3, 4, 10, 2)
    repo.count_active_learning.assert_awaited_once_with(123, 3)
    repo.count_learned.assert_awaited_once_with(123, 5)
    repo.count_all_by_user.assert_awaited_once_with(123)
    repo.count_all_today_by_user.assert_awaited_once_with(123)


async def test_get_user_stats_calculates_success_rate():
    repo = make_repo(
        distinct_subsections=AsyncMock(return_value=["Travel", "Food"]),
        count_learned_in_subsection=AsyncMock(side_effect=[1, 0]),
        count_active_in_subsection=AsyncMock(side_effect=[2, 3]),
        count_today_in_subsection=AsyncMock(side_effect=[4, 5]),
        count_total_in_subsection=AsyncMock(side_effect=[10, 12]),
        sum_success_in_subsection=AsyncMock(side_effect=[3, 0]),
        sum_attempts_in_subsection=AsyncMock(side_effect=[6, 0]),
    )
    service = UserWordsLearningService(repository=repo)

    result = await service.get_user_stats(123)

    assert result == {
        "Travel": {
            "learned": 1,
            "for_today_learning": 4,
            "active_learning": 2,
            "total_words_in_subsection": 10,
            "success_rate": 50.0,
        },
        "Food": {
            "learned": 0,
            "for_today_learning": 5,
            "active_learning": 3,
            "total_words_in_subsection": 12,
            "success_rate": 0,
        },
    }


async def test_set_progress_skips_writes_when_learning_info_missing():
    repo = make_repo(learning_info=AsyncMock(return_value=None))
    service = UserWordsLearningService(repository=repo)

    await service.set_progress(123, "Vocabulary", "Travel", 1, success=True)

    repo.update_user_points.assert_not_awaited()
    repo.update_learning_progress.assert_not_awaited()


async def test_set_progress_success_increments_points_and_success_count():
    info = learning_entry(exercise_id=1, russian="дом", english="house", success=1)
    repo = make_repo(learning_info=AsyncMock(return_value=info))
    service = UserWordsLearningService(repository=repo)

    await service.set_progress(123, "Vocabulary", "Travel", 1, success=True)

    repo.update_user_points.assert_awaited_once_with(123, 1)
    repo.update_learning_progress.assert_awaited_once()
    args = repo.update_learning_progress.await_args.args
    assert args[:4] == ("Vocabulary", "Travel", 1, 2)
    assert isinstance(args[4], date)
    assert args[4] >= date.today() + timedelta(days=1)


async def test_set_progress_failure_decrements_points_and_reviews_tomorrow():
    info = learning_entry(exercise_id=1, russian="дом", english="house", success=1)
    repo = make_repo(learning_info=AsyncMock(return_value=info))
    service = UserWordsLearningService(repository=repo)

    await service.set_progress(123, "Vocabulary", "Travel", 1, success=False)

    repo.update_user_points.assert_awaited_once_with(123, -1)
    repo.update_learning_progress.assert_awaited_once_with(
        "Vocabulary",
        "Travel",
        1,
        1,
        date.today() + timedelta(days=1),
    )


async def test_add_words_to_learning_skips_write_when_no_new_words():
    repo = make_repo(list_new_words=AsyncMock(return_value=[]))
    service = UserWordsLearningService(repository=repo)

    await service.add_words_to_learning("Vocabulary", "Travel", 123)

    repo.add_user_words_learning_entries.assert_not_awaited()


async def test_add_words_to_learning_creates_entries_for_new_words():
    repo = make_repo(
        list_new_words=AsyncMock(
            return_value=[
                build_new_word(exercise_id=1),
                build_new_word(exercise_id=2),
            ]
        )
    )
    service = UserWordsLearningService(repository=repo)

    await service.add_words_to_learning("Vocabulary", "Travel", 123)

    repo.add_user_words_learning_entries.assert_awaited_once()
    entries = repo.add_user_words_learning_entries.await_args.args[0]
    assert [entry.exercise_id for entry in entries] == [1, 2]
    assert {entry.user_id for entry in entries} == {123}


async def test_admin_add_words_to_learning_creates_custom_word_and_entry():
    repo = make_repo(max_custom_word_id=AsyncMock(return_value=4))
    service = UserWordsLearningService(repository=repo)

    await service.admin_add_words_to_learning("дом", "house", 123)

    repo.max_custom_word_id.assert_awaited_once_with(123)
    repo.add_new_word.assert_awaited_once()
    word = repo.add_new_word.await_args.args[0]
    assert isinstance(word, NewWords)
    assert word.section == "123"
    assert word.subsection == "123"
    assert word.id == 5
    assert word.russian == "дом"
    assert word.english == "house"
    repo.add_user_words_learning_entry.assert_awaited_once()
    entry = repo.add_user_words_learning_entry.await_args.args[0]
    assert isinstance(entry, UserWordsLearning)
    assert entry.user_id == 123
    assert entry.section == "123"
    assert entry.subsection == "123"
    assert entry.exercise_id == 5
