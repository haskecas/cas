from aiogram.types import *
from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, Text, StateFilter
from aiogram.fsm.state import StatesGroup, State
import aiosqlite
from filters import AdminFilter
import sys
sys.path.append('..')
from databaseclass import BotDb, token

bot = Bot(token=token)
router = Router()

class Sql(StatesGroup):
    sql = State()

@router.callback_query(Text(text="sql"), AdminFilter())
async def getsql(call: CallbackQuery, state: FSMContext):
    await state.set_state(Sql.sql)
    await bot.send_message(call.message.chat.id, "Запрос\n/cancel - отмена")

@router.message(Sql.sql, AdminFilter())
async def sql(message: Message, state: FSMContext):
    try:
        result = await BotDb.sql_execute(message.text)
        await bot.send_message(message.chat.id, f"Запрос выполнен успешно\n\n{await result}")
    except Exception as e:
        await bot.send_message(message.chat.id, f"Не удалось выполнить запрос {message.text}\nПричина: {type(e).__name__} {e}")
    await state.clear()