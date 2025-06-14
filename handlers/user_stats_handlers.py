from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message

from keyboards import keyboard_builder
from lexicon import MessageTexts, BasicButtons
from services.user import UserService
from services.user_progress import UserProgressService

user_stats_router: Router = Router()


@user_stats_router.message(Command(commands=["stats"]), ~StateFilter(default_state))
async def stats_user_command(message: Message,
                             user_service: UserService,
                             ):
    user_id = message.from_user.id
    info = await user_service.get_user_info_text(user_id, admin=False)
    await message.answer(f'{info}\n\n{MessageTexts.STATS_USER}',
                         reply_markup=await keyboard_builder(1, BasicButtons.CLOSE, args_go_first=False,
                                                             stats_today=BasicButtons.TODAY,
                                                             stats_last_week=BasicButtons.LAST_WEEK,
                                                             stats_last_month=BasicButtons.LAST_MONTH))


@user_stats_router.callback_query(F.data == 'stats_today')
@user_stats_router.callback_query(F.data == 'stats_last_week')
@user_stats_router.callback_query(F.data == 'stats_last_month')
async def see_stats_user(callback: CallbackQuery,
                         user_progress_service: UserProgressService,
                         ):
    await callback.answer()
    cbdata = callback.data
    user_id = callback.from_user.id
    if cbdata == 'stats_today':
        info = await user_progress_service.get_activity_by_user(user_id)
    elif cbdata == 'stats_last_week':
        info = await user_progress_service.get_activity_by_user(user_id, interval=7)
    else:
        info = await user_progress_service.get_activity_by_user(user_id, interval=30)
    await callback.message.answer(info, reply_markup=await keyboard_builder(1, BasicButtons.CLOSE))
