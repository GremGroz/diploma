from urllib.parse import urlparse
from bot_setup import bot
from git import Repo
from loguru import logger
import os
import shutil
import json
import docker
import asyncio



def is_valid_github_url(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme == "https" and parsed_url.netloc == "github.com" and len(parsed_url.path.split("/")) >= 3


async def clone_repo(url: str, folder_path: str):
    if not is_valid_github_url(url):
        logger.info(f'Invalid GitHub repository URL: {url}')
        raise ValueError(f'Неправильный формат ссылки или неккоректная ссылка: {url}')


    if os.path.exists(folder_path):
        shutil.rmtree(folder_path, ignore_errors=True)
    os.makedirs(folder_path, exist_ok=True)

    try:
        Repo.clone_from(url, folder_path)
        logger.info(f'Repository successfully cloned into {folder_path}')
        tasks_dir = os.path.join(folder_path, 'Test')
        shutil.copy2('docker/Dockerfile', folder_path)
        shutil.copy2('docker/copy.py', folder_path)
        if not os.path.exists(tasks_dir):
            os.makedirs(tasks_dir)
    except Exception as e:
        logger.info(f'Unknown error occurred during cloning: {e}')
        raise RuntimeError(f'Unknown error occurred during cloning: {e}') from e
        


async def run_lab(file_path):
    logger.info('docker function called')
    client = docker.from_env()
    image_name = "sai_labs"
    file_path = os.path.abspath(file_path)
    logger.info(f'{file_path}')
    data_path = os.path.abspath(os.path.join(os.getcwd(), 'data'))
    logger.info(f'{data_path}')
    try:
        # Запуск контейнера с монтированием volume
        logger.info(f"File path: {file_path}")
        client.images.build(path=file_path, dockerfile="Dockerfile", tag=image_name)
        logger.info(f"Container started with image {image_name} and volume {data_path}")
        container = client.containers.run(
            image=image_name,
            volumes={
                data_path: {"bind": "/data", "mode": "rw"},
                }
            ,
            detach=True,
        )
        for line in container.logs(stream=True):
            logger.info(line.strip().decode())
        logger.info(f'Container {container.id} started')
        # Ожидание завершения контейнера
        result = container.wait()
        logger.info(f"Container exited with status code {result['StatusCode']}")
        # Чтение данных из volume
        try:
            logger.info('Trying to read grade.json')
            with open(f"{os.getcwd()}\data\grade.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Data: {data}")
                logger.info(f"Grade: {data['grade']}")
                return data["grade"]
        except Exception as e:
            logger.info(f"Error: {e}")
            return str(e)
        
    except Exception as e:
        logger.info(f"Error: {e}")
        return e
        
        
async def copy_to_test_dict(project_path, user_id):
    new_filename = 'test.py'
    dist_dir = os.path.dirname(project_path)
    shutil.copy2(os.path.join(project_path, f'test_{user_id}.py'), dist_dir)
    if os.path.exists(os.path.join(dist_dir, new_filename)):
        os.remove(os.path.join(dist_dir, new_filename))
    os.rename(os.path.join(dist_dir, f'test_{user_id}.py'), os.path.join(dist_dir, new_filename))
    logger.info('copied')
    

async def dev_process_task(queue):
    while True:
        project_path, user_id = await queue.get()
        await copy_to_test_dict(project_path, user_id)
        grade = await run_lab(os.path.dirname(project_path))
        logger.info(type(grade))
        if isinstance(grade, str):
            await bot.send_message(chat_id=user_id, text=grade)
        elif isinstance(grade, json.decoder.JSONDecodeError):
            await bot.send_message(chat_id=user_id, text='Try except перед записью ошибки в файл должен конвертировать ошибку в строку.')
        elif grade == 'Error: Expecting value: line 2 column 1 (char 1)':
            await bot.send_message(chat_id=user_id, text='Проверьте запись оценки в файл на корректность')
        else:
            await bot.send_message(chat_id=user_id, text=f"Оценка: {grade}")
        queue.task_done()
        
        
        

