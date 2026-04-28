from bot.utils.url_builders import word_with_youglish_link, youglish_url_builder


def test_youglish_url_builder_cleans_helper_words_parentheses_and_slashes():
    result = youglish_url_builder("look (at) somebody / something")

    assert result == "https://www.youglish.com/pronounce/look/english"


def test_youglish_url_builder_encodes_spaces():
    result = youglish_url_builder("take care")

    assert result == "https://www.youglish.com/pronounce/take%20care/english"


def test_word_with_youglish_link_returns_html_anchor():
    result = word_with_youglish_link("take care")

    assert (
        result
        == '<a href="https://www.youglish.com/pronounce/take%20care/english">Take care</a>'
    )
