from __future__ import annotations

import typing as t

from sqlalchemy import select, func, update, delete, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from db.init import get_session_maker
from db.models import TestingExercise, UserProgress


class TestingRepository:

    def __init__(self, session_maker: t.Callable[[], AsyncSession] | None = None) -> None:
        self._session_maker = session_maker or get_session_maker()

    # ─────────────────────────────── READ ──────────────────────────────── #

    async def get_max_exercise_id(self, section: str, subsection: str) -> int:
        async with self._session_maker() as session:
            result = await session.execute(
                select(func.max(TestingExercise.id))
                .filter_by(section=section, subsection=subsection)
            )
            return result.scalar() or 0

    async def list_exercises(self, subsection: str) -> list[TestingExercise]:
        async with self._session_maker() as session:
            result = await session.execute(
                select(TestingExercise)
                .filter_by(subsection=subsection)
                .order_by(TestingExercise.id)
            )
            return list(result.scalars().all())

    async def count_exercises(self, section: str, subsection: str) -> int:
        async with self._session_maker() as session:
            result = await session.execute(
                select(func.count())
                .select_from(TestingExercise)
                .where(
                    TestingExercise.section == section,
                    TestingExercise.subsection == subsection,
                )
            )
            return result.scalar() or 0

    async def get_available_exercises(
            self, section: str, subsection: str, user_id: int
    ) -> list[TestingExercise]:
        async with self._session_maker() as session:
            completed_ex_ids = (
                select(UserProgress.exercise_id)
                .where(
                    UserProgress.user_id == user_id,
                    UserProgress.exercise_section == section,
                    UserProgress.exercise_subsection == subsection,
                    UserProgress.success.is_(True),
                )
            )

            result = await session.execute(
                select(TestingExercise).where(
                    TestingExercise.section == section,
                    TestingExercise.subsection == subsection,
                    TestingExercise.id.not_in(completed_ex_ids),
                )
            )
            return list(result.scalars().all())

    async def get_section_names(self) -> list[str]:
        async with self._session_maker() as session:
            result = await session.execute(
                select(distinct(TestingExercise.section)).order_by(TestingExercise.section)
            )
            return list(result.scalars().all())

    async def get_subsection_names(self, section: str) -> list[str]:
        async with self._session_maker() as session:
            result = await session.execute(
                select(distinct(TestingExercise.subsection))
                .filter_by(section=section)
                .order_by(TestingExercise.subsection)
            )
            return list(result.scalars().all())

    # ────────────────────────────── WRITE ──────────────────────────────── #

    async def add_exercise(self, exercise: TestingExercise) -> None:
        async with self._session_maker() as session, session.begin():
            session.add(exercise)

    async def update_exercise(
            self,
            section: str,
            subsection: str,
            index: int,
            test: str,
            answer: str,
    ) -> None:
        async with self._session_maker() as session, session.begin():
            await session.execute(
                update(TestingExercise)
                .where(
                    TestingExercise.section == section,
                    TestingExercise.subsection == subsection,
                    TestingExercise.id == index,
                )
                .values(test=test, answer=answer)
            )

    async def delete_exercise(self, section: str, subsection: str, index: int) -> None:
        async with self._session_maker() as session, session.begin():
            await session.execute(
                delete(TestingExercise).where(
                    TestingExercise.section == section,
                    TestingExercise.subsection == subsection,
                    TestingExercise.id == index,
                )
            )
