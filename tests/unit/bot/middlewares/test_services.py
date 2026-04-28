from unittest.mock import AsyncMock, patch

from bot.middlewares.services import ServicesMiddleware
from bot.services.daily_statistics import DailyStatisticsService
from bot.services.new_words import NewWordsService
from bot.services.testing import TestingService as _TestingService
from bot.services.user import UserService
from bot.services.user_progress import UserProgressService
from bot.services.user_words_learning import UserWordsLearningService


async def test_services_middleware_injects_all_services_and_calls_handler():
    session_maker = object()
    handler = AsyncMock(return_value="handled")
    data = {"existing": "value"}

    with patch(
        "bot.middlewares.services.get_session_maker", return_value=session_maker
    ):
        middleware = ServicesMiddleware()
        result = await middleware(handler, event=object(), data=data)

    assert result == "handled"
    assert data["existing"] == "value"
    assert isinstance(data["testing_service"], _TestingService)
    assert isinstance(data["user_progress_service"], UserProgressService)
    assert isinstance(data["user_service"], UserService)
    assert isinstance(data["new_words_service"], NewWordsService)
    assert isinstance(data["user_words_learning_service"], UserWordsLearningService)
    assert isinstance(data["daily_statistics_service"], DailyStatisticsService)
    handler.assert_awaited_once()
