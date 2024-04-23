from aiogram import Router, Bot
from aiogram.types import *
from aiogram.filters import Text
from filters import AdminFilter
import sys
sys.path.append('..')
from databaseclass import UserDb, token

router = Router()
bot = Bot(token=token)

@router.callback_query(Text(text="file"), AdminFilter())
async def count(call: CallbackQuery):
    await bot.send_document(call.message.chat.id, FSInputFile("users.db"))