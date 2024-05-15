from aiogram.fsm.state import StatesGroup, State

class UserStates(StatesGroup):
    lastname = State()
    firstname = State()
    group= State()
    selecting_lab = State()
    passing_lab = State()
    
class DeveloperStates(StatesGroup):
    lab_download = State()
    lab_test = State()
    
class AdminStates(StatesGroup):
    pass