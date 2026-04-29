import re


def youglish_url_builder(word: str) -> str:
    """
    Builds a YouGlish URL for the given word, removing unnecessary terms and special symbols.

    This function cleans the input word by:
    - Removing text within parentheses
    - Excluding "somebody", "something", "smb", and "smth"
    - Replacing '/' with a space
    - Stripping extra spaces and encoding spaces for URL usage

    Args:
        word (str): The word to format into a YouGlish URL.

    Returns:
        str: A properly formatted URL string for YouGlish.
    """
    # Remove words in parentheses
    word = re.sub(r"\(.*?\)", "", word)
    # Remove "somebody", "something", "smb", "smth"
    word = re.sub(r"\b(somebody|something|smb|smth)\b", "", word, flags=re.IGNORECASE)
    word = word.replace("/", " ")
    # Remove extra spaces and encode spaces for URL
    word = " ".join(word.split()).replace(" ", "%20")

    return f"https://www.youglish.com/pronounce/{word}/english"


def word_with_youglish_link(word_english: str) -> str:
    """
    Creates an HTML hyperlink to YouGlish pronunciation for the given word.

    The hyperlink uses YouGlish's URL structure for English pronunciation.

    Args:
        word_english (str): The word to link to YouGlish.

    Returns:
        str: An HTML anchor element as a string.
    """
    return f'<a href="{youglish_url_builder(word_english)}">{word_english.capitalize()}</a>'
