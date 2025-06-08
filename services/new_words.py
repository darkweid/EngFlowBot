from __future__ import annotations

from db.models import NewWords
from db.repositories.new_words import NewWordsRepository


class NewWordsService:

    def __init__(self, repository: NewWordsRepository | None = None) -> None:
        self._repo = repository or NewWordsRepository()

    # ──────────────────────────── PUBLIC API ───────────────────────────── #

    async def add_new_words_exercise(
            self,
            section: str,
            subsection: str,
            russian: str,
            english: str,
    ) -> None:
        max_id = await self._repo.get_max_exercise_id(section, subsection)
        next_id = max_id + 1

        exercise = NewWords(
            section=section,
            subsection=subsection,
            id=next_id,
            russian=russian,
            english=english,
        )
        await self._repo.add_exercise(exercise)

    async def delete_new_words_exercise(
            self,
            section: str,
            subsection: str,
            index: int,
    ) -> None:
        await self._repo.delete_exercise(section, subsection, index)

    async def edit_new_words_exercise(
            self,
            section: str,
            subsection: str,
            russian: str,
            english: str,
            index: int,
    ) -> None:
        await self._repo.update_exercise(section, subsection, index, russian, english)

    async def get_count_new_words_exercises_in_subsection(
            self,
            section: str,
            subsection: str,
    ) -> int:
        return await self._repo.count_exercises(section, subsection)

    async def get_new_words_exercises(self, subsection: str | int) -> str:
        subsection_str = str(subsection)
        exercises = await self._repo.list_exercises(subsection_str)
        return "".join(
            f"{ex.id}) {ex.russian} – {ex.english}\n" for ex in exercises
        )

    async def get_subsection_names(self, section: str) -> list[str]:
        return await self._repo.get_subsection_names(section)
