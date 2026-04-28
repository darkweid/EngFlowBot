from enum import StrEnum


class MessageTexts(StrEnum):
    WELCOME_NEW_USER = """
Привет, {user_name}\nЯ бот от <a href="{owner_tg_link}">{owner_name}</a>😊
Я помогаю:
– запоминать новые слова
– повторять грамматику\n
Можешь включить напоминания, чтобы заниматься регулярно😉
⬇️ В меню слева внизу ты можешь перезапустить бота, выйти в главное меню,
установить напоминания и узнать, как пользоваться ботом.
"""
    WELCOME_EXISTING_USER = "🔻 Чем займёмся сегодня? 🔻"
    INFO_RULES = """
<b>Функционал бота:</b>
1. 📝 <b>Тестирование:</b> Заполняй пробелы в английских предложениях и проверяй свои знания.
2. 📚 <b>Изучение новых слов:</b> Узнавай новые слова и фразы, выбирая правильные ответы на вопросы.
3. ➕ <b>Добавление слов:</b> Добавляй слова из готовых наборов в свои изучаемые, чтобы расширить словарный запас.
4. 👩‍🏫 <b>Индивидуальные слова:</b> Преподаватель может добавлять тебе индивидуальные слова для изучения, чтобы помочь в освоении сложных тем.
5. 📊 <b>Статистика:</b> Следи за своим прогрессом и улучшай результаты.\n
<b>Правила:</b>
- 🟢 Весь прогресс сохраняется в памяти бота. Нажатие команды /start ничего не удаляет.
- 🔵 РеГиСтР не имеет значения — вводи слова, как удобно.
- ❌ Избегай сокращений, таких как «don't» или «it's» — используй полные формы: «do not», «it is».
- 🟡 Не бойся ошибаться — это часть процесса обучения. Ты всегда можешь попробовать ещё раз или посмотреть правильный ответ.\n
<b>Поддержка и советы:</b>
- 💡 Если у тебя возникнут вопросы или ты запутаешься, всегда можно обратиться за помощью к <a href="{owner_tg_link}">преподавателю</a>.
- 📥 Ты можешь предложить свои идеи или улучшения бота, отправив сообщение <a href="https://t.me/shamanskii">разработчику</a>.\n
В любой момент ты можешь нажать команду /start, чтобы перезапустить бота и выбрать другой раздел изучения.\nУдачи и приятного обучения! 😊
"""
    ERROR = "Что-то пошло не так😐\nПерезапусти бота, нажми команду /start"
    TEST_RULES = """Задача простая: заполни пропуск\n
Если твой ответ не совпадёт с правильным:
⚪ Можешь попробовать ещё раз (количество попыток не ограничено)
⚪ Можешь нажать на кнопку «Показать ответ» – я покажу тебе ответ и задам другой вопрос, чтобы всё было честно🤓"""
    TESTING_HELLO = "Lets get it started 💃 🕺"
    CHOOSE_SECTION = "Выбери раздел для прохождения теста:"
    CHOOSE_SUBSECTION_TEST = "Выбери тему для прохождения теста:"
    ALL_EXERCISES_COMPLETED = "You’ve finished this test 💫🎉"
    INCORRECT_ANSWER = "❌ Хм, у меня другой ответ 🤔\nПопробуй ещё раз или попроси меня показать правильный ответ 😉"
    EMPTY_SECTION = "В этот раздел еще не добавлены упражнения 😐"
    ARE_YOU_SURE_START_AGAIN = (
        "Весь прогресс по этой теме будет сброшен.\nНачать проходить заново?"
    )
    NEW_WORDS_RULES = """Я использую метод интервальных повторений:
чем лучше ты помнишь слово, тем реже я буду его предлагать
Ты можешь добавлять слова, идиомы и фразовые глаголы,
а также устанавливать время напоминаний\n
<b>Повторяй слова каждый день, это важно!</b>"""
    ABOUT_SPACED_REPETITION = """<b>Интервальные повторения</b> — методика запоминания информации,
основанная на повторении учебного материала через увеличивающиеся интервалы времени.\n
<b>Основные принципы:</b>
1. <b>Забывание и восстановление</b>: Повторяя информацию в нужный момент, мы укрепляем её в памяти.
2. <b>Оптимизация времени</b>: Фокус на повторении информации, когда она может быть забыта.
3. <b>Периодические пересмотры</b>: Увеличивающиеся интервалы между повторениями способствуют переносу информации в долгосрочную память.\n
<b>Что такое уровни:</b>
Каждое успешное повторение слова увеличивает его "уровень", что удлиняет интервал до следующего повторения.
Уровни помогают определить, как хорошо усвоен материал и как часто его нужно повторять.\n
<b>Примеры интервалов:</b>
- 1 уровень: 1 день
- 2 уровень: 2 дня
- 4 уровень: 8 дней
- 5 уровень: 14 дней
- 7 уровень: 41 день
- 10 уровень: 201 день
И так далее\n
<b>Примеры:</b>
Для слова на 5 уровне следующий повтор будет через 14 дней.
Для слова на 7 уровне следующий повтор будет через 41 день.\n
Эти интервалы рассчитаны при 75% правильных ответов по упражнению. Если правильных ответов больше, слово будет повторяться реже.
Если со словом часто допускаются ошибки, оно будет повторяться чаще.
Например: при 50% правильных ответов 5 уровень – повторение через 7 дней, 7 уровень — через 20 дней."""

    NEW_WORDS_HELLO = "Lets get it started 💃 🕺"
    SELECT_SECTION_WORDS = "Выбери раздел:"
    SELECT_SUBSECTION_WORDS = "Выбери тему:"
    NO_WORDS_TO_LEARN_TODAY = "На сегодня у тебя больше нет слов для изучения"
    ADVICE_TO_ADD_MORE_WORDS = "Советую тебе добавить больше слов для изучения"

    STATS_USER = "За какой срок нужна статистика?"
    REMINDER = "Привет👋\nХочешь позаниматься?"
    REMINDER_WORDS_TO_LEARN = """Привет👋\nСегодня у тебя <b>{}</b> для изучения
Хочешь позаниматься?"""

    CHOOSE_TIMEZONE = """Выбери свой часовой пояс.
Например:
Москва - UTC+3
Омск - UTC+6
Чикаго - UTC-5"""
    PREPOSITIONS_OF_THE_TIME_RULES = """Впиши нужный предлог🐣
<b>Напомню правила</b>:
at - часы/минуты
on - дни
in - все, что больше: месяц, сезон, год и тд
no - если предлог не нужен (да, такое бывает, например со словами last, next, this, every)\n
<b>Исключения</b>:
in the morning
in the afternoon
in the evening
at night
at Christmas
on Monday morning
on Friday evening"""


class MainMenuButtons(StrEnum):
    NEW_WORDS = "Изучение слов"
    TESTING = "Повторение грамматики"
    # IRREGULAR_VERBS = 'Изучение неправильных глаголов'
    # TRANSLATING_SENTENCES = 'Предложения для перевода'


class BasicButtons(StrEnum):
    YES = "✅ Да"
    NO = "❌ Нет"
    READY = "I am ready!"
    BACK = "⬅️Назад"
    SET = "Установить"
    CHOOSE_OTHER_SECTION = "Выбрать другую тему"
    MAIN_MENU = "🏠Главное меню"
    MAIN_MENU_NEW_WORDS = "🏠Вернуться в меню"

    CANCEL = "Отменить"
    CLOSE = "Закрыть"
    RULES = "🙋‍♀️ Посмотреть правила 🙋"
    SEE_ANSWER = "🔎 Показать ответ 🔍"
    TODAY = "Сегодня"
    LAST_WEEK = "Последняя неделя"
    LAST_MONTH = "Последний месяц"
    CHANGE_TIME_ZONE = "Установить часовой пояс"
    CHANGE_REMINDER_TIME = "Установить время напоминаний"
    TURN_ON_REMINDER = "Включить напоминания"
    TURN_OFF_REMINDER = "Выключить напоминания"
    START_AGAIN = "Пройти заново"

    # New Words
    LEARN_ADDED_WORDS = "Учить мои слова"
    ADD_WORDS = "Выбрать набор слов"
    NEW_WORDS_PROGRESS = "Посмотреть прогресс"
    MORE_ABOUT_SPACED_REPETITION = "Подробнее про интервальное повторение"
    TURN_ON_HARD_MODE = "Включить сложный режим"
    TURN_OFF_HARD_MODE = "Выключить сложный режим"
    I_KNOW = "Знаю"
    I_DONT_KNOW = "Не знаю"


class TestingSections(StrEnum):
    TENSES = "Tenses"
    CONSTRUCTIONS = "Constructions"
    PHRASES_AND_WORDS = "Phrases & words"
    PREPOSITIONS = "Prepositions"
    MODAL_VERBS = "Modal verbs"
    CONDITIONALS = "Conditionals"


class TensesSections(StrEnum):
    PRESENT_SIMPLE = "Present Simple"
    PRESENT_CONTINUOUS = "Present Continuous"
    PS_VS_PC = "Present Simple VS Present Continuous"
    PAST_SIMPLE = "Past Simple"
    PAST_SIMPLE_WITH_IRR_VERBS = "Past Simple with irregular verbs"
    PRESENT_PERFECT_SIMPLE = "Present Perfect Simple"
    PAST_SIMPLE_VS_PRESENT_PERFECT_SIMPLE = "Past Simple VS Present Perfect Simple"
    PRESENT_SIMPLE_VS_PRESENT_PERFECT_SIMPLE = (
        "Present Simple VS Present Perfect Simple"
    )
    PRESENT_PERFECT_SIMPLE_VS_PRESENT_PERFECT_CONT = (
        "Present Perfect Simple VS Present Perfect Continuous"
    )


class ConstructionsSections(StrEnum):
    TO_BE_GOING_TO = "to be going to"
    WILL_VS_BE_GOING_TO = "will VS be going to"
    WAS_GOING_TO = "was going to"
    THERE_ARE_THERE_IS = "there are / there is"
    IT_TAKE = "it take"
    USED_TO = "used to"
    USED_TO_VS_PAST_SIMPLE = "used to VS Past Simple"
    TAG_QUESTIONS = "tag questions"


class PhrasesAndWordsSections(StrEnum):
    HOW_MUCH_HOW_MANY = "how much / how many"
    LITTLE_VS_FEW = "little VS few"
    SOME_VS_ANY = "some VS any"
    ENOUGH_VS_TOO = "enough VS too"
    SO_VS_SUCH = "so VS such"
    BECAUSE_VS_SO = "because VS so"
    SO_VS_NEITHER = "so VS neither"
    ARTICLES = "articles"


class PrepositionsSections(StrEnum):
    PREPOSITIONS_OF_THE_TIME = "Prepositions of time"
    PREPOSITIONS_OF_PLACE = "Prepositions of place"
    PREPOSITIONS_OF_AGENT_OR_INSTRUMENT = "Prepositions of agent or instrument"
    PREPOSITIONS_OF_CAUSE_OR_REASON = "Prepositions of Cause or Reason"


class ModalVerbsSections(StrEnum):
    CAN_VS_COULD = "can VS could"
    CANT_VS_COULDNT = "can’t VS couldn’t"
    MUST_VS_SHOULD = "must VS should"
    MUST_VS_SHOULD_VS_HAVE_TO = "must VS should VS have to"
    CAN_VS_MAY = "can VS may"


class ConditionalsSections(StrEnum):
    ZERO_COND = "zero cond"
    FIRST_COND = "first cond"
    SECOND_COND = "second cond"
    THIRD_COND = "third cond"
    MIXED = "mixed"


testing_section_mapping = {
    TestingSections.TENSES.value: TensesSections,
    TestingSections.CONSTRUCTIONS.value: ConstructionsSections,
    TestingSections.PHRASES_AND_WORDS.value: PhrasesAndWordsSections,
    TestingSections.PREPOSITIONS.value: PrepositionsSections,
    TestingSections.MODAL_VERBS.value: ModalVerbsSections,
    TestingSections.CONDITIONALS.value: ConditionalsSections,
}


class NewWordsSections(StrEnum):
    WORDS_BY_TOPIC = "Words by topic"
    BASIC_VERBS = "Basic verbs"
    ADJECTIVES = "Adjectives & Descriptions"
    PHRASAL_VERBS = "Phrasal verbs"


class Idioms(StrEnum):
    BUSINESS_IDIOMS = "Business Idioms"
    FOOD_IDIOMS = "Food Idioms"
    SPORTS_IDIOMS = "Sports Idioms"


class PhrasalVerbs(StrEnum):
    TRAVEL_PHRASAL_VERBS = "Travel Phrasal Verbs"
    WORK_PHRASAL_VERBS = "Work Phrasal Verbs"
    RELATIONSHIP_PHRASAL_VERBS = "Relationship Phrasal Verbs"


class AdminMenuButtons(StrEnum):
    YES = "Да"
    NO = "Нет"
    COMMIT = "Отправить"
    EXERCISES = "Тренажеры"
    CLOSE = "Закрыть"
    MAIN_MENU = "↖️Главное меню"
    EXIT = "⬅️Выход"

    TESTING = "Тесты"
    SET_SECTION_TESTING = "Выбрать раздел"
    SET_SUBSECTION_TESTING = "Выбрать тему"
    SEE_EXERCISES_TESTING = "Посмотреть предложения"
    ADD_EXERCISE_TESTING = "Добавить предложение"
    EDIT_EXERCISE_TESTING = "Редактировать предложение"
    DEL_EXERCISE_TESTING = "Удалить предложение"

    IRR_VERBS = "Неправильные глаголы"
    SEE_VERBS = "Посмотреть глаголы"
    ADD_VERBS = "Добавить глагол"
    DEL_VERBS = "Удалить глагол"

    NEW_WORDS = "Изучение новых слов"
    SET_SECTION_NEW_WORDS = "Выбрать раздел"
    SEE_NEW_WORDS = "Посмотреть слова/идиомы"
    ADD_NEW_SECTION = "Добавить новый раздел"
    ADD_NEW_WORDS = "Добавить слова/идиомы"
    EDIT_NEW_WORDS = "Изменить слово/идиому"
    DEL_NEW_WORDS = "Удалить слово/идиому"

    SEE_ACTIVITY_DAY = "Посмотреть активность за день"
    SEE_ACTIVITY_WEEK = "Посмотреть активность за неделю"
    SEE_ACTIVITY_MONTH = "Посмотреть активность за месяц"

    USERS = "Пользователи"
    DEL_USER = "Удалить пользователя"
    ADD_WORDS_TO_USER_LEARNING = "Добавить пользователю слова"
    SEE_INDIVIDUAL_WORDS = "Посмотреть слова пользователя"
    DEL_INDIVIDUAL_WORDS = "Удалить слова пользователя"

    BROADCAST = "Рассылка пользователям"
    DEL_BROADCASTS = "Удалить все запланированные рассылки"
    ADD_BROADCAST = "Запланировать рассылку"


class ServiceMessages(StrEnum):
    BOT_ON = "✅ Бот запущен"
    BOT_OFF = "❌ Бот остановлен"


list_right_answers = [
    "You are right!",
    "Awesome!",
    "Great!",
    "Good job",
    "You should be very proud of yourself",
    "Oh, nice!",
    "Fantastic!",
    "Good for you!",
    "That’s really nice",
    "You’re learning fast",
    "Keep up the good work",
    "You’re getting better every day!",
    "Excellent!",
    "Well done!",
    "You’re a genius",
    "Right On!",
    "Very good indeed!",
]
