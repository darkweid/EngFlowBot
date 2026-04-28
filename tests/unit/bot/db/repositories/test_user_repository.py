from datetime import time

from bot.db.repositories.user import UserRepository
from tests.factories import build_user
from tests.fakes import (
    FakeAsyncSession,
    FakeExecuteResult,
    FakeSessionMaker,
    statement_sql,
)


async def test_get_by_user_id_filters_by_telegram_user_id():
    user = build_user(user_id=123)
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=user)])
    repo = UserRepository(session_maker=FakeSessionMaker(session))

    result = await repo.get_by_user_id(123)

    assert result is user
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from users" in sql
    assert "users.user_id = 123" in sql


async def test_list_all_returns_users_ordered_by_internal_id():
    users = [build_user(id_=1), build_user(id_=2, user_id=456)]
    session = FakeAsyncSession([FakeExecuteResult(scalar_values=users)])
    repo = UserRepository(session_maker=FakeSessionMaker(session))

    result = await repo.list_all()

    assert result == users
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from users" in sql
    assert "order by users.id" in sql


async def test_add_user_adds_orm_object_inside_transaction():
    user = build_user()
    session = FakeAsyncSession()
    repo = UserRepository(session_maker=FakeSessionMaker(session))

    await repo.add(user)

    session.begin.assert_called_once_with()
    session.add.assert_called_once_with(user)


async def test_update_basic_info_mutates_user_and_persists_it():
    user = build_user(full_name="Old", tg_login="old")
    session = FakeAsyncSession()
    repo = UserRepository(session_maker=FakeSessionMaker(session))

    await repo.update_basic_info(user, full_name="New Name", tg_login="new_login")

    assert user.full_name == "New Name"
    assert user.tg_login == "new_login"
    session.begin.assert_called_once_with()
    session.add.assert_called_once_with(user)


async def test_set_reminder_time_filters_by_user_id():
    session = FakeAsyncSession([FakeExecuteResult()])
    repo = UserRepository(session_maker=FakeSessionMaker(session))

    await repo.set_reminder_time(123, time(9, 30))

    session.begin.assert_called_once_with()
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "update users" in sql
    assert "users.user_id = 123" in sql
