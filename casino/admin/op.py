import aiogram.exceptions
from aiogram.types import *
from aiogram.utils.keyboard import *
from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import Text
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State
from filters import AdminFilter
import sys
sys.path.append('..')
from databaseclass import ChannelDb, token

router = Router()
bot = Bot(token=token)

class Sending(StatesGroup):
    link = State()
    id_ = State()

class del_chn(CallbackData, prefix='delete_kb'):
    id_: int



@router.callback_query(Text(text="OP"), AdminFilter())
async def OP(call: CallbackQuery):
    result = await ChannelDb.get_link_id()
    builder = InlineKeyboardBuilder()
    for i, j in result:
        builder.button(text=i, url=i)
        builder.button(text="❌", callback_data=del_chn(id_=j))
    builder.button(text="Добавить канал✍🏻", callback_data='add')
    builder.adjust(2, 2)
    #buttons = [[InlineKeyboardButton(text="❌", callback_data=del_(id_=1).pack())]]
    #kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    #kb.add(InlineKeyboardButton(text="Добавить канал✍🏻", callback_data="add"))]
    await bot.send_message(call.message.chat.id, "Каналы:", reply_markup=builder.as_markup())

@router.callback_query(del_chn.filter(), AdminFilter())
async def delete(call: CallbackQuery, callback_data: del_chn):
    print(callback_data.id_)
    try:
        await ChannelDb.delete_channel(callback_data.id_)
        await ChannelDb.cash_link_id()
        await bot.send_message(call.message.chat.id, f"Канал удален")
    except Exception as e:
        await bot.send_message(call.message.chat.id, f"Не удалось удалить канал\nПричина: {e}")

@router.callback_query(Text(text='add'), AdminFilter())
async def add(call: CallbackQuery, state: FSMContext):
    await state.set_state(Sending.link)
    await bot.send_message(call.message.chat.id, 'Введите ссылку канала')

@router.message(Sending.link, AdminFilter())
async def link(message: Message, state: FSMContext):
    await state.update_data(link=message.text)
    await state.set_state(Sending.id_)
    await bot.send_message(message.chat.id, 'Введите id канала')

@router.message(Sending.id_, AdminFilter())
async def link(message: Message, state: FSMContext):
    await state.update_data(id_=message.text)
    user_data = await state.get_data()
    await state.clear()
    print(user_data['link'], user_data['id_'])
    try:
        await ChannelDb.add_channel(int(user_data['id_']), user_data['link'])
        await ChannelDb.cash_link_id()
        await bot.send_message(message.chat.id, f'Канал {user_data["link"]} добавлен в оп')
        try:
            await bot.get_chat(user_data['id_'])
        except aiogram.exceptions.TelegramBadRequest:
            await bot.send_message(message.chat.id, f'❗Обратите внимание, бота на данный момент нет в канале')
        except Exception as e:
            pass

    except Exception as e:
        await bot.send_message(message.chat.id, f"Не удалось добавить канал {user_data['link']}\nПричина: {type(e).__name__}: {e}")
