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
