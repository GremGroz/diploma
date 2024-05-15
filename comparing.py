from typing import Iterable

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButtonPollType,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database.crud import get_developer_user, get_tested_labs, get_passed_labs, get_dev_title
import os

class ButtonTextUser:
    SEND_LAB = "Отправить лабораторную работу"
    TEST_LAB = "Отправить тестовый файл"
    LABS = "Список лабораторных работ"  # Исправлена опечатка: "Спискок" на "Список"


class ButtonTextAdmin:
    ADD_LAB = "Добавить лабораторную работу"
    ADD_THEME = "Добавить тему"
    DELETE_LAB = "Удалить лабораторную работу"
    DELETE_THEME = "Удалить тему"

    
async def get_dynamic_user_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    
    labs = await get_tested_labs()
    title_dev_lab = await get_dev_title(user_id)
    if title_dev_lab:
        labs.remove(title_dev_lab)
    passed_labs = await get_passed_labs(user_id)
    if passed_labs:
        result_kb_button = [lab + " ✅" if lab in passed_labs else lab for lab in labs]
    else:
        result_kb_button = labs
    for lab in result_kb_button:
        kb.add(KeyboardButton(text=lab))
    
    # Добавляем базовые кнопки
    kb.add(KeyboardButton(text="Вернуться"))
    
    # Возвращаем разметку с шириной 1, чтобы кнопки выводились в столбик
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=False, row_width=1)


async def get_user_keyboard(user_id) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    if await get_developer_user(user_id):
        kb.button(text=ButtonTextUser.SEND_LAB)
        kb.add(KeyboardButton(text=ButtonTextUser.TEST_LAB))
        kb.add(KeyboardButton(text=ButtonTextUser.LABS))
    else:  # Добавляем условие, если не developer_user, чтобы LIST_LAB не повторялся
        kb.add(KeyboardButton(text=ButtonTextUser.LABS))
    
    # Возвращаем разметку с шириной 1, чтобы кнопки выводились в столбик
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=False, row_width=1)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text=ButtonTextAdmin.ADD_LAB))
    kb.add(KeyboardButton(text=ButtonTextAdmin.ADD_THEME))
    kb.add(KeyboardButton(text=ButtonTextAdmin.DELETE_LAB))
    kb.add(KeyboardButton(text=ButtonTextAdmin.DELETE_THEME))
    
    # Возвращаем разметку с шириной 1, чтобы кнопки выводились в столбик
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=False, row_width=1)
