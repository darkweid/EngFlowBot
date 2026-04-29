from aiogram.filters.state import State, StatesGroup


class UserFSM(StatesGroup):
    default = State()
    existing_user = State()
    set_reminder_time = State()


class TestingFSM(StatesGroup):
    default = State()  # Пользователь проходит тестирование
    selecting_section = State()  # Пользователь выбирает раздел в тестах
    selecting_subsection = State()  # Пользователь выбирает подраздел в тестах
    selected_subsection = State()  # Пользователь выбрал подраздел в тестах
    in_process = State()


class WordsLearningFSM(StatesGroup):
    default = State()  # Пользователь изучает новые слова
    add_words_to_learn = State()  # Пользователь добавляет слова для изучения
    selecting_section = State()  # Пользователь выбирает раздел
    selecting_subsection = State()  # Пользователь выбирает подраздел
    selected_subsection = State()  # Пользователь выбрал подраздел
    in_process = State()


class IrrVerbsLearningFSM(StatesGroup):
    pass


class SentencesForTranslationFSM(StatesGroup):
    pass


class AdminFSM(StatesGroup):
    default = State()

    # Testing
    select_section_testing = State()
    select_subsection_testing = State()
    select_management_action_testing = State()
    adding_exercise_testing = State()
    deleting_exercise_testing = State()
    editing_exercise_testing = State()
    ready_to_edit_exercise_testing = State()
    ready_to_delete_exercise_testing = State()

    # Broadcasting
    broadcasting_set_date_time = State()
    broadcasting_set_text = State()

    # New_words
    select_section_words = State()
    select_subsection_words = State()
    select_management_action_words = State()
    adding_exercise_words = State()
    deleting_exercise_words = State()
    editing_exercise_words = State()
    ready_to_edit_exercise_words = State()
    ready_to_delete_exercise_words = State()
    adding_new_section = State()

    # Irr_verbs

    # Users
    see_user_info = State()
    see_user_management = State()
    user_managing = State()
    adding_words_to_user = State()
    deleting_user = State()
