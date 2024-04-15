from database.base import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from contextlib import asynccontextmanager

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal  = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)



async def init_db():
    import database.models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()
