from enum import Enum

from aiogram.fsm.context import FSMContext


async def update_state_data(state: FSMContext, **kwargs):
    """
    Update state data with the provided key-value pairs.

    Parameters:
    - state (FSMContext): The current FSMContext object.
    - kwargs: Key-value pairs to add or update in the state data.

    This function:
    - Retrieves the current state data.
    - Converts Enum values to their names.
    - Updates the state data with the provided key-value pairs.
    - Sets the updated data back to the state.
    """
    data = await state.get_data()

    for key, value in kwargs.items():
        if isinstance(value, Enum):
            kwargs[key] = value.name

    data.update(kwargs)

    await state.set_data(data)
