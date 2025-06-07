from __future__ import annotations

import typing as t
from datetime import date

from sqlalchemy import select, update, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from db.init import get_session_maker
from db.models import (
    UserWordsLearning,
    NewWords,
    User,
)


class UserWordsLearningRepository:

    def __init__(self, session_maker: t.Callable[[], AsyncSession] | None = None) -> None:
        self._session_maker = session_maker or get_session_maker()

    # ─────────────────────────────── READ ──────────────────────────────── #

    async def words_to_learn_today(self, user_id: int) -> list[UserWordsLearning]:
        async with self._session_maker() as session:
            stmt = (
                select(UserWordsLearning)
                .filter(
                    UserWordsLearning.user_id == user_id,
                    UserWordsLearning.next_review_date <= date.today(),
                )
                .options(joinedload(UserWordsLearning.new_word))
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def all_words_by_section_subsection(
            self, user_id: int, section: str, subsection: str
    ) -> list[UserWordsLearning]:
        async with self._session_maker() as session:
            stmt = (
                select(UserWordsLearning)
                .filter(
                    UserWordsLearning.user_id == user_id,
                    UserWordsLearning.section == section,
                    UserWordsLearning.subsection == subsection,
                )
                .options(joinedload(UserWordsLearning.new_word))
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def all_words_by_user(self, user_id: int) -> list[UserWordsLearning]:
        async with self._session_maker() as session:
            stmt = (
                select(UserWordsLearning)
                .filter(UserWordsLearning.user_id == user_id)
                .options(joinedload(UserWordsLearning.new_word))
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_active_learning(
            self, user_id: int, active_rate: int
    ) -> int:
        async with self._session_maker() as session:
            stmt = select(func.count(UserWordsLearning.exercise_id)).where(
                UserWordsLearning.user_id == user_id,
                UserWordsLearning.success <= active_rate,
            )
            result = await session.execute(stmt)

            return result.scalar() or 0

    async def count_active_in_subsection(self, user_id: int, subsection: str, learning_rate: int) -> int:
        async with self._session_maker() as session:
            stmt = select(func.count(UserWordsLearning.exercise_id)).where(
                UserWordsLearning.subsection == subsection,
                UserWordsLearning.user_id == user_id,
                UserWordsLearning.success <= learning_rate)
            result = await session.execute(stmt)
            return result.scalar()

    async def count_learned(
            self, user_id: int, learned_rate: int
    ) -> int:
        async with self._session_maker() as session:
            stmt = select(func.count(UserWordsLearning.exercise_id)).where(
                UserWordsLearning.user_id == user_id,
                UserWordsLearning.success >= learned_rate,
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def count_all_by_user(self, user_id: int) -> int:
        async with self._session_maker() as session:
            stmt = select(func.count(UserWordsLearning.exercise_id)).where(
                UserWordsLearning.user_id == user_id
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def count_all_today_by_user(self, user_id: int) -> int:
        async with self._session_maker() as session:
            stmt = select(func.count(UserWordsLearning.exercise_id)).where(
                UserWordsLearning.user_id == user_id,
                UserWordsLearning.next_review_date <= date.today(),
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def distinct_subsections(self, user_id: int) -> list[str]:
        async with self._session_maker() as session:
            stmt = select(distinct(UserWordsLearning.subsection)).filter(UserWordsLearning.user_id == user_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_learned_in_subsection(
            self, user_id: int, subsection: str, learned_rate: int
    ) -> int:
        async with self._session_maker() as session:
            stmt = select(func.count(UserWordsLearning.exercise_id)).where(
                UserWordsLearning.subsection == subsection,
                UserWordsLearning.user_id == user_id,
                UserWordsLearning.success >= learned_rate,
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def count_today_in_subsection(
            self, user_id: int, subsection: str
    ) -> int:
        async with self._session_maker() as session:
            stmt = select(func.count(UserWordsLearning.exercise_id)).where(
                UserWordsLearning.subsection == subsection,
                UserWordsLearning.user_id == user_id,
                UserWordsLearning.next_review_date <= date.today(),
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def count_total_in_subsection(
            self, user_id: int, subsection: str
    ) -> int:
        async with self._session_maker() as session:
            stmt = select(func.count(UserWordsLearning.exercise_id)).where(
                UserWordsLearning.subsection == subsection,
                UserWordsLearning.user_id == user_id,
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def sum_success_in_subsection(
            self, user_id: int, subsection: str
    ) -> int:
        async with self._session_maker() as session:
            stmt = select(func.sum(UserWordsLearning.success)).where(
                UserWordsLearning.subsection == subsection,
                UserWordsLearning.user_id == user_id,
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def sum_attempts_in_subsection(
            self, user_id: int, subsection: str
    ) -> int:
        async with self._session_maker() as session:
            stmt = select(func.sum(UserWordsLearning.attempts)).where(
                UserWordsLearning.subsection == subsection,
                UserWordsLearning.user_id == user_id,
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def learning_info(
            self, user_id: int, section: str, subsection: str, exercise_id: int
    ) -> UserWordsLearning | None:
        async with self._session_maker() as session:
            stmt = (
                select(UserWordsLearning)
                .where(
                    UserWordsLearning.user_id == user_id,
                    UserWordsLearning.section == section,
                    UserWordsLearning.subsection == subsection,
                    UserWordsLearning.exercise_id == exercise_id,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    # ────────────────────────────── WRITE ──────────────────────────────── #

    async def update_user_points(self, user_id: int, delta: int) -> None:
        async with self._session_maker() as session, session.begin():
            await session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(points=User.points + delta)
            )

    async def update_learning_progress(
            self,
            section: str,
            subsection: str,
            exercise_id: int,
            success_value: int,
            next_review_date: date,
    ) -> None:
        async with self._session_maker() as session, session.begin():
            await session.execute(
                update(UserWordsLearning)
                .where(
                    UserWordsLearning.section == section,
                    UserWordsLearning.subsection == subsection,
                    UserWordsLearning.exercise_id == exercise_id,
                )
                .values(
                    success=success_value,
                    next_review_date=next_review_date,
                    attempts=UserWordsLearning.attempts + 1,
                )
            )

    async def list_new_words(self, section: str, subsection: str) -> list[NewWords]:
        async with self._session_maker() as session:
            stmt = (
                select(NewWords)
                .filter_by(section=section, subsection=subsection)
                .order_by(NewWords.id)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def add_user_words_learning_entries(
            self, entries: list[UserWordsLearning]
    ) -> None:
        async with self._session_maker() as session, session.begin():
            session.add_all(entries)

    async def max_custom_word_id(self, user_id: int) -> int:
        async with self._session_maker() as session:
            stmt = select(func.max(NewWords.id)).filter_by(
                section=str(user_id), subsection=str(user_id)
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def add_new_word(self, word: NewWords) -> None:
        async with self._session_maker() as session, session.begin():
            session.add(word)

    async def add_user_words_learning_entry(
            self, entry: UserWordsLearning
    ) -> None:
        async with self._session_maker() as session, session.begin():
            session.add(entry)
