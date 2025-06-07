from __future__ import annotations

from datetime import date

from db.repositories.daily_statistics import DailyStatisticsRepository


class DailyStatisticsService:
    _TYPE_TO_FIELD = {
        "new_words": "total_new_words",
        "testing_exercises": "total_testing_exercises",
        "irregular_verbs": "total_irregular_verbs",
        "new_user": "new_users",
    }

    def __init__(
            self, repository: DailyStatisticsRepository | None = None
    ) -> None:
        self._repo = repository or DailyStatisticsRepository()

    # ─────────────────────────── PUBLIC API ─────────────────────────── #

    async def update(self, update_type: str) -> None:
        field = self._TYPE_TO_FIELD.get(update_type)
        if field is None:
            return

        today = date.today()

        # ensure row exists
        stats = await self._repo.get_by_date(today)
        if stats is None:
            await self._repo.create_blank_for_date(today)

        # increment field
        await self._repo.increment_field(today, field)

    async def get(self, start_date: date, end_date: date) -> dict[str, int]:
        return await self._repo.aggregate(start_date, end_date)
