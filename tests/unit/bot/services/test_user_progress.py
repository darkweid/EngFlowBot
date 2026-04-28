from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.db.models import UserProgress
from bot.services.user_progress import UserProgressService
from tests.factories import build_user


class FixedDatetime(datetime):
    @classmethod
    def utcnow(cls):
        return cls(2026, 4, 28, 12, 0)


def make_repo(**overrides):
    defaults = {
        "update_progress_attempt": AsyncMock(return_value=0),
        "update_user_points": AsyncMock(),
        "add_progress_entry": AsyncMock(),
        "delete_progress_by_subsection": AsyncMock(),
        "count_success_testing": AsyncMock(return_value=0),
        "count_testing_exercises_total": AsyncMock(return_value=0),
        "count_by_type_in_interval": AsyncMock(return_value=0),
        "get_user_points": AsyncMock(return_value=0),
        "count_users_with_points_greater": AsyncMock(return_value=0),
        "total_users": AsyncMock(return_value=0),
        "list_users_ordered_by_points": AsyncMock(return_value=[]),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


async def test_mark_exercise_completed_creates_progress_on_first_attempt():
    repo = make_repo(update_progress_attempt=AsyncMock(return_value=0))
    service = UserProgressService(repository=repo)

    result = await service.mark_exercise_completed(
        user_id=123,
        exercise_type="Testing",
        subsection="Present Simple",
        section="Grammar",
        exercise_id=5,
        success=True,
    )

    assert result is True
    repo.update_progress_attempt.assert_awaited_once_with(
        123,
        "Testing",
        "Grammar",
        "Present Simple",
        5,
        True,
    )
    repo.update_user_points.assert_awaited_once_with(123, 1)
    repo.add_progress_entry.assert_awaited_once()
    entry = repo.add_progress_entry.await_args.args[0]
    assert isinstance(entry, UserProgress)
    assert entry.user_id == 123
    assert entry.exercise_type == "Testing"
    assert entry.exercise_section == "Grammar"
    assert entry.exercise_subsection == "Present Simple"
    assert entry.exercise_id == 5
    assert entry.attempts == 1
    assert entry.success is True


async def test_mark_exercise_completed_skips_entry_on_existing_progress():
    repo = make_repo(update_progress_attempt=AsyncMock(return_value=1))
    service = UserProgressService(repository=repo)

    result = await service.mark_exercise_completed(
        user_id=123,
        exercise_type="Testing",
        subsection="Present Simple",
        section="Grammar",
        exercise_id=5,
        success=False,
    )

    assert result is False
    repo.update_user_points.assert_awaited_once_with(123, -1)
    repo.add_progress_entry.assert_not_awaited()


async def test_delete_progress_by_subsection_delegates_to_repository():
    repo = make_repo()
    service = UserProgressService(repository=repo)

    await service.delete_progress_by_subsection(123, "Grammar", "Present Simple")

    repo.delete_progress_by_subsection.assert_awaited_once_with(
        123,
        "Grammar",
        "Present Simple",
    )


async def test_get_counts_completed_exercises_testing_returns_counts():
    repo = make_repo(
        count_success_testing=AsyncMock(side_effect=[2, 4]),
        count_testing_exercises_total=AsyncMock(return_value=10),
    )
    service = UserProgressService(repository=repo)

    result = await service.get_counts_completed_exercises_testing(
        123,
        "Grammar",
        "Present Simple",
    )

    assert result == (2, 4, 10)
    repo.count_success_testing.assert_any_await(
        123,
        "Grammar",
        "Present Simple",
        first_try_only=True,
    )
    repo.count_success_testing.assert_any_await(
        123,
        "Grammar",
        "Present Simple",
        first_try_only=False,
    )
    repo.count_testing_exercises_total.assert_awaited_once_with(
        "Grammar",
        "Present Simple",
    )


async def test_get_activity_by_user_formats_known_interval(monkeypatch):
    monkeypatch.setattr("bot.services.user_progress.datetime", FixedDatetime)
    repo = make_repo(count_by_type_in_interval=AsyncMock(side_effect=[1, 2, 3]))
    service = UserProgressService(repository=repo)

    result = await service.get_activity_by_user(123, interval=7)

    assert "последнюю неделю" in result
    assert "Тестирование: 1" in result
    assert "Изучение новых слов: 2" in result
    assert "Неправильные глаголы: 3" in result
    repo.count_by_type_in_interval.assert_any_await(
        123,
        "Testing",
        date(2026, 4, 21),
        date(2026, 4, 28),
    )


async def test_get_activity_by_user_formats_custom_interval(monkeypatch):
    monkeypatch.setattr("bot.services.user_progress.datetime", FixedDatetime)
    repo = make_repo(count_by_type_in_interval=AsyncMock(side_effect=[0, 0, 0]))
    service = UserProgressService(repository=repo)

    result = await service.get_activity_by_user(123, interval=5)

    assert "последние 5 дн." in result


async def test_get_user_rank_and_total_returns_numeric_rank():
    repo = make_repo(
        get_user_points=AsyncMock(return_value=50),
        count_users_with_points_greater=AsyncMock(return_value=3),
        total_users=AsyncMock(return_value=10),
    )
    service = UserProgressService(repository=repo)

    result = await service.get_user_rank_and_total(123)

    assert result == (4, 10)
    repo.get_user_points.assert_awaited_once_with(123)
    repo.count_users_with_points_greater.assert_awaited_once_with(50)
    repo.total_users.assert_awaited_once_with()


async def test_get_user_rank_and_total_returns_medal_for_top_three():
    repo = make_repo(
        get_user_points=AsyncMock(return_value=50),
        count_users_with_points_greater=AsyncMock(return_value=0),
        total_users=AsyncMock(return_value=10),
    )
    service = UserProgressService(repository=repo)

    result = await service.get_user_rank_and_total(123, medals_rank=True)

    assert result == ("🥇", 10)


async def test_get_all_users_ranks_and_points_maps_users():
    users = [
        build_user(user_id=1, full_name="One", tg_login="one", points=30),
        build_user(user_id=2, full_name="Two", tg_login="two", points=20),
        build_user(user_id=3, full_name="Three", tg_login="three", points=10),
        build_user(user_id=4, full_name="Four", tg_login="four", points=5),
    ]
    repo = make_repo(list_users_ordered_by_points=AsyncMock(return_value=users))
    service = UserProgressService(repository=repo)

    result = await service.get_all_users_ranks_and_points(medals_rank=True)

    assert result == [
        {
            "rank": "🥇",
            "user_id": "1",
            "full_name": "One",
            "tg_login": "one",
            "points": "30",
        },
        {
            "rank": "🥈",
            "user_id": "2",
            "full_name": "Two",
            "tg_login": "two",
            "points": "20",
        },
        {
            "rank": "🥉",
            "user_id": "3",
            "full_name": "Three",
            "tg_login": "three",
            "points": "10",
        },
        {
            "rank": "4",
            "user_id": "4",
            "full_name": "Four",
            "tg_login": "four",
            "points": "5",
        },
    ]
