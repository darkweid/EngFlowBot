from __future__ import annotations

import typing as t

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.init import get_session_maker
from db.models import User


class UserRepository:

    def __init__(self, session_maker: t.Callable[[], AsyncSession] | None = None) -> None:
        self._session_maker = session_maker or get_session_maker()

    # ───────────────────────── helpers ───────────────────────── #

    async def _scalar(self, stmt):
        async with self._session_maker() as session:
            return (await session.execute(stmt)).scalar_one_or_none()

    async def _scalars(self, stmt):
        async with self._session_maker() as session:
            return (await session.execute(stmt)).scalars().all()

    # ───────────────────────── READ ──────────────────────────── #

    async def get_by_user_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.user_id == user_id)
        return await self._scalar(stmt)

    async def list_all(self) -> list[User]:
        stmt = select(User).order_by(User.id)
        return list(await self._scalars(stmt))

    # ───────────────────────── WRITE ─────────────────────────── #

    async def add(self, user: User) -> None:
        async with self._session_maker() as session, session.begin():
            session.add(user)

    async def update_basic_info(
            self, user: User, full_name: str, tg_login: str
    ) -> None:
        user.full_name = full_name
        user.tg_login = tg_login
        async with self._session_maker() as session, session.begin():
            session.add(user)

    async def delete_by_user_id(self, user_id: int) -> None:
        async with self._session_maker() as session, session.begin():
            stmt = delete(User).where(User.user_id == user_id)
            await session.execute(stmt)

    async def set_timezone(self, user_id: int, timezone: str | None) -> None:
        async with self._session_maker() as session, session.begin():
            stmt = update(User).where(User.user_id == user_id).values(time_zone=timezone)
            await session.execute(stmt)

    async def set_reminder_time(self, user_id: int, reminder_time: str | None) -> None:
        async with self._session_maker() as session, session.begin():
            stmt = update(User).where(User.user_id == user_id).values(reminder_time=reminder_time)
            await session.execute(stmt)
