from datetime import date

from bot.db.models import DailyStatistics
from bot.db.repositories.daily_statistics import DailyStatisticsRepository
from tests.fakes import (
    FakeAsyncSession,
    FakeExecuteResult,
    FakeSessionMaker,
    row,
    statement_sql,
)


async def test_get_by_date_filters_by_day():
    stats = DailyStatistics(date=date(2026, 4, 28))
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=stats)])
    repo = DailyStatisticsRepository(session_maker=FakeSessionMaker(session))

    result = await repo.get_by_date(date(2026, 4, 28))

    assert result is stats
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from daily_statistics" in sql
    assert "daily_statistics.date = '2026-04-28'" in sql


async def test_create_blank_for_date_adds_zeroed_statistics_row():
    session = FakeAsyncSession()
    repo = DailyStatisticsRepository(session_maker=FakeSessionMaker(session))

    result = await repo.create_blank_for_date(date(2026, 4, 28))

    assert result.date == date(2026, 4, 28)
    assert result.total_new_words == 0
    assert result.total_testing_exercises == 0
    assert result.total_irregular_verbs == 0
    assert result.new_users == 0
    session.begin.assert_called_once_with()
    session.add.assert_called_once_with(result)


async def test_increment_field_updates_selected_counter():
    session = FakeAsyncSession([FakeExecuteResult()])
    repo = DailyStatisticsRepository(session_maker=FakeSessionMaker(session))

    await repo.increment_field(
        day=date(2026, 4, 28),
        field_name="total_new_words",
        amount=3,
    )

    session.begin.assert_called_once_with()
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "update daily_statistics" in sql
    assert "daily_statistics.date = '2026-04-28'" in sql


async def test_aggregate_maps_null_sums_to_zero():
    session = FakeAsyncSession(
        [
            FakeExecuteResult(
                one_value=row(
                    testing_exercises=None,
                    new_words=2,
                    irregular_verbs=None,
                    new_users=1,
                )
            )
        ]
    )
    repo = DailyStatisticsRepository(session_maker=FakeSessionMaker(session))

    result = await repo.aggregate(date(2026, 4, 1), date(2026, 4, 28))

    assert result == {
        "testing_exercises": 0,
        "new_words": 2,
        "irregular_verbs": 0,
        "new_users": 1,
    }
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "daily_statistics.date >= '2026-04-01'" in sql
    assert "daily_statistics.date <= '2026-04-28'" in sql
