from aiogram.types import *
from aiogram import Dispatcher, Bot
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
import aiosqlite
from aiogram.utils.deep_linking import get_start_link, decode_payload
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters import StateFilter
from aiogram.utils.callback_data import CallbackData
from typing import Union, Dict, Any
import re
import logging
logging.basicConfig(level=logging.ERROR)

bot = Bot(token="5362234675:AAHmNWHS2xAiSMkph6bV0sv-0YEUc4CFfUA")
dp = Dispatcher(bot, storage=MemoryStorage())

adminlist = [1377307544]

class Admin(StatesGroup):
    sendtoall = State()
    sql = State()

@dp.message_handler(commands=['start'])
async def greets(message: Message):
    await bot.send_message(message.chat.id, 'Тут ваш бот')
    try:
        async with aiosqlite.connect("users.db", timeout=100) as db:
            await db.execute(f'insert into users ("id", "name", "surname", "lang", "date") values ("{message.chat.id}", "{message.from_user.first_name}", "{message.from_user.last_name}", "{message.from_user.language_code}", "{message.date}")')
            await db.commit()
    except Exception as e:
        print(e)

@dp.message_handler(commands=['cancel', 'admin'], state='*')
async def adminka(message: Message, state: FSMContext):
    await state.finish()
    if message.text == '/cancel':
        await message.answer("Отменено")
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(text='Рассылка📃', callback_data='sendtoall'),
        InlineKeyboardButton(text="Кол-во пользователей🙋🏻‍♂️", callback_data='count'),
        InlineKeyboardButton(text="sql-запрос👨🏻‍💻", callback_data='sql'),
        InlineKeyboardButton(text="Скинуть базу .db файлом✉", callback_data='file'),
        InlineKeyboardButton(text="Обязательная подписка✔", callback_data="OP"),
        InlineKeyboardButton(text="Рефералка для рекламы🔗", callback_data="ref")
    )
    await bot.send_message(message.chat.id, "Что далее", reply_markup=kb)


@dp.callback_query_handler(text="sendtoall")
async def getrasstext(call: CallbackQuery):
    await Admin.sendtoall.set()
    await bot.send_message(call.message.chat.id, "введите текст (HTML формат)\n<pre>{Текст|url.com}</pre> - inline-кнопка\n/cancel - отмена", parse_mode='HTML')

@dp.message_handler(state=Admin.sendtoall)
async def sendtoall(message: Message, state: FSMContext):
    await state.finish()
    text = message.text
    kb = InlineKeyboardMarkup(row_width=1)
    btns = re.findall(r"{(.+)\|(.+)}", message.text)
    text = re.sub(r"{(.+)\|(.+)}", "", message.text)
    print(btns)
    try:
        await bot.send_message(message.chat.id, text, parse_mode="HTML")
    except Exception as e:
        await bot.send_message(message.chat.id, f'Не удалось начать рассылку\n{e}')
        return
    for i in btns:
        kb.add(InlineKeyboardButton(text=i[0], url=i[1]))
    async with aiosqlite.connect("users.db") as db:

        async with db.execute("SELECT id FROM users") as cursor:
            async for i in cursor:
                try:
                    await bot.send_message(i[0], text, parse_mode="HTML", reply_markup=kb)
                except Exception as e:
                    await bot.send_message(message.chat.id, f"Не удалось прислать сообщение пользователю {i[0]}\nПричина: {e}")


class refka(StatesGroup):
    ref = State()
    editref = State()
    addref = State()

@dp.callback_query_handler(text="ref")
@dp.callback_query_handler(text='backtoreflist', state=refka.editref)
async def ref(call: CallbackQuery):
    await refka.ref.set()
    kb = InlineKeyboardMarkup(row_width=1)
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT * FROM ref") as cursor:
            async for name in cursor:
                #print(name)
                kb.add(InlineKeyboardButton(text=name[0], callback_data=name[0]))
            kb.add(InlineKeyboardButton(text="Добавить рефа✏", callback_data='addref'))
    if call.data == 'backtoreflist':
        await bot.edit_message_text("Рефы", call.message.chat.id, call.message.message_id, reply_markup=kb)
    else:
        await bot.send_message(call.message.chat.id, "Рефы", reply_markup=kb)

edit_ref = CallbackData('refedit', 'action', 'refname')

@dp.callback_query_handler(text='addref', state='*')
async def refadd(call: CallbackQuery):
    await refka.addref.set()
    await bot.send_message(call.message.chat.id, 'Введите имя рефа\n/cancel - отмена')

@dp.message_handler(state=refka.addref)
async def refwrite(message: Message, state: FSMContext):
    try:
        async with aiosqlite.connect("users.db") as db:
            await db.execute(f"insert into ref('name') values ('{message.text}')")
            await db.commit()
        link = await get_start_link(message.text)
        await bot.send_message(message.chat.id, f'Реферал {message.text} добавлен\nЕго ссылка:\n{link}')
    except Exception as e:
        await message.answer(e)
        await adminka(message, state)

@dp.callback_query_handler(state=refka.ref)
async def refinfo(call: CallbackQuery):
    await refka.editref.set()
    async with aiosqlite.connect("users.db") as db:
        async with db.execute(f"SELECT * FROM ref where name = '{call.data}'") as cursor:
            async for name, amount in cursor:
                kb = InlineKeyboardMarkup(row_width=3)
                kb.add(
                    InlineKeyboardButton(text="❌", callback_data=edit_ref.new(action="delete", refname=name)),
                    InlineKeyboardButton(text="🔄", callback_data=edit_ref.new(action="reset", refname=name)),
                    InlineKeyboardButton(text="🔙", callback_data='backtoreflist')
                )
                link = await get_start_link(name)
                await bot.edit_message_text(f"Реферал {name}\nКол-во приглашенных {amount}\nСсылка:\n{link}", call.message.chat.id, call.message.message_id, reply_markup=kb)



@dp.callback_query_handler(edit_ref.filter(), state=refka.editref)
async def refedit(call: CallbackQuery, callback_data: dict) -> None:
    if callback_data['action'] == 'delete':
        async with aiosqlite.connect("users.db") as db:
            await db.execute(f"delete from ref where name = '{callback_data['refname']}'")
            await db.commit()
        await bot.edit_message_text(f"Реферал {callback_data['refname']} удален", call.message.chat.id, call.message.message_id)
    elif callback_data['action'] == 'reset':
        async with aiosqlite.connect("users.db") as db:
            await db.execute(f"update ref set amount = 0 where name = '{callback_data['refname']}")
            await db.commit()
        await bot.send_message(call.message.chat.id, f"Кол-во юзеров которое пригласил реферал {callback_data['refname']} сброшено")



@dp.callback_query_handler(text="count")
async def count(call: CallbackQuery):
    async with aiosqlite.connect("users.db") as db:
        async with db.execute('SELECT count(id) FROM users') as cursor:
            async for i in cursor:
                await bot.send_message(call.message.chat.id, f"Кол-во юзеров: {i[0]}")

@dp.callback_query_handler(text="sql")
async def getsql(call: CallbackQuery):
    await bot.send_message(call.message.chat.id, "Запрос")
    await Admin.sql.set()

@dp.message_handler(state=Admin.sql)
async def sql(message: Message, state: FSMContext):
    try:
        async with aiosqlite.connect("users.db") as db:
            cursor = await db.execute(message.text)
            await db.commit()
            await bot.send_message(message.chat.id, f"Запрос выполнен успешно\n\n{await cursor.fetchall()}")
    except Exception as e:
        await bot.send_message(message.chat.id, f"Не удалось выполнить запрос {message.text}\nПричина: {e}")
    await state.finish()

@dp.callback_query_handler(text="file")
async def count(call: CallbackQuery):
    await bot.send_document(call.message.chat.id, InputFile("users.db"))

class op(StatesGroup):
    start = State()
    link = State()
    id = State()

del_chl = CallbackData('delchnl', 'idc')


@dp.callback_query_handler(text="OP")
async def OP(call: CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1)
    async with aiosqlite.connect("users.db") as db:
        async with db.execute('SELECT link, id FROM op') as cursor:
            async for i, j in cursor:
                kb.row(InlineKeyboardButton(text=i, url=i), InlineKeyboardButton(text="❌", callback_data=del_chl.new(idc=j)))
            kb.add(InlineKeyboardButton(text="Добавить канал✍🏻", callback_data="add"))
    await bot.send_message(call.message.chat.id, "Каналы:", reply_markup=kb)


@dp.callback_query_handler(state=op.start, text="add")
async def add(call: CallbackQuery, state: FSMContext):
    await bot.send_message(call.message.chat.id, "Введите ссылку канала\n/cancel - отмена")
    await op.link.set()

@dp.message_handler(content_types=['text'], state=op.link)
async def link(message: Message, state: FSMContext):
    await state.update_data(link=message.text)
    await bot.send_message(message.chat.id, "ID канала\n/cancel - отмена")
    await op.next()

@dp.message_handler(content_types=['text'], state=op.id)
async def chnlid(message: Message, state: FSMContext):
    await state.update_data(id=message.text)
    data = await state.get_data()
    #await bot.send_message(message.chat.id, f"{data['link']}\n{data['id']}")
    await state.finish()
    try:
        async with aiosqlite.connect("users.db") as db:
            cursor = await db.execute(f'insert into op("link", "id") values("{data["link"]}", "{data["id"]}")')
            await db.commit()
            await bot.send_message(message.chat.id, f'Канал {data["link"]} добавлен в оп')
    except Exception as e:
        await bot.send_message(message.chat.id, f"Не удалось добавить канал\nПричина: {e}")

@dp.callback_query_handler(del_chl.filter())
async def remove(call: CallbackQuery, callback_data: dict, state: FSMContext) -> None:
    print(callback_data['idc'])
    try:
        async with aiosqlite.connect("users.db") as db:
            cursor = await db.execute(f"delete from op where id = {callback_data['idc']}")
            await db.commit()
            await bot.send_message(call.message.chat.id, f"Канал удален")
    except Exception as e:
        await bot.send_message(call.message.chat.id, f"Не удалось удалить канал\nПричина: {e}")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp)
