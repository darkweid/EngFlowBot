from unittest.mock import patch

from bot.keyboards.keyboards import (
    keyboard_builder,
    keyboard_builder_users,
    keyboard_builder_words_learning,
)
from bot.lexicon import AdminMenuButtons, BasicButtons


def button_pairs(markup):
    return [
        (button.text, button.callback_data)
        for row in markup.inline_keyboard
        for button in row
    ]


async def test_keyboard_builder_places_args_before_kwargs_by_default():
    markup = await keyboard_builder(
        2,
        BasicButtons.MAIN_MENU,
        extra=BasicButtons.CLOSE,
    )

    assert button_pairs(markup) == [
        (BasicButtons.MAIN_MENU, BasicButtons.MAIN_MENU),
        (BasicButtons.CLOSE, "extra"),
    ]


async def test_keyboard_builder_can_place_kwargs_before_args():
    markup = await keyboard_builder(
        1,
        BasicButtons.MAIN_MENU,
        args_go_first=False,
        extra=BasicButtons.CLOSE,
    )

    assert button_pairs(markup) == [
        (BasicButtons.CLOSE, "extra"),
        (BasicButtons.MAIN_MENU, BasicButtons.MAIN_MENU),
    ]


async def test_keyboard_builder_words_learning_adds_answer_options_and_unknown_button():
    with patch(
        "bot.keyboards.keyboards.random.shuffle", side_effect=lambda buttons: None
    ):
        markup = await keyboard_builder_words_learning(
            width=2,
            correct="Дом",
            options=["Поезд", "Самолет", "Корабль"],
        )

    assert button_pairs(markup) == [
        ("Дом", "correct"),
        ("Поезд", "not_correct"),
        ("Самолет", "not_correct"),
        ("Корабль", "not_correct"),
        (BasicButtons.I_DONT_KNOW, "i_dont_know_word"),
    ]


async def test_keyboard_builder_users_adds_user_buttons_and_exit():
    users = (
        {
            "id": 1,
            "tg_login": "one",
            "full_name": "User One",
            "user_id": 123,
        },
        {
            "id": 2,
            "tg_login": "two",
            "full_name": "User Two",
            "user_id": 456,
        },
    )

    markup = await keyboard_builder_users(users)

    assert button_pairs(markup) == [
        ("1. @one [User One][123]", "123"),
        ("2. @two [User Two][456]", "456"),
        (AdminMenuButtons.EXIT, AdminMenuButtons.EXIT),
    ]
