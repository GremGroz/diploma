from aiogram import types, F, Router
from database.database import get_db
from config import ADMIN_ID, model, generation_config
from aiogram.fsm.context import FSMContext, StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from database.crud import get_user_info, add_gemini, get_first_last_gemini, get_all_user_from_gemini
from bot_setup import dp, bot
from aiogram.filters import Command
import asyncio
from loguru import logger
from task1.handlers.states import Task1States
from data import user_queue

storage = MemoryStorage()
lock = asyncio.Lock()
router_user_gemini = Router()


@router_user_gemini.message(Command('register'), Task1States.register_for_task)
async def process_group_number(message: types.Message, state: FSMContext):

    telegram_id = message.from_user.id
    logger.info(f'registered {telegram_id}')
    user_queue.append(telegram_id) 
    user = await get_user_info(telegram_id)
    
    await message.reply(f"Спасибо, {user[0]}, вы записаны на выполнение задания.")
    await state.clear()
    

@router_user_gemini.message(Task1States.answer)
async def finalize_task_entry(message: types.Message, state: FSMContext):
    logger.info(f'{user_queue}, {message.from_user.id}')

    # Первый пользователь и первоначальный запрос
    first_user_id = message.from_user.id
    initial_message =  message.text 
    initial_response = model.generate_content('напиши код ' + message.text +
                                              ''' в ответе указывай ТОЛЬКО КОД,
                                              если код написать невозможно ответь ЭТО НЕ ЗАПРОС НА НАПИСАНИЕ КОДА,
                                              в качестве названия функций и переменных не используй названия из запроса''',
                                              generation_config=generation_config)
    
    if initial_response.text == 'ЭТО НЕ ЗАПРОС НА НАПИСАНИЕ КОДА':
        await message.reply("Пожалуйста указывайте ТОЛЬКО название алгоритма!")
        return
    await message.reply(initial_response.text)
    await add_gemini(first_user_id, initial_message, initial_response.text)
    # Цикл обработки запросов
    await bot.send_message(first_user_id, "Задание выполнено. Дождитесь остальных участников.")
    if user_queue:
        user_id = user_queue.pop(0)  # Извлекаем пользователя из очереди
        await bot.send_message(user_id, 
        f"Воспроизведите запрос, после которого генирируется этот код:\n\n {initial_response.text}")
        state_with: FSMContext = FSMContext(
            #bot=bot,  # объект бота
            storage=dp.storage,  # dp - экземпляр диспатчера
            key=StorageKey(
                chat_id=user_id,  # если юзер в ЛС, то chat_id=user_id
                user_id=user_id,
                bot_id=bot.id))
        await state_with.set_state(Task1States.answer)
    else:
        first, last = await get_first_last_gemini()
        stmt = await get_all_user_from_gemini()
        async with get_db() as session:
            result = await session.execute(stmt)
        user_ids = [row[0] for row in result.fetchall()]
        for user in user_ids:
            
            await bot.send_message(user, f'Первый запрос:\n\n\'{first[0]}\'')
            await bot.send_message(user, f'Первый ответ:\n\n {first[1]}')
            await bot.send_message(user, f'Последний запрос:\n\n\'{last[0]}\'')
            await bot.send_message(user, f'Последний ответ:\n\n {last[1]}')
            await bot.send_message(user, "Задание окончено")
        await bot.send_message(ADMIN_ID, "Задание проведено")
    await state.clear()
    


