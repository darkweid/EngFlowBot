from __future__ import annotations

import random

from db.models import TestingExercise
from db.repositories.testing import TestingRepository


class TestingService:
    """
    Business-logic layer for testing exercises.
    Depends on a repository; can be easily mocked in tests.
    """

    def __init__(self, repository: TestingRepository | None = None) -> None:
        self._repo = repository or TestingRepository()

    # ──────────────────────────── PUBLIC API ───────────────────────────── #

    async def add_testing_exercise(
        self,
        section: str,
        subsection: str,
        test: str,
        answer: str,
    ) -> None:
        max_id = await self._repo.get_max_exercise_id(section, subsection)
        next_id = max_id + 1

        exercise = TestingExercise(
            section=section,
            subsection=subsection,
            id=next_id,
            test=test,
            answer=answer.replace(chr(160), ""),  # non-breaking space → plain space
        )
        await self._repo.add_exercise(exercise)

    async def get_testing_exercises(self, subsection: str) -> str:
        exercises = await self._repo.list_exercises(subsection)
        # Convert to human-readable string (UI/telegram format).
        return "".join(
            f"{ex.id}) {ex.test}. Ответ: {ex.answer}\n\n" for ex in exercises
        )

    async def get_count_testing_exercises_in_subsection(
        self,
        section: str,
        subsection: str,
    ) -> int:
        return await self._repo.count_exercises(section, subsection)

    async def get_random_testing_exercise(
        self,
        section: str,
        subsection: str,
        user_id: int,
    ) -> tuple[str, str, int] | None:
        exercises = await self._repo.get_available_exercises(
            section, subsection, user_id
        )
        if not exercises:
            return None
        chosen = random.choice(exercises)
        return chosen.test, chosen.answer, chosen.id

    async def get_section_names(self) -> list[str]:
        return await self._repo.get_section_names()

    async def get_subsection_names(self, section: str) -> list[str]:
        return await self._repo.get_subsection_names(section)

    async def edit_testing_exercise(
        self,
        section: str,
        subsection: str,
        test: str,
        answer: str,
        index: int,
    ) -> None:
        await self._repo.update_exercise(section, subsection, index, test, answer)

    async def delete_testing_exercise(
        self, section: str, subsection: str, index: int
    ) -> None:
        await self._repo.delete_exercise(section, subsection, index)