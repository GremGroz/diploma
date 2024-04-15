from sqlalchemy import Column, Integer, String, DateTime, func, BigInteger, ForeignKey, Boolean
from database.base import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'users'
    telegram_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=False)
    name = Column(String)
    group = Column(String)
    
class Themes(Base):
    __tablename__ = 'themes'
    id = Column(Integer, primary_key=True)
    title = Column(String)


class LabWorks(Base):
    __tablename__ = 'lab_works'
    lab_num = Column(Integer, ForeignKey(Themes.id), primary_key=True, autoincrement=False)
    developer_id = Column(BigInteger, ForeignKey(User.telegram_id), primary_key=True, autoincrement=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    test_code = Column(Boolean, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    developer = relationship(User)


    
class Grade(Base):
    __tablename__ = 'grade'
    user_id = Column(BigInteger, ForeignKey(User.telegram_id), primary_key=True)
    lab_work_id = Column(Integer, ForeignKey(Themes.id), primary_key=True)
    grade = Column(Integer)
    completed_at = Column(DateTime, server_default=func.now())
    user = relationship(User)
    lab_work = relationship(Themes)


class Gemini(Base):
    __tablename__ = 'gemini_answer'
    user_id = Column(BigInteger, ForeignKey(User.telegram_id), primary_key=True)
    request = Column(String)
    response = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    user = relationship(User)