from datetime import date

from bot.db.repositories.user_progress import UserProgressRepository
from tests.fakes import (
    FakeAsyncSession,
    FakeExecuteResult,
    FakeSessionMaker,
    row,
    statement_sql,
)


async def test_update_progress_attempt_filters_by_user_and_exercise_key():
    session = FakeAsyncSession([FakeExecuteResult(rowcount=1)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.update_progress_attempt(
        user_id=123,
        exercise_type="Testing",
        section="Grammar",
        subsection="Present Simple",
        exercise_id=5,
        success=True,
    )

    assert result == 1
    session.begin.assert_called_once_with()
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "update user_progress" in sql
    assert "user_progress.user_id = 123" in sql
    assert "user_progress.exercise_type = 'testing'" in sql
    assert "user_progress.exercise_section = 'grammar'" in sql
    assert "user_progress.exercise_subsection = 'present simple'" in sql
    assert "user_progress.exercise_id = 5" in sql


async def test_count_success_testing_adds_first_try_filter_when_requested():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=2)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_success_testing(
        user_id=123,
        section="Grammar",
        subsection="Present Simple",
        first_try_only=True,
    )

    assert result == 2
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from user_progress" in sql
    assert "user_progress.success is true" in sql
    assert "user_progress.attempts = 1" in sql


async def test_count_by_type_in_interval_uses_closed_date_bounds():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=4)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_by_type_in_interval(
        user_id=123,
        exercise_type="Testing",
        start=date(2026, 4, 1),
        end=date(2026, 4, 28),
    )

    assert result == 4
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_progress.date >= '2026-04-01'" in sql
    assert "user_progress.date <= '2026-04-28'" in sql
    assert "user_progress.user_id = 123" in sql


async def test_list_users_ordered_by_points_returns_raw_rows():
    rows = [
        row(id=1, user_id=123, full_name="One", tg_login="one", points=10),
        row(id=2, user_id=456, full_name="Two", tg_login="two", points=5),
    ]
    session = FakeAsyncSession([FakeExecuteResult(fetchall_values=rows)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.list_users_ordered_by_points()

    assert result == rows
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from users" in sql
    assert "order by users.points desc" in sql
