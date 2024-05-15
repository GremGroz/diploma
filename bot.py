from task1.handlers.AdminHandlers import router_admin_gemini
from task1.handlers.UserHandlers import router_user_gemini
from routers.userRouters import router as user_router
from routers.developerRouters import router as developer_router
from routers.common import router as common_router
from database.database import init_db
from loguru import logger
from bot_setup import dp, bot, task_queue, user_task_queue
import asyncio
from utils import process_task, user_process_task


logger.add("bot_debug.log", format="{time} {level} {message}", level="INFO")



dp.include_routers(developer_router,
                   router_admin_gemini,
                   user_router,
                   router_user_gemini,
                   common_router)


async def main():
    logger.info('Bot is running')
    asyncio.create_task(process_task(task_queue))
    asyncio.create_task(user_process_task(user_task_queue))
    await init_db()
    await dp.start_polling(bot)
    
    
if __name__ == "__main__":
    asyncio.run(main())
