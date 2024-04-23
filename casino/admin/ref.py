from aiogram.types import *
from aiogram.utils.keyboard import *
from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, Text, StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State
import aiosqlite
from aiogram.utils.deep_linking import create_start_link
from enum import Enum
from filters import AdminFilter
import sys
sys.path.append('..')
from databaseclass import RefDb, token

router = Router()
bot = Bot(token=token)

class refchoose(CallbackData, prefix='refchoose'):
    nick: str

class Action(str, Enum):
    reset = 'reset'
    delete = 'delete'

class refedit(CallbackData, prefix='refedit'):
    action: Action
    nick: str

class Addref(StatesGroup):
    refname = State()

@router.callback_query(Text(text=["ref", 'backtoreflist']), AdminFilter())
async def ref(call: CallbackQuery):

    builder = InlineKeyboardBuilder()
    for name in await RefDb.get_refs():
        #print(name)
        builder.button(text=name, callback_data=refchoose(nick=name))
    builder.button(text="Добавить рефа✏", callback_data='addref')
    builder.adjust(1)
    if call.data == 'backtoreflist':
        await bot.edit_message_text("Рефы", call.message.chat.id, call.message.message_id, reply_markup=builder.as_markup())
    else:
        await bot.send_message(call.message.chat.id, "Рефы", reply_markup=builder.as_markup())

@router.callback_query(Text(text='addref'))
async def addref(call: CallbackQuery, state: FSMContext):
    await bot.send_message(call.message.chat.id, 'Введите имя рефа')
    await state.set_state(Addref.refname)

@router.message(Addref.refname)
async def addreffoo(message: Message, state: FSMContext):
    await state.clear()
    try:
        await RefDb.add_ref(message.text)
        await bot.send_message(message.chat.id, f'Реф {message.text} добавлен')
    except Exception as e:
        await bot.send_message(message.chat.id, f'Не удалось добавить рефа\nПричина: {e}')

@router.callback_query(refchoose.filter(), AdminFilter())
async def refeditfoo(call: CallbackQuery, callback_data: refchoose):
    print(callback_data.nick)
    for name, amount in await RefDb.get_ref(callback_data.nick):
        builder = InlineKeyboardBuilder()
        builder.button(text="❌", callback_data=refedit(action=Action.delete, nick=name))
        builder.button(text="🔄", callback_data=refedit(action=Action.reset, nick=name))
        builder.button(text="🔙", callback_data='backtoreflist')

        link = await create_start_link(bot, name)
        await bot.edit_message_text(f"Реферал {name}\nКол-во приглашенных {amount}\nСсылка:\n{link}",
                                    call.message.chat.id, call.message.message_id, reply_markup=builder.as_markup())

@router.callback_query(refedit.filter(F.action == Action.delete), AdminFilter())
async def refdelete(call: CallbackQuery, callback_data: refedit):
    print(callback_data.nick)
    try:
        await RefDb.delete_ref(callback_data.nick)
        await bot.edit_message_text(f"Реферал {callback_data.nick} удален", call.message.chat.id,
                                    call.message.message_id)
    except Exception as e:
        await bot.send_message(call.message.chat.id, f'Не удалось удалить рефа\nПричина: {e}')

@router.callback_query(refedit.filter(F.action == Action.reset), AdminFilter())
async def refreset(call: CallbackQuery, callback_data: refedit):
    print(callback_data.nick)
    try:
        await RefDb.reset_ref(callback_data.nick)
        await bot.send_message(call.message.chat.id,
                               f"Кол-во юзеров которое пригласил реферал {callback_data.nick} сброшено")
    except Exception as e:
        await bot.send_message(call.message.chat.id, f'Не удалось сбросить\nПричина: {e}')
