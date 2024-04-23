from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.callback_data import CallbackData
GUESS_NUMBER = "guess_number"
TWO_DICES = "two_dices"
class Bet(StatesGroup):
    summ_guess_number = State()
    summ_two_dices = State()
    guessing_number_guess_number = State()

class Deposit(StatesGroup):
    cryptobot = State()

class GuessedNumber(CallbackData, prefix="gm"):
    game: str
    number: int

class Check(CallbackData, prefix="check"):
    foo: str
    id_: str