import aiogram.exceptions
from aiogram.types import *
from aiogram.utils.keyboard import *
from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, Text, StateFilter
from aiogram.fsm.state import StatesGroup, State
import re
import aiosqlite
from filters import AdminFilter
import aiosqlite
import sys
sys.path.append('..')
from databaseclass import UserDb, token
import time

bot = Bot(token=token)
router = Router()

class Sending(StatesGroup):
    message = State()

@router.callback_query(Text(text="sendtoall"), AdminFilter())
async def getrasstext(call: CallbackQuery, state: FSMContext):
    await state.set_state(Sending.message)
    await bot.send_message(call.message.chat.id, "введите текст (HTML формат)\n<pre>{Текст|url.com}</pre> - inline-кнопка\n/cancel - отмена", parse_mode='HTML')

@router.message(Sending.message, AdminFilter())
async def sendtoall(message: Message, state: FSMContext):
    await state.clear()
    text = message.text
    btns = re.findall(r"{(.+)\|(.+)}", message.text)
    text = re.sub(r"{(.+)\|(.+)}", "", message.text)
    print(btns)
    # for i in btns:
    #     kb.add(InlineKeyboardButton(text=i[0], url=i[1]))
    buttons =[[InlineKeyboardButton(text=i[0], url=i[1]) for i in btns]]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    try:
        await bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)
        await bot.send_message(message.chat.id, f'Рассылка начата')
    except Exception as e:
        await bot.send_message(message.chat.id, f'Не удалось начать рассылку\n{e}')
        return
    async with aiosqlite.connect("users.db") as db:
        succ = 0
        unsucc = 0
        users = await UserDb.get_users()
        unactive_users = []
        start_time = time.time()
        for i in users:
            try:
                await bot.send_message(i, text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)
                succ+=1
            except aiogram.exceptions.TelegramForbiddenError as e:
                unsucc+=1
                unactive_users.append(i)
                print(type(e).__name__, e)
            except Exception as e:
                print(type(e).__name__, e)
                unsucc+=1
                #await bot.send_message(message.chat.id, f"Не удалось прислать сообщение пользователю {i[0]}\nПричина: {e}")
        print(unactive_users)
        await bot.send_message(message.chat.id, f'Рассылка завершена\nУдачных - {succ}\nНеудачных - {unsucc}\n\nВремя рассылки: <i>{round(time.time() - start_time, 2)} сек</i>', parse_mode="HTML")