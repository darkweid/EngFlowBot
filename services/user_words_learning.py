from __future__ import annotations

import random
from datetime import date, timedelta

from db.models import NewWords, UserWordsLearning
from db.repositories.user_words_learning import UserWordsLearningRepository
from services.utils import calculate_next_review_date


class UserWordsLearningService:
    ACTIVE_LEARNING_RATE = 3
    LEARNED_RATE = 5

    def __init__(
            self, repository: UserWordsLearningRepository | None = None
    ) -> None:
        self._user_words_learning_repo = repository or UserWordsLearningRepository()

    # ──────────────────────────── PUBLIC API ───────────────────────────── #

    async def get_random_word_exercise(self, user_id: int) -> dict | None:
        words_today = await self._user_words_learning_repo.words_to_learn_today(user_id)
        if not words_today:
            return None

        exercise = random.choice(words_today)

        same_sub_words = await self._user_words_learning_repo.all_words_by_section_subsection(
            user_id, exercise.new_word.section, exercise.new_word.subsection
        )
        options = [
            w.new_word.russian.capitalize()
            for w in same_sub_words
            if w.new_word.russian != exercise.new_word.russian
        ]

        # if not enough in same section, take from all user words
        if len(options) < 3:
            all_words = await self._user_words_learning_repo.all_words_by_user(user_id)
            options = [
                w.new_word.russian.capitalize()
                for w in all_words
                if w.new_word.russian != exercise.new_word.russian
            ]

        options = random.sample(options, k=3)

        return {
            "russian": exercise.new_word.russian.capitalize(),
            "english": exercise.new_word.english.capitalize(),
            "section": exercise.new_word.section,
            "subsection": exercise.new_word.subsection,
            "exercise_id": exercise.exercise_id,
            "options": options,
        }

    async def get_count_active_learning_exercises(self, user_id: int) -> int:
        return await self._user_words_learning_repo.count_active_learning(
            user_id, self.ACTIVE_LEARNING_RATE
        )

    async def get_count_learned_exercises(self, user_id: int) -> int:
        return await self._user_words_learning_repo.count_learned(user_id, self.LEARNED_RATE)

    async def get_count_all_exercises_by_user(self, user_id: int) -> int:
        return await self._user_words_learning_repo.count_all_by_user(user_id)

    async def get_count_all_exercises_for_today_by_user(
            self, user_id: int
    ) -> int:
        return await self._user_words_learning_repo.count_all_today_by_user(user_id)

    async def get_added_subsections_by_user(self, user_id: int):
        return await self._user_words_learning_repo.distinct_subsections(user_id)

    async def get_user_stats(self, user_id: int) -> dict:
        stats: dict[str, dict] = {}
        subsections = await self._user_words_learning_repo.distinct_subsections(user_id)

        for subsection in subsections:
            learned = await self._user_words_learning_repo.count_learned_in_subsection(
                user_id, subsection, self.LEARNED_RATE
            )
            active = await self._user_words_learning_repo.count_active_in_subsection(
                user_id, subsection, self.ACTIVE_LEARNING_RATE
            )
            today = await self._user_words_learning_repo.count_today_in_subsection(user_id, subsection)
            total = await self._user_words_learning_repo.count_total_in_subsection(user_id, subsection)

            total_success = await self._user_words_learning_repo.sum_success_in_subsection(
                user_id, subsection
            )
            total_attempts = await self._user_words_learning_repo.sum_attempts_in_subsection(
                user_id, subsection
            )

            success_rate = (
                (total_success / total_attempts) * 100
                if total_attempts
                else 0
            )

            stats[subsection] = {
                "learned": learned,
                "for_today_learning": today,
                "active_learning": active,
                "total_words_in_subsection": total,
                "success_rate": success_rate,
            }

        return stats

    async def set_progress(
            self,
            user_id: int,
            section: str,
            subsection: str,
            exercise_id: int,
            success: bool,
    ) -> None:
        info = await self._user_words_learning_repo.learning_info(
            user_id, section, subsection, exercise_id
        )
        if info is None:
            return  # safety guard

        success_value = info.success
        attempts = info.attempts + 1

        if success:
            await self._user_words_learning_repo.update_user_points(user_id, +1)
            success_value += 1
            next_review_date = await calculate_next_review_date(
                success_attempts=success_value, total_attempts=attempts
            )
        else:
            await self._user_words_learning_repo.update_user_points(user_id, -1)
            next_review_date = date.today() + timedelta(days=1)

        await self._user_words_learning_repo.update_learning_progress(
            section,
            subsection,
            exercise_id,
            success_value,
            next_review_date,
        )

    async def add_words_to_learning(
            self, section: str, subsection: str, user_id: int
    ) -> None:
        new_words = await self._user_words_learning_repo.list_new_words(section, subsection)
        entries = [
            UserWordsLearning(
                user_id=user_id,
                section=section,
                subsection=subsection,
                exercise_id=word.id,
            )
            for word in new_words
        ]
        if entries:
            await self._user_words_learning_repo.add_user_words_learning_entries(entries)

    async def admin_add_words_to_learning(
            self, russian: str, english: str, user_id: int
    ) -> None:
        # individual section/subsection — user ID
        section = subsection = str(user_id)

        next_id = (await self._user_words_learning_repo.max_custom_word_id(user_id)) + 1

        word = NewWords(
            section=section,
            subsection=subsection,
            id=next_id,
            russian=russian,
            english=english,
        )
        await self._user_words_learning_repo.add_new_word(word)

        entry = UserWordsLearning(
            user_id=user_id,
            section=section,
            subsection=subsection,
            exercise_id=next_id,
        )
        await self._user_words_learning_repo.add_user_words_learning_entry(entry)
