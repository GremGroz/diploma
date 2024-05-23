from aiogram.filters import Command, CommandStart
from aiogram import types, F, Router
from routers.states import UserStates
from database.crud import get_user_info, add_user, get_grades_by_student_id
from aiogram.fsm.context import FSMContext
from loguru import logger
from keyboards import get_user_keyboard, get_dynamic_user_keyboard
from bot_setup import bot, user_task_queue
from pathlib import Path
import asyncio
import os


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
        keyboard = await get_user_keyboard(telegram_id)
        await message.reply(f"{check_user[0]}, вы уже зарегистрированы", reply_markup=keyboard)
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
    keyboard = await get_user_keyboard(message.from_user.id)
    await message.reply(f"Спасибо, {name}, ваши данные сохранены.", reply_markup=keyboard)
    await state.clear()
    
@router.message(F.text == "Список лабораторных работ")
async def handle_show_labs(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} запросил список лабораторных работ")
    user_id = message.from_user.id
    await state.set_state(UserStates.selecting_lab)
    keyboard = await get_dynamic_user_keyboard(user_id)
    await message.reply("Выберите лабораторную работу", reply_markup=keyboard)
    
@router.message(F.text=="Вернуться")
async def handle_back_to_main(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} вернулся в главное меню")
    await state.clear()
    keyboard = await get_user_keyboard(message.from_user.id)
    await message.reply("Главное меню", reply_markup=keyboard)

@router.message(F.text == "Мои оценки")
async def handle_show_grades(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} запросил свои оценки")
    user_id = message.from_user.id
    grades = await get_grades_by_student_id(user_id)
    
    if grades:
        response = "Ваши оценки:\n"
        for lab_work, grade in grades:
            response += f"{lab_work}: {grade}\n"
    else:
        response = "У вас пока нет оценок."
    
    await message.reply(response)

@router.message(UserStates.selecting_lab)
async def handle_lab_selection(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} выбрал лабораторную работу {message.text}")
    await state.set_state(UserStates.passing_lab)
    title = message.text
    if title.endswith(" ✅"):
        title = title[:-2]
    if not os.path.exists(f'labs/{title}'):
        await message.reply(f"Лабораторной работы \'{title}\' не существует")
        await state.set_state(UserStates.selecting_lab)
        return
    await state.update_data(title=title)
    keyboard = await get_user_keyboard(message.from_user.id)
    await message.reply("Вы можете перерешивать задачу неограниченное количество раз, в оценку записывается последний результат")
    await message.reply("Отправьте своё решение файлом .py", reply_markup=keyboard)



@router.message(F.document, UserStates.passing_lab)
async def handle_passing_lab(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    data = await state.get_data()
    title = data['title']
    folder_path = Path(f'labs/{title}/Test/')
    logger.info(f'download into {folder_path} by user {message.from_user.id}')
    folder_path.mkdir(parents=True, exist_ok=True)
    if os.path.exists(folder_path / f'task_{message.from_user.id}.py'):
        os.remove(folder_path / f'task_{message.from_user.id}.py')
    await bot.download_file(file_path, folder_path / f'task_{message.from_user.id}.py')
    await user_task_queue.put((folder_path, title, message.from_user.id))   
    await state.clear()
