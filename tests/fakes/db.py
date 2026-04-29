from __future__ import annotations

from collections.abc import Iterable
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock


class FakeScalarResult:
    def __init__(self, values: Iterable | None = None, scalar_value=None) -> None:
        self._values = list(values or [])
        self._scalar_value = scalar_value

    def all(self):
        return self._values

    def first(self):
        return self._values[0] if self._values else None


class FakeExecuteResult:
    def __init__(
        self,
        *,
        scalar_value=None,
        scalar_values: Iterable | None = None,
        fetchall_values: Iterable | None = None,
        one_value=None,
        rowcount: int = 0,
    ) -> None:
        self._scalar_value = scalar_value
        self._scalar_values = list(scalar_values or [])
        self._fetchall_values = list(fetchall_values or [])
        self._one_value = one_value
        self.rowcount = rowcount

    def scalar(self):
        return self._scalar_value

    def scalar_one_or_none(self):
        return self._scalar_value

    def scalars(self):
        return FakeScalarResult(self._scalar_values)

    def fetchall(self):
        return self._fetchall_values

    def one(self):
        return self._one_value


class AsyncTransactionContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


class FakeAsyncSession:
    def __init__(self, execute_results: Iterable[FakeExecuteResult] | None = None):
        self.execute_results = list(execute_results or [])
        self.executed_statements = []
        self.add = MagicMock()
        self.add_all = MagicMock()
        self.begin = MagicMock(return_value=AsyncTransactionContext())
        self.execute = AsyncMock(side_effect=self._execute)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    async def _execute(self, statement):
        self.executed_statements.append(statement)
        if self.execute_results:
            return self.execute_results.pop(0)
        return FakeExecuteResult()


class FakeSessionMaker:
    def __init__(self, session: FakeAsyncSession):
        self.session = session
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.session


def statement_sql(statement) -> str:
    return str(statement.compile(compile_kwargs={"literal_binds": True}))


def row(**values):
    return SimpleNamespace(**values)
