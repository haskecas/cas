from aiogram.types import *

cancel_kb = [
    [InlineKeyboardButton(text="Назад", callback_data="main")],
]
cancel_keyboard = InlineKeyboardMarkup(
    inline_keyboard=cancel_kb,
)

withdraw_kb = [
    [InlineKeyboardButton(text="Вывести", callback_data="withdraw_cryptobot")],
    [cancel_kb[0][0]]
]
withdraw_keyboard = InlineKeyboardMarkup(
    inline_keyboard=withdraw_kb,
)