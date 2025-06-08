from __future__ import annotations

import typing as t
from datetime import date
from typing import Any, Callable, Coroutine

from sqlalchemy import (
    select,
    update,
    delete,
    func,
    desc,
)
from sqlalchemy.ext.asyncio import AsyncSession

from db.init import get_session_maker
from db.models import (
    UserProgress,
    User,
    TestingExercise,
)


class UserProgressRepository:

    # ──────────────────────────── infra ─────────────────────────── #

    def __init__(self, session_maker: t.Callable[[], AsyncSession] | None = None):
        self._session_maker = session_maker or get_session_maker()

    # helpers
    async def _scalar(self, stmt):
        async with self._session_maker() as session:
            return (await session.execute(stmt)).scalar()

    async def _scalars(self, stmt):
        async with self._session_maker() as session:
            return (await session.execute(stmt)).scalars().all()

    async def _fetchall(self, stmt):
        async with self._session_maker() as session:
            return (await session.execute(stmt)).fetchall()

    # ───────────────────────────── WRITE ────────────────────────── #

    async def update_progress_attempt(
            self,
            user_id: int,
            exercise_type: str,
            section: str,
            subsection: str,
            exercise_id: int,
            success: bool,
    ) -> int:
        async with self._session_maker() as session, session.begin():
            stmt = (
                update(UserProgress)
                .where(
                    UserProgress.user_id == user_id,
                    UserProgress.exercise_type == exercise_type,
                    UserProgress.exercise_section == section,
                    UserProgress.exercise_subsection == subsection,
                    UserProgress.exercise_id == exercise_id,
                )
                .values(
                    attempts=UserProgress.attempts + 1,
                    success=success,
                    date=date.today(),
                )
            )
            result = await session.execute(stmt)
            return result.rowcount

    async def add_progress_entry(self, entry: UserProgress) -> None:
        async with self._session_maker() as session, session.begin():
            session.add(entry)

    async def update_user_points(self, user_id: int, delta: int) -> None:
        async with self._session_maker() as session, session.begin():
            stmt = update(User).where(User.user_id == user_id).values(points=User.points + delta)
            await session.execute(stmt)

    async def delete_progress_by_subsection(
            self, user_id: int, section: str, subsection: str
    ) -> None:
        async with self._session_maker() as session, session.begin():
            stmt = delete(UserProgress).where(
                UserProgress.exercise_section == section,
                UserProgress.exercise_subsection == subsection,
                UserProgress.user_id == user_id,
            )
            await session.execute(stmt)

    # ───────────────────────────── READ ─────────────────────────── #

    # --- counts for Testing section ---
    async def count_success_testing(
            self, user_id: int, section: str, subsection: str, first_try_only: bool = False
    ) -> int:
        stmt = select(func.count()).select_from(UserProgress).where(
            UserProgress.user_id == user_id,
            UserProgress.exercise_type == "Testing",
            UserProgress.exercise_section == section,
            UserProgress.exercise_subsection == subsection,
            UserProgress.success.is_(True),
        )
        if first_try_only:
            stmt = stmt.where(UserProgress.attempts == 1)
        return await self._scalar(stmt) or 0

    async def count_testing_exercises_total(
            self, section: str, subsection: str
    ) -> int:
        stmt = select(func.count()).select_from(TestingExercise).where(
            TestingExercise.section == section, TestingExercise.subsection == subsection
        )
        return await self._scalar(stmt) or 0

    # --- generic activity ---
    async def count_by_type_in_interval(
            self,
            user_id: int,
            exercise_type: str,
            start: date,
            end: date,
    ) -> int:
        stmt = select(func.count()).select_from(UserProgress).where(
            UserProgress.exercise_type == exercise_type,
            UserProgress.date >= start,
            UserProgress.date <= end,
            UserProgress.user_id == user_id,
        )
        return await self._scalar(stmt) or 0

    # --- user points / ranks ---
    async def get_user_points(self, user_id: int) -> int:
        stmt = select(User.points).where(User.user_id == user_id)
        return await self._scalar(stmt) or 0

    async def count_users_with_points_greater(self, points: int) -> int:
        stmt = select(func.count()).select_from(User).where(User.points > points)
        return await self._scalar(stmt) or 0

    async def total_users(self) -> int:
        stmt = select(func.count()).select_from(User)
        return await self._scalar(stmt) or 0

    async def list_users_ordered_by_points(self):
        stmt = select(
            User.id,
            User.user_id,
            User.full_name,
            User.tg_login,
            User.points,
        ).order_by(desc(User.points))
        return await self._fetchall(stmt)
