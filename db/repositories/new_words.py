from __future__ import annotations

import typing as t

from sqlalchemy import select, func, update, delete, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from db.init import get_session_maker
from db.models import NewWords


class NewWordsRepository:

    def __init__(self, session_maker: t.Callable[[], AsyncSession] | None = None) -> None:
        self._session_maker = session_maker or get_session_maker()

    # ─────────────────────────────── READ ──────────────────────────────── #

    async def get_max_exercise_id(self, section: str, subsection: str) -> int:
        async with self._session_maker() as session:
            result = await session.execute(
                select(func.max(NewWords.id))
                .filter_by(section=section, subsection=subsection)
            )
            return result.scalar() or 0

    async def list_exercises(self, subsection: str) -> list[NewWords]:
        async with self._session_maker() as session:
            result = await session.execute(
                select(NewWords)
                .filter_by(subsection=subsection)
                .order_by(NewWords.id)
            )
            return list(result.scalars().all())

    async def count_exercises(self, section: str, subsection: str) -> int:
        async with self._session_maker() as session:
            result = await session.execute(
                select(func.count())
                .select_from(NewWords)
                .where(
                    NewWords.section == section,
                    NewWords.subsection == subsection,
                )
            )
            return result.scalar() or 0

    async def get_subsection_names(self, section: str) -> list[str]:
        async with self._session_maker() as session:
            result = await session.execute(
                select(distinct(NewWords.subsection))
                .filter_by(section=section)
                .order_by(NewWords.subsection)
            )
            return list(result.scalars().all())

    # ────────────────────────────── WRITE ──────────────────────────────── #

    async def add_exercise(self, exercise: NewWords) -> None:
        async with self._session_maker() as session, session.begin():
            session.add(exercise)

    async def update_exercise(
            self,
            section: str,
            subsection: str,
            index: int,
            russian: str,
            english: str,
    ) -> None:
        async with self._session_maker() as session, session.begin():
            await session.execute(
                update(NewWords)
                .where(
                    NewWords.section == section,
                    NewWords.subsection == subsection,
                    NewWords.id == index,
                )
                .values(russian=russian, english=english)
            )

    async def delete_exercise(self, section: str, subsection: str, index: int) -> None:
        async with self._session_maker() as session, session.begin():
            await session.execute(
                delete(NewWords).where(
                    NewWords.section == section,
                    NewWords.subsection == subsection,
                    NewWords.id == index,
                )
            )
