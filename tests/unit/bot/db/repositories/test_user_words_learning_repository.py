from datetime import date

from bot.db.repositories.user_words_learning import UserWordsLearningRepository
from tests.factories import build_new_word, build_user_word_learning
from tests.fakes import (
    FakeAsyncSession,
    FakeExecuteResult,
    FakeSessionMaker,
    statement_sql,
)


async def test_words_to_learn_today_filters_by_user_and_due_date():
    entry = build_user_word_learning(user_id=123)
    session = FakeAsyncSession([FakeExecuteResult(scalar_values=[entry])])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.words_to_learn_today(123)

    assert result == [entry]
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from user_words_learning" in sql
    assert "user_words_learning.user_id = 123" in sql
    assert "user_words_learning.next_review_date <=" in sql


async def test_learning_info_filters_by_user_and_composite_word_key():
    entry = build_user_word_learning(user_id=123, exercise_id=8)
    session = FakeAsyncSession([FakeExecuteResult(scalar_values=[entry])])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.learning_info(
        user_id=123,
        section="Vocabulary",
        subsection="Travel",
        exercise_id=8,
    )

    assert result is entry
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_words_learning.user_id = 123" in sql
    assert "user_words_learning.section = 'vocabulary'" in sql
    assert "user_words_learning.subsection = 'travel'" in sql
    assert "user_words_learning.exercise_id = 8" in sql


async def test_update_learning_progress_updates_review_state_by_word_key():
    session = FakeAsyncSession([FakeExecuteResult()])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    await repo.update_learning_progress(
        section="Vocabulary",
        subsection="Travel",
        exercise_id=8,
        success_value=2,
        next_review_date=date(2026, 5, 1),
    )

    session.begin.assert_called_once_with()
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "update user_words_learning" in sql
    assert "user_words_learning.section = 'vocabulary'" in sql
    assert "user_words_learning.subsection = 'travel'" in sql
    assert "user_words_learning.exercise_id = 8" in sql


async def test_add_user_words_learning_entries_adds_all_inside_transaction():
    entries = [
        build_user_word_learning(exercise_id=1),
        build_user_word_learning(exercise_id=2),
    ]
    session = FakeAsyncSession()
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    await repo.add_user_words_learning_entries(entries)

    session.begin.assert_called_once_with()
    session.add_all.assert_called_once_with(entries)


async def test_list_new_words_filters_by_section_and_subsection():
    word = build_new_word(section="Vocabulary", subsection="Travel")
    session = FakeAsyncSession([FakeExecuteResult(scalar_values=[word])])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.list_new_words("Vocabulary", "Travel")

    assert result == [word]
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from new_words" in sql
    assert "new_words.section = 'vocabulary'" in sql
    assert "new_words.subsection = 'travel'" in sql
    assert "order by new_words.id" in sql
