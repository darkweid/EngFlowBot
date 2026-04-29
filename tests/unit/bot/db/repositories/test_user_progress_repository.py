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


async def test_count_success_testing_without_first_try_filter():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=3)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_success_testing(
        user_id=123,
        section="Grammar",
        subsection="Present Simple",
    )

    assert result == 3
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_progress.success is true" in sql
    assert "user_progress.attempts" not in sql


async def test_count_success_testing_returns_zero_when_no_rows():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=None)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_success_testing(
        user_id=123,
        section="Grammar",
        subsection="Present Simple",
    )

    assert result == 0


async def test_count_testing_exercises_total_counts_testing_exercises():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=12)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_testing_exercises_total("Grammar", "Present Simple")

    assert result == 12
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from testing_exercises" in sql
    assert "testing_exercises.section = 'grammar'" in sql
    assert "testing_exercises.subsection = 'present simple'" in sql


async def test_count_testing_exercises_total_returns_zero_when_no_rows():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=None)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_testing_exercises_total("Grammar", "Present Simple")

    assert result == 0


async def test_count_by_type_in_interval_returns_zero_when_no_rows():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=None)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_by_type_in_interval(
        user_id=123,
        exercise_type="Testing",
        start=date(2026, 4, 1),
        end=date(2026, 4, 28),
    )

    assert result == 0


async def test_add_progress_entry_adds_orm_object_inside_transaction():
    from tests.factories import build_user_progress

    entry = build_user_progress(user_id=123)
    session = FakeAsyncSession()
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    await repo.add_progress_entry(entry)

    session.begin.assert_called_once_with()
    session.add.assert_called_once_with(entry)


async def test_update_user_points_increments_points_inside_transaction():
    session = FakeAsyncSession([FakeExecuteResult()])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    await repo.update_user_points(123, 5)

    session.begin.assert_called_once_with()
    session.execute.assert_awaited_once()
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "update users" in sql
    assert "users.user_id = 123" in sql
    assert "points=" in sql.replace(" ", "")


async def test_delete_progress_by_subsection_filters_by_user_section_subsection():
    session = FakeAsyncSession([FakeExecuteResult()])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    await repo.delete_progress_by_subsection(
        user_id=123,
        section="Grammar",
        subsection="Present Simple",
    )

    session.begin.assert_called_once_with()
    session.execute.assert_awaited_once()
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "delete from user_progress" in sql
    assert "user_progress.user_id = 123" in sql
    assert "user_progress.exercise_section = 'grammar'" in sql
    assert "user_progress.exercise_subsection = 'present simple'" in sql


async def test_get_user_points_returns_zero_when_user_has_none():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=None)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.get_user_points(123)

    assert result == 0


async def test_get_user_points_returns_scalar_value():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=42)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.get_user_points(123)

    assert result == 42
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from users" in sql
    assert "users.user_id = 123" in sql


async def test_count_users_with_points_greater_filters_by_points():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=2)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_users_with_points_greater(10)

    assert result == 2
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from users" in sql
    assert "users.points > 10" in sql


async def test_total_users_counts_all_users():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=7)])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo.total_users()

    assert result == 7
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from users" in sql


async def test_internal_scalars_helper_returns_iterable_of_values():
    from sqlalchemy import select

    from bot.db.models import User

    session = FakeAsyncSession([FakeExecuteResult(scalar_values=[1, 2, 3])])
    repo = UserProgressRepository(session_maker=FakeSessionMaker(session))

    result = await repo._scalars(select(User))

    assert list(result) == [1, 2, 3]
