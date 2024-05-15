from aiogram import types, F, Router
from database.database import get_db
from bot_setup import dp, bot
from database.crud import get_all_user
from loguru import logger
from config import ADMIN_ID, model, generation_config
from task1.handlers.states import Task1States, AdminStates
from database.crud import get_user_info, clear_gemini_table, add_theme, add_lab_work
from aiogram.fsm.context import FSMContext, StorageKey
from loguru import logger
from data import user_queue
from aiogram.filters import Command, CommandStart
from keyboards import get_admin_keyboard
import copy


router_admin_gemini = Router()

@router_admin_gemini.message(CommandStart(), F.from_user.id == ADMIN_ID)
async def start(message: types.Message):
     await message.reply("Привет!\nТы администратор, просто скажи мне когда запустить задание для студентов, и я сделаю это.",
     reply_markup=get_admin_keyboard())
     
@router_admin_gemini.message(F.text == 'Добавить лабораторную работу', F.from_user.id == ADMIN_ID)
async def add_lab(message: types.Message, state: FSMContext):
    await message.reply('Введите номер темы лабораторной работы:')
    await state.set_state(AdminStates.type_num_lab)

@router_admin_gemini.message(AdminStates.type_num_lab)
async def add_lab(message: types.Message, state: FSMContext):
    await message.reply('Введите id студента:')
    await state.set_state(AdminStates.type_developer)
    await state.update_data(num_lab=int(message.text))
    
    
@router_admin_gemini.message(AdminStates.type_developer)
async def add_lab(message: types.Message, state: FSMContext):
    await message.reply('Введите название лабораторной работы:')
    await state.set_state(AdminStates.type_title)
    await state.update_data(developer=int(message.text))
    
@router_admin_gemini.message(AdminStates.type_title)
async def add_lab(message: types.Message, state: FSMContext):
    lab_num = state.get_data()['num_lab']
    developer = state.get_data()['developer']
    title = message.text
    description = message.text
    await add_lab_work(lab_num=lab_num, developer_id=developer, title=title, description=description)
    await state.clear()


@router_admin_gemini.message(Command('start_task_recording'))
async def start_task_recording(message: types.Message):
    await clear_gemini_table()
    logger.info(message.text)
    if message.from_user.id != ADMIN_ID:
        await message.reply("Вы не администратор!")
        return

    # Получаем список всех пользователей из базы данных
    stmt = await get_all_user()
    logger.info(stmt)
    async with get_db() as session:
        result = await session.execute(stmt)
        user_ids = [row[0] for row in result.fetchall()]

    # Отправляем сообщение каждому пользователю
    for user_id in user_ids:
        state_with: FSMContext = FSMContext(
            #bot=bot,  # объект бота
            storage=dp.storage,  # dp - экземпляр диспатчера
            key=StorageKey(
                chat_id=user_id,  # если юзер в ЛС, то chat_id=user_id
                user_id=user_id,
                bot_id=bot.id))
        await state_with.set_state(Task1States.register_for_task)
        cur_state, cur_user = await state_with.get_state(), state_with.key.user_id
        logger.info(f'Состояние {cur_state}, для пользователя {cur_user}')
        try:
            await bot.send_message(user_id, "Запишитесь на задание, введите /register")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    await message.reply("Сообщение отправлено всем пользователям.")
    

@router_admin_gemini.message(Command('finalize_task_entry'))    
async def finalize_task_entry(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Вы не администратор!")
        return
    if user_queue:
        user_id = user_queue.pop(0)  # Извлекаем пользователя из очереди
        await bot.send_message(user_id, 
        "Вы выбраны первым\n\nЗадайте запрос на написание несложного алгоритма\n\nВведите ТОЛЬКО название алгоритма")
        state_with: FSMContext = FSMContext(
            #bot=bot,  # объект бота
            storage=dp.storage,  # dp - экземпляр диспатчера
            key=StorageKey(
                chat_id=user_id,  # если юзер в ЛС, то chat_id=user_id
                user_id=user_id,
                bot_id=bot.id))
        await state_with.set_state(Task1States.answer)
        user = await get_user_info(user_id)
        await message.reply(f"Задача назначена пользователю {user[0]}")
    else:
        await message.reply("Очередь пользователей пуста.")
        

@router_admin_gemini.message(Command('test'))    
async def test(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Вы не администратор!")
        return
    await state.set_state(AdminStates.test)
    current_state = await state.get_state()
    logger.info(f"Current state after: {current_state}")
    await message.reply('Введите test запрос для гугл Gemini')

    

@router_admin_gemini.message(AdminStates.test)    
async def test(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Current state after: {current_state}")
    initial_request =  message.text
    logger.info(initial_request)
    initial_response = model.generate_content(initial_request, generation_config=generation_config)
    await message.reply(initial_response.text)
    await state.clear()

