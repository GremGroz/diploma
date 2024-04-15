from aiogram.fsm.state import StatesGroup, State

class UserStates(StatesGroup):
    lastname = State()
    firstname = State()
    group= State()