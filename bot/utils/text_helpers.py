def get_word_declension(count: int, word: str) -> str:
    """
    Returns the correct form of a word based on a numeral.

    The function takes a number and a word, and returns a string with the
    number and the corresponding form of the word according to the rules of
    Russian declension.

    Parameters:
    ----------
    count : int
        The number for which the word needs to be declined. It should be non-negative.
    word : str
        The word for which the declension needs to be determined. Supported words
        are registered in the function's dictionary (e.g., "слово", "предложение").

    Returns:
    ----------
    str
        A string formatted as "{count} {declined word}", where {declined word}
        is in the correct form depending on the value of count.

    Exceptions:
    -----------
    ValueError
        If the word is not supported (not found in the declension dictionary).

    Examples:
    ---------
    >>> get_word_declension(1, "слово")
    '1 слово'

    >>> get_word_declension(5, "слово")
    '5 слов'

    >>> get_word_declension(11, "предложение")
    '11 предложений'
    """
    declensions = {
        "слово": ("слово", "слова", "слов"),
        "предложение": ("предложение", "предложения", "предложений"),
        "упражнение": ("упражнение", "упражнения", "упражнений"),
    }
    word = word.lower()

    if word not in declensions:
        raise ValueError(f"Склонение для слова '{word}' не задано.")

    if count % 10 == 1 and count % 100 != 11:
        form = declensions[word][0]  # Именительный падеж
    elif 2 <= count % 10 <= 4 and not (12 <= count % 100 <= 14):
        form = declensions[word][1]  # Родительный падеж
    else:
        form = declensions[word][2]  # Множественный падеж

    return f"{count} {form}"
