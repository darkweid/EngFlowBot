from enum import Enum
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.utils.state_data_updater import update_state_data


class Mode(Enum):
    TRAINING = "training"


async def test_update_state_data_merges_existing_data_and_enum_names():
    state = SimpleNamespace(
        get_data=AsyncMock(return_value={"user_id": 123}),
        set_data=AsyncMock(),
    )

    await update_state_data(state, mode=Mode.TRAINING, subsection="Travel")

    state.get_data.assert_awaited_once_with()
    state.set_data.assert_awaited_once_with(
        {
            "user_id": 123,
            "mode": "TRAINING",
            "subsection": "Travel",
        }
    )
