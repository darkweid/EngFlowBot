from enum import Enum

class MessagesEnum(Enum):
    WELCOME_NEW_USER = f"""Помогаю людям изучать английский.
У меня три раздела:
– тренажер по грамматике
- запоминание неправильных глаголов
– запоминание новых слов

Так же ты можешь выбрать удобное тебе время по кнопке ниже, а я буду напоминать заниматься😉
Если хочешь - можешь установить время напоминаний позже из меню слева """
    WELCOME_EXISTING_USER = '🔻 Чем займёмся сегодня? 🔻'
    WRONG_ANSWER = '❌ Хм, у меня другой ответ 🤔'
    GIVE_A_HINT = '<u>Попробуй ещё раз</u> или попроси меня показать ответ 😉'
    LETS_CONTINUE = 'Продолжаем 😊'
    LEARN_FROM_MISTAKES = 'На ошибках учатся, так что продолжаем 😊'
    GRAMMAR_TRAINING_HELLO = 'Отличный выбор!\nБудем улучшать твою <b>грамматику</b>\nЕсли нужно - жми кнопку ниже и посмотри правила'

class ButtonEnum(Enum):
    YES = '✅ <b>ДА!</b>'
    NO = '❌ <b>НЕТ</b>'
    READY = 'Готов!'
    SET = 'Установить'
    MAIN_MENU = 'Главное меню'
    CANCEL = 'Отменить'
    GRAMMAR_TRAINING = 'Тренажер по грамматике'
    IRREGULAR_VERBS = 'Изучение неправильных глаголов'
    NEW_WORDS = 'Изучение новых слов'
    RULES = '🙋‍♀️ Посмотреть правила 🙋'
    SEE_ANSWER = '🔎 Показать ответ 🔍'
    REMINDER_TIME = 'Установить время напоминаний'


class GrammarTrainingButtons(Enum):
    PRESENT_SIMPLE_VS_PRESENT_CONTINIOUS = 'Present Simple vs Present Continuous'
    PAST_SIMPLE_VS_PRESENT_PERFECT = 'Past Simple vs Present Perfect'
    THERE_IS_THERE_ARE = 'There is / There are'
    COUNT_AND_UNCOUNT_NOUNS = 'Countable and Uncountable Nouns'
    MODAL_VERBS = 'Modal Verbs(can, could, may, might, must, should)'
    FUTURE_FORMS = 'Future Forms(will, going to)'
    COMPARATIVES_SUPERLATIVES = 'Comparatives and Superlatives'
