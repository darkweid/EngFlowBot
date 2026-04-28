from collections import namedtuple
import re

WordPair = namedtuple("WordPair", ["russian", "english"])
NON_ALPHABETIC_ALLOWED = r"0-9,()\'«»‘’:–\[\]\-\s\\\/\."


def check_line(line: str) -> WordPair:
    """
    Checks if line is in correct format and swaps order if needed.

    Accepted formats: "russian =+= english" or "russian | english".
    If the word identified as "russian" is in English and the "english" word is in Russian,
    the function swaps them to ensure the correct order.
    """
    # Match any of the delimiters `=+=` or `|`
    match = re.match(r"(.+?)\s*(=\+=|\|)\s*(.+)", line)
    if not match:
        raise ValueError(
            'Неверный формат строки, разделитель отсутствует или строка не соответствует формату\n"{line}"'
        )

    russian, english = match.group(1).strip(), match.group(3).strip()
    if not russian or not english:
        raise ValueError('Слово на русском и/или английском пустое\n"{line}"')

    # Ensure words are in correct languages; swap if needed
    if is_english(english) and is_russian(russian):
        pass
    elif is_english(russian) and is_russian(english):
        russian, english = english, russian
    else:
        raise ValueError(
            f'В одном из слов присутствуют буквы другого языка или недопустимые символы\n"{line}"'
        )

    return WordPair(russian=russian, english=english)


def is_russian(text: str) -> bool:
    return bool(re.fullmatch(rf"[а-яА-ЯёЁ{NON_ALPHABETIC_ALLOWED}]+", text))


def is_english(text: str) -> bool:
    return bool(re.fullmatch(rf"[a-zA-Z{NON_ALPHABETIC_ALLOWED}]+", text))
