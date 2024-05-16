from urllib.parse import urlparse
from bot_setup import bot
from git import Repo
from loguru import logger
from database.crud import add_grade
from keyboards import get_user_keyboard
from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import json
import docker
import stat
import asyncio




executor = ThreadPoolExecutor(max_workers=4)

async def run_in_executor(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, func, *args)

def is_valid_github_url(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme == "https" and parsed_url.netloc == "github.com" and len(parsed_url.path.split("/")) >= 3

def handle_remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

async def clone_repo(url: str, folder_path: str):
    if not is_valid_github_url(url):
        logger.error(f'Invalid GitHub repository URL: {url}')
        raise ValueError(f'Неправильный формат ссылки или некорректная ссылка: {url}')

    if os.path.exists(folder_path):
        shutil.rmtree(folder_path, ignore_errors=False, onerror=handle_remove_readonly)
    os.makedirs(folder_path, exist_ok=True)

    try:
        Repo.clone_from(url, folder_path)
        logger.info(f'Repository successfully cloned into {folder_path}')
        tasks_dir = os.path.join(folder_path, 'Test')
        for filename in ['docker/Dockerfile', 'docker/copy_master.py']:
            shutil.copy2(filename, folder_path)
        os.makedirs(tasks_dir, exist_ok=True)
    except Exception as e:
        logger.error(f'Unknown error occurred during cloning: {e}')
        raise RuntimeError(f'Unknown error occurred during cloning: {e}') from e
    

async def run_lab(file_path):
    data_path = os.path.abspath(os.path.join(os.getcwd(), 'data'))
    json_file_path = os.path.join(data_path, 'grade.json')

    with open(json_file_path, 'w') as json_file:
        json.dump({'grade': 'ошибка в записи оценки'}, json_file)

    logger.info('Docker function called')
    client = docker.from_env()
    image_name = "sai_labs"
    file_path = os.path.abspath(file_path)
    
    def build_and_run_container():
        try:
            logger.info(f'Building Docker image from {file_path}')
            client.images.build(path=file_path, dockerfile="Dockerfile", tag=image_name, rm=True)
            logger.info(f'Starting container with image {image_name}')
            container = client.containers.run(
                image=image_name,
                volumes={data_path: {"bind": "/data", "mode": "rw"}},
                detach=True,
                remove=True
            )

            for line in container.logs(stream=True):
                decoded_line = line.strip().decode()
                logger.info(decoded_line)
                if "Error" in decoded_line:
                    return decoded_line

            result = container.wait()
            logger.info(f"Container exited with status code {result['StatusCode']}")

            try:
                with open(json_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Grade: {data['grade']}")
                    return data["grade"]
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return str(e)
            except Exception as e:
                logger.error(f"Error reading grade.json: {e}")
                return str(e)
        except Exception as e:
            logger.error(f"Docker error: {e}")
            return str(e)

    # Запуск блокирующей функции в пуле потоков
    return await run_in_executor(build_and_run_container)

# async def run_lab(file_path):
#     data_path = os.path.abspath(os.path.join(os.getcwd(), 'data'))
#     json_file_path = os.path.join(data_path, 'grade.json')

#     with open(json_file_path, 'w') as json_file:
#         json.dump({'grade': 'ошибка в записи оценки'}, json_file)

#     logger.info('Docker function called')
#     client = docker.from_env()
#     image_name = "sai_labs"
#     file_path = os.path.abspath(file_path)
    
#     try:
#         logger.info(f'Building Docker image from {file_path}')
#         client.images.build(path=file_path, dockerfile="Dockerfile", tag=image_name, rm=True)
#         logger.info(f'Starting container with image {image_name}')
#         container = client.containers.run(
#             image=image_name,
#             volumes={data_path: {"bind": "/data", "mode": "rw"}},
#             detach=True,
#             remove=True
#         )

#         for line in container.logs(stream=True):
#             decoded_line = line.strip().decode()
#             logger.info(decoded_line)
#             if "Error" in decoded_line:
#                 return decoded_line

#         result = container.wait()
#         logger.info(f"Container exited with status code {result['StatusCode']}")

#         try:
#             with open(json_file_path, "r", encoding="utf-8") as f:
#                 data = json.load(f)
#                 logger.info(f"Grade: {data['grade']}")
#                 return data["grade"]
#         except json.JSONDecodeError as e:
#             logger.error(f"JSON decode error: {e}")
#             return str(e)
#         except Exception as e:
#             logger.error(f"Error reading grade.json: {e}")
#             return str(e)
#     except Exception as e:
#         logger.error(f"Docker error: {e}")
#         return str(e)

async def copy_to_test_dir(project_path, user_id):
    new_filename = 'task.py'
    dist_dir = os.path.dirname(project_path)
    user_task_file = os.path.join(project_path, f'task_{user_id}.py')

    if os.path.exists(user_task_file):
        shutil.copy2(user_task_file, dist_dir)
        new_file_path = os.path.join(dist_dir, new_filename)
        if os.path.exists(new_file_path):
            os.remove(new_file_path)
        os.rename(os.path.join(dist_dir, f'task_{user_id}.py'), new_file_path)
        logger.info('Task copied successfully')
        await bot.send_message(chat_id=user_id, text='Задача успешно загружена')
    else:
        logger.error(f"File {user_task_file} does not exist")
        await bot.send_message(chat_id=user_id, text='Файл задачи не найден')

async def process_task(queue):
    while True:
        project_path, user_id = await queue.get()
        await copy_to_test_dir(project_path, user_id)
        await bot.send_message(chat_id=user_id, text='Запускаю проверку')
        grade = await run_lab(os.path.dirname(project_path))
        
        if isinstance(grade, str):
            await bot.send_message(chat_id=user_id, text=grade)
        elif isinstance(grade, json.decoder.JSONDecodeError):
            await bot.send_message(chat_id=user_id, text='Ошибка в записи оценки: неправильный формат JSON')
        else:
            await bot.send_message(chat_id=user_id, text=f"Оценка: {grade}")

        queue.task_done()




async def user_process_task(queue):
    while True:
        project_path, title, user_id = await queue.get()
        logger.info(f'queue size: {queue.qsize()}')
        await copy_to_test_dir(project_path, user_id)
        await bot.send_message(chat_id=user_id, text='Запускаю проверку')
        grade = await run_lab(os.path.dirname(project_path))
        keyboard = await get_user_keyboard(user_id)
        
        if isinstance(grade, str):
            await bot.send_message(chat_id=user_id, text=grade, reply_markup=keyboard)
        else:
            await add_grade(user_id=user_id, lab_work=title, grade=grade)
            
            await bot.send_message(chat_id=user_id, text=f"Оценка: {grade}", reply_markup=keyboard)

        queue.task_done()

