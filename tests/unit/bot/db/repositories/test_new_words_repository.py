from bot.db.repositories.new_words import NewWordsRepository
from tests.factories import build_new_word
from tests.fakes import (
    FakeAsyncSession,
    FakeExecuteResult,
    FakeSessionMaker,
    statement_sql,
)


async def test_list_exercises_filters_by_subsection_and_returns_words():
    word = build_new_word(subsection="Travel")
    session = FakeAsyncSession([FakeExecuteResult(scalar_values=[word])])
    repo = NewWordsRepository(session_maker=FakeSessionMaker(session))

    result = await repo.list_exercises("Travel")

    assert result == [word]
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from new_words" in sql
    assert "new_words.subsection = 'travel'" in sql
    assert "order by new_words.id" in sql


async def test_get_subsection_names_returns_distinct_ordered_values():
    session = FakeAsyncSession([FakeExecuteResult(scalar_values=["Food", "Travel"])])
    repo = NewWordsRepository(session_maker=FakeSessionMaker(session))

    result = await repo.get_subsection_names("Vocabulary")

    assert result == ["Food", "Travel"]
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "select distinct" in sql
    assert "new_words.section = 'vocabulary'" in sql
    assert "order by new_words.subsection" in sql


async def test_update_exercise_filters_by_composite_word_key():
    session = FakeAsyncSession([FakeExecuteResult()])
    repo = NewWordsRepository(session_maker=FakeSessionMaker(session))

    await repo.update_exercise(
        section="Vocabulary",
        subsection="Travel",
        index=3,
        russian="поезд",
        english="train",
    )

    session.begin.assert_called_once_with()
    session.execute.assert_awaited_once()
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "update new_words" in sql
    assert "new_words.section = 'vocabulary'" in sql
    assert "new_words.subsection = 'travel'" in sql
    assert "new_words.id = 3" in sql


async def test_add_exercise_adds_orm_object_inside_transaction():
    word = build_new_word()
    session = FakeAsyncSession()
    repo = NewWordsRepository(session_maker=FakeSessionMaker(session))

    await repo.add_exercise(word)

    session.begin.assert_called_once_with()
    session.add.assert_called_once_with(word)


async def test_get_max_exercise_id_returns_zero_when_no_rows():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=None)])
    repo = NewWordsRepository(session_maker=FakeSessionMaker(session))

    result = await repo.get_max_exercise_id("Vocabulary", "Travel")

    assert result == 0
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "max(new_words.id)" in sql
    assert "new_words.section = 'vocabulary'" in sql
    assert "new_words.subsection = 'travel'" in sql


async def test_get_max_exercise_id_returns_existing_max():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=42)])
    repo = NewWordsRepository(session_maker=FakeSessionMaker(session))

    result = await repo.get_max_exercise_id("Vocabulary", "Travel")

    assert result == 42


async def test_count_exercises_filters_by_section_and_subsection():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=5)])
    repo = NewWordsRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_exercises("Vocabulary", "Travel")

    assert result == 5
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "from new_words" in sql
    assert "new_words.section = 'vocabulary'" in sql
    assert "new_words.subsection = 'travel'" in sql


async def test_count_exercises_returns_zero_when_no_rows():
    session = FakeAsyncSession([FakeExecuteResult(scalar_value=None)])
    repo = NewWordsRepository(session_maker=FakeSessionMaker(session))

    result = await repo.count_exercises("Vocabulary", "Travel")

    assert result == 0


async def test_delete_exercise_filters_by_composite_word_key():
    session = FakeAsyncSession([FakeExecuteResult()])
    repo = NewWordsRepository(session_maker=FakeSessionMaker(session))

    await repo.delete_exercise("Vocabulary", "Travel", 7)

    session.begin.assert_called_once_with()
    session.execute.assert_awaited_once()
    sql = statement_sql(session.executed_statements[0]).lower()
    assert "delete from new_words" in sql
    assert "new_words.section = 'vocabulary'" in sql
    assert "new_words.subsection = 'travel'" in sql
    assert "new_words.id = 7" in sql
