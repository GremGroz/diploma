from aiogram import types, F, Router
from database.crud import get_developer_user, add_lab_repo, get_dev_title
from aiogram.fsm.context import FSMContext
from loguru import logger
from utils import is_valid_github_url, clone_repo
from .states import DeveloperStates
from bot_setup import bot
from pathlib import Path
import os
from bot_setup import task_queue
from keyboards import ButtonTextUser


router = Router()


@router.message(F.text == ButtonTextUser.SEND_LAB)
async def set_lab_state(message: types.Message, state: FSMContext):
    is_developer = await get_developer_user(message.from_user.id)
    if is_developer:
        await message.reply('Введите ссылку на лабораторную работу:')
        logger.info(f'set_lab_state for user {message.from_user.id}')
        await state.set_state(DeveloperStates.lab_download)
    else:
        await message.reply('ты не разработчик')

    
@router.message(F.text.cast(is_valid_github_url), DeveloperStates.lab_download)
async def upload_project(message: types.Message, state: FSMContext):
    developer_id = message.from_user.id
    url = message.text
    await message.reply('Пытаюсь загрузить репозиторий')
    title = await add_lab_repo(developer_id, url)
    path = Path(f'labs/{title}')
    logger.info(f'cloning into {path} by user {developer_id}')
    try:
        await clone_repo(url, path)
        await state.set_state(DeveloperStates.lab_test)
        await state.update_data(title=title)
        await message.reply(f'Лабораторная работа загружена!\nМожете отправить тестовый файл .py')   
    except Exception as e:
        logger.error(e)
        await message.reply('Что-то не так')

@router.message(F.text == ButtonTextUser.TEST_LAB, )
async def set_test_lab(message: types.Message, state: FSMContext):
    is_developer = await get_developer_user(message.from_user.id)
    if is_developer:
        title = await get_dev_title(message.from_user.id)
        if title and os.path.exists(f'labs/{title}/Test'): 
            await state.set_state(DeveloperStates.lab_test)
            await state.update_data(title=title)
            logger.info(f'set_test_lab for user {message.from_user.id}')
            await message.reply('Отправьте тестовый файл .py')
        else:
            await message.reply('Сначала отправьте лабораторную работу')
    else:
        await message.reply('ты не разработчик')
        
@router.message(F.document, DeveloperStates.lab_test)
async def testing_lab(message: types.Message, state: FSMContext):
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
    await task_queue.put((folder_path, message.from_user.id))   
    await state.clear()