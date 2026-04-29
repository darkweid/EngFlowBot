import pytest

from bot.utils.message_to_users import get_word_declension as get_word_count_declension
from bot.utils.text_helpers import get_word_declension


@pytest.mark.parametrize(
    "count, word, expected",
    [
        (1, "слово", "1 слово"),
        (2, "слово", "2 слова"),
        (5, "слово", "5 слов"),
        (11, "слово", "11 слов"),
        (21, "предложение", "21 предложение"),
        (22, "предложение", "22 предложения"),
        (25, "предложение", "25 предложений"),
        (1, "упражнение", "1 упражнение"),
        (3, "упражнение", "3 упражнения"),
        (14, "упражнение", "14 упражнений"),
    ],
)
def test_get_word_declension_returns_russian_declension(count, word, expected):
    assert get_word_declension(count, word) == expected


def test_get_word_declension_rejects_unsupported_word():
    with pytest.raises(ValueError, match="Склонение"):
        get_word_declension(1, "тест")


@pytest.mark.parametrize(
    "count, expected",
    [
        (1, "1 слово"),
        (2, "2 слова"),
        (5, "5 слов"),
        (11, "11 слов"),
        (21, "21 слово"),
        (22, "22 слова"),
        (25, "25 слов"),
    ],
)
def test_message_to_users_word_declension_returns_word_forms(count, expected):
    assert get_word_count_declension(count) == expected
