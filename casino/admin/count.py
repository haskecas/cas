from aiogram import Router, Bot
import aiosqlite
from aiogram.filters import Text
from aiogram.types import *
from filters import AdminFilter
import sys
sys.path.append('..')
from databaseclass import UserDb, token

bot = Bot(token=token)
router = Router()

@router.callback_query(Text(text="count"), AdminFilter())
async def count(call: CallbackQuery):
    count_result, result_str = await UserDb.statistic()
    await bot.send_message(call.message.chat.id, f"Кол-во юзеров: {count_result}\nЯзыки:\n{result_str}")