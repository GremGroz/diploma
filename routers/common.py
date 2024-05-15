
from aiogram import types, F, Router
from config import ADMIN_ID
from routers.states import UserStates
from database.crud import get_developer_users
from aiogram.fsm.context import FSMContext
from loguru import logger
from utils import is_valid_github_url
from keyboards import get_user_keyboard
router = Router()


@router.message()
async def echo_message(message: types.Message):
    logger.info(f'message {message.text} from {message.from_user.id}')
    developers = await get_developer_users()
    is_developer = message.from_user.id in developers
    logger.info(is_developer)
    keyboard = await get_user_keyboard(message.from_user.id)
    message.reply('',reply_markup=keyboard)