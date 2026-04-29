from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.services.daily_statistics import DailyStatisticsService


def make_repo(**overrides):
    defaults = {
        "get_by_date": AsyncMock(return_value=object()),
        "create_blank_for_date": AsyncMock(),
        "increment_field": AsyncMock(),
        "aggregate": AsyncMock(return_value={}),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


async def test_update_ignores_unknown_update_type():
    repo = make_repo()
    service = DailyStatisticsService(repository=repo)

    await service.update("unknown")

    repo.get_by_date.assert_not_awaited()
    repo.create_blank_for_date.assert_not_awaited()
    repo.increment_field.assert_not_awaited()


async def test_update_creates_missing_daily_row_before_incrementing():
    repo = make_repo(get_by_date=AsyncMock(return_value=None))
    service = DailyStatisticsService(repository=repo)

    await service.update("new_words")

    repo.get_by_date.assert_awaited_once()
    today = repo.get_by_date.await_args.args[0]
    repo.create_blank_for_date.assert_awaited_once_with(today)
    repo.increment_field.assert_awaited_once_with(today, "total_new_words")


async def test_update_increments_existing_daily_row():
    existing_stats = object()
    repo = make_repo(get_by_date=AsyncMock(return_value=existing_stats))
    service = DailyStatisticsService(repository=repo)

    await service.update("testing_exercises")

    repo.create_blank_for_date.assert_not_awaited()
    today = repo.get_by_date.await_args.args[0]
    repo.increment_field.assert_awaited_once_with(today, "total_testing_exercises")


async def test_get_delegates_to_repository_aggregate():
    start_date = date(2026, 1, 1)
    end_date = date(2026, 1, 31)
    expected = {"total_new_words": 3}
    repo = make_repo(aggregate=AsyncMock(return_value=expected))
    service = DailyStatisticsService(repository=repo)

    result = await service.get(start_date, end_date)

    assert result == expected
    repo.aggregate.assert_awaited_once_with(start_date, end_date)
