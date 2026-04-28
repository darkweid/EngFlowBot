from datetime import date, datetime, time

from bot.db.models import (
    NewWords,
    TestingExercise,
    User,
    UserProgress,
    UserWordsLearning,
)


def build_testing_exercise(
    *,
    section: str = "Grammar",
    subsection: str = "Present Simple",
    exercise_id: int = 1,
    test: str = "She ... English.",
    answer: str = "speaks",
) -> TestingExercise:
    return TestingExercise(
        section=section,
        subsection=subsection,
        id=exercise_id,
        test=test,
        answer=answer,
    )


def build_new_word(
    *,
    section: str = "Vocabulary",
    subsection: str = "Travel",
    exercise_id: int = 1,
    russian: str = "самолет",
    english: str = "plane",
) -> NewWords:
    return NewWords(
        section=section,
        subsection=subsection,
        id=exercise_id,
        russian=russian,
        english=english,
    )


def build_user(
    *,
    id_: int = 1,
    user_id: int = 123456,
    full_name: str = "Test User",
    tg_login: str = "test_user",
    points: int = 0,
    registration_date: datetime | None = None,
    reminder_time: time | None = None,
    time_zone: str | None = None,
) -> User:
    return User(
        id=id_,
        registration_date=registration_date or datetime(2026, 1, 2, 3, 4),
        user_id=user_id,
        full_name=full_name,
        tg_login=tg_login,
        points=points,
        reminder_time=reminder_time,
        time_zone=time_zone,
    )


def build_user_progress(
    *,
    user_id: int = 123456,
    exercise_type: str = "Testing",
    section: str = "Grammar",
    subsection: str = "Present Simple",
    exercise_id: int = 1,
    attempts: int = 1,
    success: bool = True,
    progress_date: date | None = None,
) -> UserProgress:
    return UserProgress(
        user_id=user_id,
        exercise_type=exercise_type,
        exercise_section=section,
        exercise_subsection=subsection,
        exercise_id=exercise_id,
        attempts=attempts,
        success=success,
        date=progress_date or date(2026, 1, 2),
    )


def build_user_word_learning(
    *,
    user_id: int = 123456,
    section: str = "Vocabulary",
    subsection: str = "Travel",
    exercise_id: int = 1,
    attempts: int = 0,
    success: int = 0,
    next_review_date: date | None = None,
    add_date: date | None = None,
    new_word: NewWords | None = None,
) -> UserWordsLearning:
    entry = UserWordsLearning(
        user_id=user_id,
        section=section,
        subsection=subsection,
        exercise_id=exercise_id,
        attempts=attempts,
        success=success,
        next_review_date=next_review_date or date(2026, 1, 2),
        add_date=add_date or date(2026, 1, 2),
    )
    entry.new_word = new_word or build_new_word(
        section=section,
        subsection=subsection,
        exercise_id=exercise_id,
    )
    return entry
