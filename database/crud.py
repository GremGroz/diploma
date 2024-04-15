from database.database import get_db
from database.models import User, Gemini
from sqlalchemy import select, delete, bindparam
from sqlalchemy.sql import asc, desc

async def add_user(telegram_id: int, name: str, group: str):
    async with get_db() as session:
        new_user = User(telegram_id=telegram_id, name=name, group=group)
        session.add(new_user)
    return
    

async def add_theme(title: str):
    return

async def add_lab_work(lab_num: int, developer_id: int, title: str, description:str, test_code: bool):
    return

async def add_grade(user_id: int, lab_work_id: int, grade: int):
    return

async def add_gemini(user_id: int, request: str, response: str):
    async with get_db() as session:
        gemini = Gemini(
        user_id=user_id,
        request=request,
        response=response
        )
        session.add(gemini)


async def get_first_last_gemini():
    first = select(Gemini.request, Gemini.response).order_by(asc(Gemini.created_at))
    last = select(Gemini.request, Gemini.response).order_by(desc(Gemini.created_at))
    async with get_db() as session:
        result_first = (await session.execute(first)).first()
        result_last = (await session.execute(last)).first()
    if result_first:
        return result_first, result_last
    else:
        return None 

async def clear_gemini_table():
    async with get_db() as session:
        await session.execute(delete(Gemini)) 
    return

async def get_user_info(telegram_id: int):

    stmt = select(User.name, User.group).where(User.telegram_id == telegram_id)
    async with get_db() as session:
        result = await session.execute(stmt)
        user_data = result.fetchone()
    
    if user_data:
        return user_data[0], user_data[1]
    else:
        return None 
    
async def get_all_user_from_gemini():
    return select(Gemini.user_id)   

async def get_all_user():
    return select(User.telegram_id)


#TODO print smth