from __future__ import annotations

import typing as t
from datetime import date

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.init import get_session_maker
from db.models import DailyStatistics


class DailyStatisticsRepository:

    def __init__(self, session_maker: t.Callable[[], AsyncSession] | None = None) -> None:
        self._session_maker = session_maker or get_session_maker()

    # ───────────────────────── helpers ───────────────────────── #

    async def _scalar(self, stmt):
        async with self._session_maker() as session:
            return (await session.execute(stmt)).scalar_one_or_none()

    # ───────────────────────── CRUD ──────────────────────────── #

    async def get_by_date(self, day: date) -> DailyStatistics | None:
        stmt = select(DailyStatistics).filter_by(date=day)
        return await self._scalar(stmt)

    async def create_blank_for_date(self, day: date) -> DailyStatistics:
        stats = DailyStatistics(
            date=day,
            total_new_words=0,
            total_testing_exercises=0,
            total_irregular_verbs=0,
            new_users=0,
        )
        async with self._session_maker() as session, session.begin():
            session.add(stats)
        return stats

    async def increment_field(
            self, day: date, field_name: str, amount: int = 1
    ) -> None:
        async with self._session_maker() as session, session.begin():
            await session.execute(
                update(DailyStatistics)
                .where(DailyStatistics.date == day)
                .values({field_name: getattr(DailyStatistics, field_name) + amount})
            )

    # ──────────────────────── aggregation ────────────────────── #

    async def aggregate(
            self, start_date: date, end_date: date
    ) -> dict[str, int]:
        stmt = (
            select(
                func.sum(DailyStatistics.total_testing_exercises).label(
                    "testing_exercises"
                ),
                func.sum(DailyStatistics.total_new_words).label("new_words"),
                func.sum(DailyStatistics.total_irregular_verbs).label(
                    "irregular_verbs"
                ),
                func.sum(DailyStatistics.new_users).label("new_users"),
            )
            .where(DailyStatistics.date >= start_date)
            .where(DailyStatistics.date <= end_date)
        )
        async with self._session_maker() as session:
            row = (await session.execute(stmt)).one()
        return {
            "testing_exercises": row.testing_exercises or 0,
            "new_words": row.new_words or 0,
            "irregular_verbs": row.irregular_verbs or 0,
            "new_users": row.new_users or 0,
        }
