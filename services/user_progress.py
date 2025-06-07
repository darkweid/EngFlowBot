from __future__ import annotations

from datetime import date, datetime, timedelta

from db.models import UserProgress
from db.repositories.user_progress import UserProgressRepository


class UserProgressService:

    def __init__(self, repository: UserProgressRepository | None = None) -> None:
        self._repo = repository or UserProgressRepository()

    # ───────────────────────── mark / update ───────────────────────── #

    async def mark_exercise_completed(
            self,
            user_id: int,
            exercise_type: str,
            subsection: str,
            section: str,
            exercise_id: int,
            success: bool,
    ) -> bool:
        """
        Returns True if this was the user's first attempt to solve
        a specific exercise (i.e. there was no record yet), otherwise False.
        """
        rowcount = await self._repo.update_progress_attempt(
            user_id,
            exercise_type,
            section,
            subsection,
            exercise_id,
            success,
        )

        await self._repo.update_user_points(user_id, 1 if success else -1)

        first_try = rowcount == 0
        if first_try:
            entry = UserProgress(
                user_id=user_id,
                exercise_type=exercise_type,
                exercise_section=section,
                exercise_subsection=subsection,
                exercise_id=exercise_id,
                attempts=1,
                success=success,
                date=date.today(),
            )
            await self._repo.add_progress_entry(entry)

        return first_try

    async def delete_progress_by_subsection(
            self, user_id: int, section: str, subsection: str
    ) -> None:
        await self._repo.delete_progress_by_subsection(user_id, section, subsection)

    # ───────────────────────── statistics & info ──────────────────────── #

    async def get_counts_completed_exercises_testing(
            self, user_id: int, section: str, subsection: str
    ) -> tuple[int, int, int]:
        first_try_success = await self._repo.count_success_testing(
            user_id, section, subsection, first_try_only=True
        )
        success = await self._repo.count_success_testing(
            user_id, section, subsection, first_try_only=False
        )
        total = await self._repo.count_testing_exercises_total(section, subsection)
        return first_try_success, success, total

    async def get_activity_by_user(self, user_id: int, interval: int = 0) -> str:
        """
        interval = 0 → today, 7 → last week, 30 → last month.
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=interval)

        result_testing = await self._repo.count_by_type_in_interval(
            user_id, "Testing", start_date, end_date
        )
        result_new_words = await self._repo.count_by_type_in_interval(
            user_id, "New words", start_date, end_date
        )
        result_irregular_verbs = await self._repo.count_by_type_in_interval(
            user_id, "Irregular verbs", start_date, end_date
        )

        if interval == 0:
            text = "сегодня"
        elif interval == 7:
            text = "последнюю неделю"
        elif interval == 30:
            text = "последний месяц"
        else:
            text = f"последние {interval} дн."

        return (
            f"Твоя статистика за <b>{text}</b>:\n"
            f"Тестирование: {result_testing}\n"
            f"Изучение новых слов: {result_new_words}\n"
            f"Неправильные глаголы: {result_irregular_verbs}\n"
        )

    async def get_user_points(self, user_id: int) -> int:
        return await self._repo.get_user_points(user_id)

    async def get_user_rank_and_total(
            self, user_id: int, medals_rank: bool = False
    ) -> tuple[str | int, int]:
        points = await self._repo.get_user_points(user_id)
        higher = await self._repo.count_users_with_points_greater(points)
        total = await self._repo.total_users()
        rank: int | str = higher + 1

        if medals_rank:
            if rank == 1:
                rank = "🥇"
            elif rank == 2:
                rank = "🥈"
            elif rank == 3:
                rank = "🥉"

        return rank, total

    async def get_all_users_ranks_and_points(
            self, medals_rank: bool = False
    ) -> list[dict[str, str]]:
        users = await self._repo.list_users_ordered_by_points()
        users_with_ranks: list[dict[str, str]] = []

        for idx, user in enumerate(users, start=1):
            rank_display: str | int = idx
            if medals_rank:
                if idx == 1:
                    rank_display = "🥇"
                elif idx == 2:
                    rank_display = "🥈"
                elif idx == 3:
                    rank_display = "🥉"

            users_with_ranks.append(
                {
                    "rank": str(rank_display),
                    "user_id": str(user.user_id),
                    "full_name": user.full_name,
                    "tg_login": user.tg_login,
                    "points": str(user.points),
                }
            )

        return users_with_ranks
