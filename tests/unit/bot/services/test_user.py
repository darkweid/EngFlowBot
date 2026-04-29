from datetime import datetime, time
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.db.models import User
from bot.services.user import UserService
from tests.factories import build_user


def make_repo(**overrides):
    defaults = {
        "get_by_user_id": AsyncMock(return_value=None),
        "update_basic_info": AsyncMock(),
        "add": AsyncMock(),
        "delete_by_user_id": AsyncMock(),
        "set_timezone": AsyncMock(),
        "set_reminder_time": AsyncMock(),
        "list_all": AsyncMock(return_value=[]),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


async def test_add_user_creates_new_user_when_missing():
    repo = make_repo(get_by_user_id=AsyncMock(return_value=None))
    service = UserService(repository=repo)

    await service.add_user(123, "Mark", "mark_login")

    repo.get_by_user_id.assert_awaited_once_with(123)
    repo.add.assert_awaited_once()
    user = repo.add.await_args.args[0]
    assert isinstance(user, User)
    assert user.user_id == 123
    assert user.full_name == "Mark"
    assert user.tg_login == "mark_login"
    assert user.registration_date.tzinfo is None
    assert user.reminder_time is None
    assert user.time_zone is None
    repo.update_basic_info.assert_not_awaited()


async def test_add_user_updates_existing_user_when_identity_changed():
    existing = build_user(user_id=123, full_name="Old Name", tg_login="old")
    repo = make_repo(get_by_user_id=AsyncMock(return_value=existing))
    service = UserService(repository=repo)

    await service.add_user(123, "New Name", "new")

    repo.update_basic_info.assert_awaited_once_with(existing, "New Name", "new")
    repo.add.assert_not_awaited()


async def test_add_user_skips_write_when_existing_user_is_unchanged():
    existing = build_user(user_id=123, full_name="Mark", tg_login="mark_login")
    repo = make_repo(get_by_user_id=AsyncMock(return_value=existing))
    service = UserService(repository=repo)

    await service.add_user(123, "Mark", "mark_login")

    repo.update_basic_info.assert_not_awaited()
    repo.add.assert_not_awaited()


async def test_get_user_returns_none_when_missing():
    repo = make_repo(get_by_user_id=AsyncMock(return_value=None))
    service = UserService(repository=repo)

    result = await service.get_user(404)

    assert result is None
    repo.get_by_user_id.assert_awaited_once_with(404)


async def test_get_user_maps_model_to_dict():
    reminder = time(9, 30)
    registration = datetime(2026, 1, 2, 3, 4)
    user = build_user(
        id_=9,
        user_id=123,
        full_name="Mark",
        tg_login="mark_login",
        points=15,
        registration_date=registration,
        reminder_time=reminder,
        time_zone="Europe/Moscow",
    )
    repo = make_repo(get_by_user_id=AsyncMock(return_value=user))
    service = UserService(repository=repo)

    result = await service.get_user(123)

    assert result == {
        "id": 9,
        "user_id": 123,
        "full_name": "Mark",
        "tg_login": "mark_login",
        "registration_date": registration,
        "points": 15,
        "reminder_time": reminder,
        "time_zone": "Europe/Moscow",
    }


async def test_get_all_users_maps_models_to_tuple_of_dicts():
    user = build_user(user_id=123, full_name="Mark", tg_login="mark_login")
    repo = make_repo(list_all=AsyncMock(return_value=[user]))
    service = UserService(repository=repo)

    result = await service.get_all_users()

    assert isinstance(result, tuple)
    assert result[0]["user_id"] == 123
    assert result[0]["full_name"] == "Mark"
    repo.list_all.assert_awaited_once_with()


async def test_get_user_info_text_returns_none_when_user_missing():
    repo = make_repo(get_by_user_id=AsyncMock(return_value=None))
    service = UserService(repository=repo)

    result = await service.get_user_info_text(404)

    assert result is None


async def test_get_user_info_text_includes_admin_fields_by_default():
    user = build_user(
        user_id=123,
        full_name="Mark",
        tg_login="mark_login",
        points=10,
        registration_date=datetime(2026, 1, 2, 3, 4),
        reminder_time=time(9, 30),
        time_zone="UTC",
    )
    repo = make_repo(get_by_user_id=AsyncMock(return_value=user))
    service = UserService(repository=repo)

    result = await service.get_user_info_text(123)

    assert "Имя: Mark" in result
    assert "telegram: @mark_login" in result
    assert "telegram id: 123" in result
    assert "Баллов: 10" in result
    assert "Дата регистрации: 02-01-2026 | 03:04 UTC" in result
    assert "Время напоминаний: 09:30:00" in result
    assert "Часовой пояс: UTC" in result


async def test_get_user_info_text_can_hide_admin_fields():
    user = build_user(
        user_id=123,
        full_name="Mark",
        tg_login="mark_login",
        registration_date=datetime(2026, 1, 2, 3, 4),
    )
    repo = make_repo(get_by_user_id=AsyncMock(return_value=user))
    service = UserService(repository=repo)

    result = await service.get_user_info_text(123, admin=False)

    assert "Имя:" not in result
    assert "telegram id:" not in result
    assert "Дата регистрации: 02-01-2026 | 03:04 UTC" in result
    assert "Время напоминаний: Не установлено" in result
    assert "Часовой пояс: Не установлен" in result


async def test_mutating_user_methods_delegate_to_repository():
    repo = make_repo()
    service = UserService(repository=repo)

    await service.delete_user(123)
    await service.set_timezone(123, "UTC")
    await service.set_reminder_time(123, time(9, 30))

    repo.delete_by_user_id.assert_awaited_once_with(123)
    repo.set_timezone.assert_awaited_once_with(123, "UTC")
    repo.set_reminder_time.assert_awaited_once_with(123, time(9, 30))
