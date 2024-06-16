from enum import Enum

class MessagesEnum(Enum):
    WELCOME_NEW_USER = f"""Помогаю людям изучать английский.
У меня три функции:
– тренажер по грамматике
- запоминание неправильных глаголов
– запоминание новых слов
\n🔻️ Выбери, с чего начнём сегодня 🔻"""
    WELCOME_EXISTING_USER = '🔻 Чем займёмся сегодня? 🔻'

class ButtonEnum(Enum):
    YES = '✅ <b>ДА!</b>'
    NO = '❌ <b>НЕТ</b>'
    CANCEL = 'Отменить'
    GRAMMAR_TRAINING = 'Тренажер по грамматике'
    IRREGULAR_VERBS = 'Изучение неправильных глаголов'
    NEW_WORDS = 'Изучение новых слов'
    RULES = '🙋‍♀️ Посмотреть правила 🙋'
    SEE_ANSWER = '🔎 Показать ответ 🔍'
    MAIN_MENU = 'Главное меню'