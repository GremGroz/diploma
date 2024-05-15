from database.database import get_db
from database.models import User, Gemini, LabWorks, Grade, Themes
from sqlalchemy import select, delete, update
from sqlalchemy.sql import asc, desc, and_
from loguru import logger
from datetime import datetime


async def get_tested_labs():

    stmt = (
        select(LabWorks.title)
        .where(LabWorks.test_code == True)
        .distinct()
    )
    async with get_db() as session:
        result = await session.execute(stmt)
        tested_labs = result.fetchall()
        return [row[0] for row in tested_labs]

async def get_passed_labs(user_id: int):
    stmt = select(Grade.lab_work).where(Grade.user_id == user_id)
    async with get_db() as session:
        result = await session.execute(stmt)
        passed_labs = result.fetchall()
        return [row[0] for row in passed_labs] if passed_labs else []
    


async def add_user(telegram_id: int, name: str, group: str):
    async with get_db() as session:
        new_user = User(telegram_id=telegram_id, name=name, group=group)
        session.add(new_user)
    return

# async def get_cheked_lab(user_id):
#     stmt = (
#         select(LabWorks.test_code)
#         .where(LabWorks.developer_id == user_id)
#     )
#     async with get_db() as session:
#         result = await session.execute(stmt)
#         cheked_lab = result.fetchone()
#         return cheked_lab[0]
    


async def get_dev_title(user_id):
    stmt = (
        select(LabWorks.title)
        .where(LabWorks.developer_id == user_id)
    )
    
    async with get_db() as session:
        result = await session.execute(stmt)
        dev_title = result.fetchone()
        return str(dev_title[0]) if dev_title else None
            


async def add_lab_repo(developer_id: int, description: str):
    stmt = (
            select(LabWorks.lab_num, LabWorks.title)
            .where(LabWorks.developer_id==developer_id)
        )
    async with get_db() as session:
        result = await session.execute(stmt)
        lab_num_edit, title = result.fetchone()
      
    async with get_db() as session:
        updater = (
            update(LabWorks)
            .where(LabWorks.lab_num==lab_num_edit)
            .values(description=description)
        )
        await session.execute(updater)
    return title
    

async def get_developer_user(developer_id):
    stmt = select(LabWorks.developer_id).where(LabWorks.developer_id == developer_id)
    async with get_db() as session:
        result = await session.execute(stmt)
        developers_data = result.fetchone()
    if developers_data:
        return developers_data
    else:
        return None 

async def get_developer_users():
    stmt = select(LabWorks.developer_id)
    async with get_db() as session:
        result = await session.execute(stmt)
        developers_data = result.fetchall()

    
    if developers_data:
        developers_ids = [developers_id[0] for developers_id in developers_data]
        logger.info(developers_ids)
        return developers_ids
    else:
        return None 



async def add_theme(title: str):
    async with get_db() as session:
        new_theme = Themes(title=title)
        session.add(new_theme)

async def add_lab_work(lab_num: int, developer_id: int, title: str, description:str):
    async with get_db() as session:
        new_lab = LabWorks(
            lab_num=lab_num, developer_id=developer_id,
            title=title, description=description,
                           )
        session.add(new_lab)
    return

async def add_grade(user_id: int, lab_work: int, grade: int):
    async with get_db() as session:
        # Проверка существующей записи
        stmt = select(Grade).where(Grade.user_id == user_id, Grade.lab_work == lab_work)
        result = await session.execute(stmt)
        existing_grade = result.scalar_one_or_none()
        
        if existing_grade:
            # Если запись существует, обновляем её
            update_stmt = (
                update(Grade)
                .where(Grade.user_id == user_id, Grade.lab_work == lab_work)
                .values(grade=grade, completed_at=datetime.utcnow())
            )
            await session.execute(update_stmt)
        else:
            # Если записи не существует, добавляем новую
            new_grade = Grade(
                user_id=user_id,
                lab_work=lab_work,
                grade=grade
            )
            session.add(new_grade)
        
        # Подтверждение транзакции
        await session.commit()


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