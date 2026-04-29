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


async def test_all_words_by_section_subsection_filters_by_user_and_subsection():
    entry = build_user_word_learning(user_id=123, subsection="Travel")
    session = FakeAsyncSession([FakeExecuteResult(scalar_values=[entry])])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.all_words_by_section_subsection(
        user_id=123,
        section="Vocabulary",
        subsection="Travel",
    )

    assert result == [entry]
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_words_learning.user_id = 123" in sql
    assert "user_words_learning.section = 'vocabulary'" in sql
    assert "user_words_learning.subsection = 'travel'" in sql


async def test_all_words_by_user_filters_by_user_only():
    entry = build_user_word_learning(user_id=123)
    session = FakeAsyncSession([FakeExecuteResult(scalar_values=[entry])])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.all_words_by_user(123)

    assert result == [entry]
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_words_learning.user_id = 123" in sql


async def test_count_active_learning_returns_zero_when_no_rows():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=None)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_active_learning(user_id=123, active_rate=2)

    assert result == 0


async def test_count_active_learning_filters_by_user_and_success_le():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=5)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_active_learning(user_id=123, active_rate=2)

    assert result == 5
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_words_learning.user_id = 123" in sql
    assert "user_words_learning.success <= 2" in sql


async def test_count_active_in_subsection_filters_by_subsection():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=4)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_active_in_subsection(
        user_id=123, subsection="Travel", learning_rate=3
    )

    assert result == 4
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_words_learning.subsection = 'travel'" in sql
    assert "user_words_learning.user_id = 123" in sql
    assert "user_words_learning.success <= 3" in sql


async def test_count_learned_filters_by_success_ge():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=8)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_learned(user_id=123, learned_rate=5)

    assert result == 8
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_words_learning.user_id = 123" in sql
    assert "user_words_learning.success >= 5" in sql


async def test_count_learned_returns_zero_when_no_rows():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=None)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_learned(user_id=123, learned_rate=5)

    assert result == 0


async def test_count_all_by_user_counts_user_entries():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=10)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_all_by_user(123)

    assert result == 10
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_words_learning.user_id = 123" in sql


async def test_count_all_today_by_user_filters_by_due_date():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=3)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_all_today_by_user(123)

    assert result == 3
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_words_learning.user_id = 123" in sql
    assert "user_words_learning.next_review_date <=" in sql


async def test_distinct_subsections_returns_user_subsections():
    session = FakeAsyncSession([FakeExecuteResult(scalar_values=["Food", "Travel"])])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.distinct_subsections(123)

    assert result == ["Food", "Travel"]
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "select distinct" in sql
    assert "user_words_learning.user_id = 123" in sql


async def test_count_learned_in_subsection_filters_subsection_and_success_ge():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=6)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_learned_in_subsection(
        user_id=123, subsection="Travel", learned_rate=5
    )

    assert result == 6
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_words_learning.subsection = 'travel'" in sql
    assert "user_words_learning.user_id = 123" in sql
    assert "user_words_learning.success >= 5" in sql


async def test_count_today_in_subsection_filters_by_due_date():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=2)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_today_in_subsection(123, "Travel")

    assert result == 2
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_words_learning.subsection = 'travel'" in sql
    assert "user_words_learning.user_id = 123" in sql
    assert "user_words_learning.next_review_date <=" in sql


async def test_count_total_in_subsection_returns_count():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=9)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_total_in_subsection(123, "Travel")

    assert result == 9
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "user_words_learning.subsection = 'travel'" in sql
    assert "user_words_learning.user_id = 123" in sql


async def test_sum_success_in_subsection_returns_zero_when_none():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=None)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.sum_success_in_subsection(123, "Travel")

    assert result == 0


async def test_sum_success_in_subsection_returns_sum():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=14)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.sum_success_in_subsection(123, "Travel")

    assert result == 14
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "sum(user_words_learning.success)" in sql
    assert "user_words_learning.subsection = 'travel'" in sql
    assert "user_words_learning.user_id = 123" in sql


async def test_sum_attempts_in_subsection_returns_sum():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=20)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.sum_attempts_in_subsection(123, "Travel")

    assert result == 20
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "sum(user_words_learning.attempts)" in sql


async def test_sum_attempts_in_subsection_returns_zero_when_none():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=None)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.sum_attempts_in_subsection(123, "Travel")

    assert result == 0


async def test_update_user_points_increments_points_inside_transaction():
    session = FakeAsyncSession([FakeExecuteResult()])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    await repo.update_user_points(123, 7)

    session.begin.assert_called_once_with()
    session.execute.assert_awaited_once()
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "update users" in sql
    assert "users.user_id = 123" in sql


async def test_max_custom_word_id_returns_zero_when_none():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=None)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.max_custom_word_id(123)

    assert result == 0
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "max(new_words.id)" in sql
    assert "new_words.section = '123'" in sql
    assert "new_words.subsection = '123'" in sql


async def test_max_custom_word_id_returns_existing_max():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=42)])
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    result = await repo.max_custom_word_id(123)

    assert result == 42


async def test_add_new_word_adds_orm_object_inside_transaction():
    word = build_new_word()
    session = FakeAsyncSession()
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    await repo.add_new_word(word)

    session.begin.assert_called_once_with()
    session.add.assert_called_once_with(word)


async def test_add_user_words_learning_entry_adds_single_entry_in_transaction():
    entry = build_user_word_learning()
    session = FakeAsyncSession()
    repo = UserWordsLearningRepository(session_maker=FakeSessionMaker(session))

    await repo.add_user_words_learning_entry(entry)

    session.begin.assert_called_once_with()
    session.add.assert_called_once_with(entry)
