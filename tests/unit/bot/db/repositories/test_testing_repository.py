from bot.db.repositories.testing import TestingRepository as _TestingRepository
from tests.factories import build_testing_exercise
from tests.fakes import (
    FakeAsyncSession,
    FakeExecuteResult,
    FakeSessionMaker,
    statement_sql,
)


async def test_get_available_exercises_excludes_completed_successes_for_user():
    exercise = build_testing_exercise()
    session = FakeAsyncSession([FakeExecuteResult(scalar_values=[exercise])])
    repo = _TestingRepository(session_maker=FakeSessionMaker(session))

    result = await repo.get_available_exercises(
        section="Grammar",
        subsection="Present Simple",
        user_id=123,
    )

    assert result == [exercise]
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "testing_exercises" in sql
    assert "user_progress" in sql
    assert "user_progress.user_id = 123" in sql
    assert "user_progress.exercise_section = 'grammar'" in sql
    assert "user_progress.exercise_subsection = 'present simple'" in sql
    assert "user_progress.success is true" in sql


async def test_add_exercise_adds_orm_object_inside_transaction():
    exercise = build_testing_exercise()
    session = FakeAsyncSession()
    repo = _TestingRepository(session_maker=FakeSessionMaker(session))

    await repo.add_exercise(exercise)

    session.begin.assert_called_once_with()
    session.add.assert_called_once_with(exercise)


async def test_update_exercise_filters_by_composite_exercise_key():
    session = FakeAsyncSession([FakeExecuteResult()])
    repo = _TestingRepository(session_maker=FakeSessionMaker(session))

    await repo.update_exercise(
        section="Grammar",
        subsection="Present Simple",
        index=7,
        test="He ... here.",
        answer="works",
    )

    session.begin.assert_called_once_with()
    session.execute.assert_awaited_once()
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "update testing_exercises" in sql
    assert "testing_exercises.section = 'grammar'" in sql
    assert "testing_exercises.subsection = 'present simple'" in sql
    assert "testing_exercises.id = 7" in sql


async def test_delete_exercise_filters_by_composite_exercise_key():
    session = FakeAsyncSession([FakeExecuteResult()])
    repo = _TestingRepository(session_maker=FakeSessionMaker(session))

    await repo.delete_exercise("Grammar", "Present Simple", 7)

    session.begin.assert_called_once_with()
    session.execute.assert_awaited_once()
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "delete from testing_exercises" in sql
    assert "testing_exercises.section = 'grammar'" in sql
    assert "testing_exercises.subsection = 'present simple'" in sql
    assert "testing_exercises.id = 7" in sql
