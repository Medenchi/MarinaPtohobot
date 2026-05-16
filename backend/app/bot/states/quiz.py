from aiogram.fsm.state import State, StatesGroup


class OutfitQuiz(StatesGroup):
    colors = State()
    style = State()
    season = State()
    occasion = State()
    body_type = State()
    budget = State()
    shoot_type = State()
