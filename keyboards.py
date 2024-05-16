from typing import Iterable, List

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from database.crud import get_developer_user, get_tested_labs, get_passed_labs, get_dev_title

class ButtonTextUser:
    SEND_LAB = "Отправить лабораторную работу"
    TEST_LAB = "Отправить тестовый файл"
    LABS = "Список лабораторных работ"
    GRADES = "Мои оценки"  


class ButtonTextAdmin:
    ADD_LAB = "Добавить лабораторную работу"
    ADD_THEME = "Добавить тему"
    DELETE_LAB = "Удалить лабораторную работу"
    DELETE_THEME = "Удалить тему"


def create_reply_keyboard(buttons: List[str], resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
    """Helper to create a keyboard with each button on a new line."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn)] for btn in buttons],
        resize_keyboard=resize_keyboard
    )


async def get_dynamic_user_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    labs = await get_tested_labs()
    title_dev_lab = await get_dev_title(user_id)
    if title_dev_lab:
        labs.remove(title_dev_lab)
    passed_labs = await get_passed_labs(user_id)
    if passed_labs:
        result_kb_button = [lab + " ✅" if lab in passed_labs else lab for lab in labs]
    else:
        result_kb_button = labs
    
    result_kb_button.append("Вернуться")
    
    return create_reply_keyboard(result_kb_button)


async def get_user_keyboard(user_id) -> ReplyKeyboardMarkup:
    buttons = []
    if await get_developer_user(user_id):
        buttons.append(ButtonTextUser.SEND_LAB)
        buttons.append(ButtonTextUser.TEST_LAB)
    buttons.append(ButtonTextUser.LABS)
    buttons.append(ButtonTextUser.GRADES)
    return create_reply_keyboard(buttons)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        ButtonTextAdmin.ADD_LAB,
        ButtonTextAdmin.ADD_THEME,
        ButtonTextAdmin.DELETE_LAB,
        ButtonTextAdmin.DELETE_THEME
    ]
    return create_reply_keyboard(buttons)
