from aiogram.filters import Command, CommandStart
from aiogram import types, F, Router
from database.crud import get_developer_user, add_lab_repo
from aiogram.fsm.context import FSMContext
from loguru import logger
from utils import is_valid_github_url, clone_repo
from .developerStates import DeveloperStates
from bot_setup import bot
from pathlib import Path
import os
from bot_setup import dev_task_queue
import asyncio


router = Router()

    
@router.message(F.text.cast(is_valid_github_url))
async def upload_project(message: types.Message, state: FSMContext):
    developer_id = message.from_user.id
    url = message.text
    is_developer = await get_developer_user(developer_id)
    if is_developer:
        await message.reply('Пытаюсь загрузить репозиторий')
        title = await add_lab_repo(developer_id, url)
        path = Path(f'labs/{title}')
        logger.info(f'clonning into {path} by user {developer_id}')
        try:
            await clone_repo(url, path)
            await state.set_state(DeveloperStates.lab_downloaded)
            await state.update_data(title=title)
            await message.reply(f'Лабораторная работа загружена')   
        except Exception as e:
            logger.error(e)
            await message.reply('Что-то не так')
    else:
        await message.reply('ты не разработчик')
        
        
@router.message(F.document, DeveloperStates.lab_downloaded)
async def testing_lab(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    data = await state.get_data()
    title = data['title']
    folder_path = Path(f'labs/{title}/Test/')
    logger.info(f'download into {folder_path} by user {message.from_user.id}')
    folder_path.mkdir(parents=True, exist_ok=True)
    if os.path.exists(folder_path / f'test_{message.from_user.id}.py'):
        os.remove(folder_path / f'test_{message.from_user.id}.py')
    await bot.download_file(file_path, folder_path / f'test_{message.from_user.id}.py')
    await dev_task_queue.put((folder_path, message.from_user.id))   
    await message.reply('Задача успешно загружена')
    