from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
import asyncio

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
task_queue = asyncio.Queue()
user_task_queue = asyncio.Queue()