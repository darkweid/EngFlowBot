from __future__ import annotations

from datetime import datetime, time as tm

from db.models import User
from db.repositories.user import UserRepository
from loggers import get_logger

logger = get_logger(__name__)


class UserService:

    def __init__(self, repository: UserRepository | None = None) -> None:
        self._repo = repository or UserRepository()

    # ─────────────────────────── PUBLIC API ─────────────────────────── #

    async def add_user(self, user_id: int, full_name: str, tg_login: str) -> None:
        existing = await self._repo.get_by_user_id(user_id)

        if existing:
            if existing.full_name != full_name or existing.tg_login != tg_login:
                await self._repo.update_basic_info(existing, full_name, tg_login)
                logger.info(f"User {user_id}:{full_name} information updated.")
            else:
                logger.info(
                    f"User {user_id}:{full_name} already exists with the same information."
                )
            return

        user = User(
            registration_date=datetime.utcnow(),
            user_id=user_id,
            full_name=full_name,
            tg_login=tg_login,
            reminder_time=None,
            time_zone=None,
        )
        await self._repo.add(user)
        logger.info(f"User {full_name} added successfully.")

    async def delete_user(self, user_id: int) -> None:
        await self._repo.delete_by_user_id(user_id)

    async def set_timezone(self, user_id: int, timezone: str | None) -> None:
        await self._repo.set_timezone(user_id, timezone)

    async def set_reminder_time(self, user_id: int, time: tm | None) -> None:
        await self._repo.set_reminder_time(user_id, time)

    async def get_all_users(self) -> tuple[dict, ...]:
        users = await self._repo.list_all()
        return tuple(
            {
                "id": u.id,
                "user_id": u.user_id,
                "full_name": u.full_name,
                "tg_login": u.tg_login,
                "registration_date": u.registration_date,
                "points": u.points,
                "reminder_time": u.reminder_time,
                "time_zone": u.time_zone,
            }
            for u in users
        )

    async def get_user(self, user_id: int) -> dict | None:
        user = await self._repo.get_by_user_id(user_id)
        if user is None:
            return None
        return {
            "id": user.id,
            "user_id": user.user_id,
            "full_name": user.full_name,
            "tg_login": user.tg_login,
            "registration_date": user.registration_date,
            "points": user.points,
            "reminder_time": user.reminder_time,
            "time_zone": user.time_zone,
        }

    async def get_user_info_text(self, user_id: int, admin: bool = True) -> str | None:
        user = await self._repo.get_by_user_id(user_id)
        if not user:
            return None

        info = ""
        if admin:
            info += (
                f"Имя: {user.full_name}\n"
                f"telegram: @{user.tg_login}\n"
                f"telegram id: {user.user_id}\n"
                f"Баллов: {user.points}\n"
            )

        info += (
            f"Дата регистрации: {user.registration_date.strftime('%d-%m-%Y | %H:%M UTC')}\n"
            f"Время напоминаний: {user.reminder_time if user.reminder_time else 'Не установлено'}\n"
            f"Часовой пояс: {user.time_zone if user.time_zone else 'Не установлен'}"
        )

        return info
