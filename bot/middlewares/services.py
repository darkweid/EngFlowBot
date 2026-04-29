from aiogram import BaseMiddleware

from bot.db.init import get_session_maker
from bot.db.repositories.daily_statistics import DailyStatisticsRepository
from bot.db.repositories.new_words import NewWordsRepository
from bot.db.repositories.testing import TestingRepository
from bot.db.repositories.user import UserRepository
from bot.db.repositories.user_progress import UserProgressRepository
from bot.db.repositories.user_words_learning import UserWordsLearningRepository
from bot.services.daily_statistics import DailyStatisticsService
from bot.services.new_words import NewWordsService
from bot.services.testing import TestingService
from bot.services.user import UserService
from bot.services.user_progress import UserProgressService
from bot.services.user_words_learning import UserWordsLearningService


class ServicesMiddleware(BaseMiddleware):
    """
    Injects all services into update data dictionary.
    Services are created lazily - a new instance for each update,
    but use a common sessionmaker.
    """

    def __init__(self) -> None:
        self._session_maker = get_session_maker()

    async def __call__(self, handler, event, data):
        sm = self._session_maker

        data.update(
            testing_service=TestingService(repository=TestingRepository(sm)),
            user_progress_service=UserProgressService(
                repository=UserProgressRepository(sm)
            ),
            user_service=UserService(repository=UserRepository(sm)),
            new_words_service=NewWordsService(repository=NewWordsRepository(sm)),
            user_words_learning_service=UserWordsLearningService(
                repository=UserWordsLearningRepository(sm)
            ),
            daily_statistics_service=DailyStatisticsService(
                repository=DailyStatisticsRepository(sm)
            ),
        )
        return await handler(event, data)
