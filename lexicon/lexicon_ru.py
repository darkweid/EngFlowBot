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
    INFO_RULES = f"""\n🟢Весь прогресс сохраняется в памяти бота
\n🔵Регистр введенных предложений/слов не имеет значения.
\n❌Не используй сокращения «don't», «it's»
✅Используй полные формы «do not», «it is»
\n🟠В любой непонятной ситуации нажимай команду /start и бот перезапустится 😊"""
    ERROR = 'Что-то пошло не так\nПерезапусти бота, нажми команду /start'


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


class AdminMenuButtons(Enum):
    EXERCISES = 'Тренажеры'

    GRAMMAR = 'Тренажер по грамматике'
    SET_SECTION_GRAMMAR = 'Выбрать раздел'
    SEE_EXERCISES_GRAMMAR = 'Посмотреть предложения'
    ADD_EXERCISE_GRAMMAR = 'Добавить предложение'
    DEL_EXERCISE_GRAMMAR = 'Удалить предложение'

    IRR_VERBS = 'Неправильные глаголы'
    SEE_VERBS = 'Посмотреть глаголы'
    ADD_VERBS = 'Добавить глагол'
    DEL_VERBS = 'Удалить глагол'

    NEW_WORDS = 'Изучение новых слов'
    SET_SECTION_NEW_WORDS = 'Выбрать раздел'
    SEE_NEW_WORDS = 'Посмотреть слова'
    ADD_NEW_WORDS = 'Добавить слово'
    DEL_NEW_WORDS = 'Удалить слово'

    SEE_ACTIVITY_DAY = 'Посмотреть активность за день'
    SEE_ACTIVITY_WEEK = 'Посмотреть активность за неделю'
    SEE_CHART = 'Посмотреть рейтинг пользователей'

    USERS = 'Пользователи'
    SEE_USERS = 'Посмотреть пользователей'
    DEL_USER = 'Удалить пользователя'

    BACK = '↖️Назад'
    EXIT = '⬅️Выход'
