from aiogram.filters import Command, CommandStart
from aiogram import types, F, Router
from routers.states import UserStates
from database.crud import get_user_info, add_user
from aiogram.fsm.context import FSMContext
from loguru import logger
import asyncio


router = Router()
queue = asyncio.Queue()

@router.message(CommandStart())
async def input_surname(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    logger.info(f"Пользователь {telegram_id} начал взаимодействие с ботом")
    check_user = await get_user_info(telegram_id)
    if not check_user:
        await state.set_state(UserStates.lastname)
        current_state = await state.get_state()
        logger.info(f"Current state after: {current_state}")
        await message.reply("Привет!\n\nЯ бот для проведения лабораторных работ по СИИ.\nДавайте знакомиться!")
        await message.reply('Введите Фамилию:')
    else:
        await message.reply(f"{check_user[0]}, вы уже зарегестрированы")
    logger.debug(f"Текущее состояние FSM: {await state.get_state()}")
    
    


@router.message(UserStates.lastname)
async def process_lastname(message: types.Message, state: FSMContext):
    await state.update_data(lastname=message.text)
    await state.set_state(UserStates.firstname)
    await message.reply("Введите ваше имя:")
    
    
    
@router.message(UserStates.firstname)
async def process_firstname(message: types.Message, state: FSMContext):
    await state.update_data(firstname=message.text)
    await state.set_state(UserStates.group)
    await message.reply("Введите номер вашей группы:")
    
    
@router.message(UserStates.group)
async def process_group_number(message: types.Message, state: FSMContext):
    
    await state.update_data(group=message.text)
    data = await state.get_data()
    name = data['lastname'] + ' ' + data['firstname']

    await add_user(telegram_id=message.from_user.id, name=name, group=message.text)
    
    await message.reply(f"Спасибо, {name}, ваши данные сохранены.")
    await state.clear()