from typing import Union
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from lexicon import *

ButtonEnumType = Union[BasicButtons, MainMenuButtons, AdminMenuButtons, TestingSections, MessageTexts, TensesSections,
ConstructionsSections, PhrasesAndWordsSections, PrepositionsSections, ModalVerbsSections,
ConditionalsSections]


# dict[str, ButtonEnumType]
async def keyboard_builder(width: int, *args: ButtonEnumType, args_go_first: bool = True,
                           **kwargs: ButtonEnumType) -> InlineKeyboardMarkup:
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    if args_go_first:
        if args:
            for button in args:
                buttons.append(InlineKeyboardButton(
                    text=button,
                    callback_data=button))

        if kwargs:
            for callback, button in kwargs.items():
                buttons.append(InlineKeyboardButton(
                    text=button,
                    callback_data=callback))
    else:
        if kwargs:
            for callback, button in kwargs.items():
                buttons.append(InlineKeyboardButton(
                    text=button,
                    callback_data=callback))
        if args:
            for button in args:
                buttons.append(InlineKeyboardButton(
                    text=button,
                    callback_data=button))
    kb_builder.row(*buttons, width=width)
    return kb_builder.as_markup()


async def keyboard_builder_users(users: list) -> InlineKeyboardMarkup:
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    for user in users:
        buttons.append(InlineKeyboardButton(
            text=f"{user.get('id')}. @{user.get('tg_login')} [{user.get('full_name')}][{user.get('user_id')}]",
            callback_data=str(user.get('user_id'))))
    buttons.append(InlineKeyboardButton(
        text=AdminMenuButtons.EXIT,
        callback_data=AdminMenuButtons.EXIT))
    kb_builder.row(*buttons, width=1)
    return kb_builder.as_markup()
