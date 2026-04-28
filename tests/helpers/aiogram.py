from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock


class FakeState:
    def __init__(self, data: dict | None = None) -> None:
        self._data = dict(data or {})
        self.clear = AsyncMock(side_effect=self._clear)
        self.get_data = AsyncMock(side_effect=self._get_data)
        self.set_data = AsyncMock(side_effect=self._set_data)
        self.set_state = AsyncMock()
        self.update_data = AsyncMock(side_effect=self._update_data)

    async def _clear(self):
        self._data.clear()

    async def _get_data(self):
        return dict(self._data)

    async def _set_data(self, data: dict):
        self._data = dict(data)

    async def _update_data(self, **kwargs):
        self._data.update(kwargs)


class FakeMessage:
    def __init__(
        self,
        *,
        text: str = "",
        user_id: int = 123,
        full_name: str = "Test User",
        username: str | None = "test_user",
    ) -> None:
        self.text = text
        self.from_user = SimpleNamespace(
            id=user_id,
            full_name=full_name,
            username=username,
            first_name=full_name.split()[0],
        )
        self.answer = AsyncMock()
        self.reply = AsyncMock()
        self.delete = AsyncMock()


class FakeCallback:
    def __init__(
        self,
        *,
        data: str = "",
        user_id: int = 123,
        full_name: str = "Test User",
        username: str | None = "test_user",
    ) -> None:
        self.data = data
        self.from_user = SimpleNamespace(
            id=user_id,
            full_name=full_name,
            username=username,
        )
        self.answer = AsyncMock()
        self.message = SimpleNamespace(
            answer=AsyncMock(),
            edit_text=AsyncMock(),
            delete=AsyncMock(),
        )
