import pytest

from bot.utils.new_words_parser import check_line, is_english, is_russian


@pytest.mark.parametrize(
    "line, expected_russian, expected_english",
    [
        ("дом =+= house", "дом", "house"),
        ("самолет | plane", "самолет", "plane"),
        ("train | поезд", "поезд", "train"),
    ],
)
def test_check_line_accepts_supported_formats_and_normalizes_order(
    line,
    expected_russian,
    expected_english,
):
    result = check_line(line)

    assert result.russian == expected_russian
    assert result.english == expected_english


@pytest.mark.parametrize(
    "line",
    [
        "дом house",
        "дом | ",
        "house | plane",
        "дом | дом",
        "дом house | plane",
    ],
)
def test_check_line_rejects_invalid_lines(line):
    with pytest.raises(ValueError):
        check_line(line)


@pytest.mark.parametrize(
    "text",
    [
        "самолет",
        "слово (пояснение)",
        "слово-слово",
        "слово, слово",
    ],
)
def test_is_russian_accepts_allowed_russian_text(text):
    assert is_russian(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "plane",
        "word (note)",
        "word-word",
        "word / phrase",
    ],
)
def test_is_english_accepts_allowed_english_text(text):
    assert is_english(text) is True


def test_language_helpers_reject_mixed_alphabets():
    assert is_russian("дом house") is False
    assert is_english("house дом") is False
