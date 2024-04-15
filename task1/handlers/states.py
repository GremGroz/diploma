from aiogram.fsm.state import StatesGroup, State

class Task1States(StatesGroup):
    register_for_task = State()
    answer = State()

class AdminStates(StatesGroup):
    end_register = State()
    test = State()