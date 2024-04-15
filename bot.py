from task1.handlers.AdminHandlers import router_admin_gemini
from task1.handlers.UserHandlers import router_user_gemini
from routers.userRouters import router
from database.database import init_db
from loguru import logger
from bot_setup import dp, bot
import asyncio



logger.add("bot_debug.log", format="{time} {level} {message}", level="INFO")



dp.include_router(router)
dp.include_router(router_admin_gemini)
dp.include_router(router_user_gemini)
# router.register_message_handler(start_task_recording, commands=['start_task_recording'])
# router.register_message_handler(finalize_task_entry, commands=['finalize_task_entry'])

async def main():
    await init_db()
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())