from aiogram.types import *
from aiogram.utils.keyboard import *
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import Bot
from filters import AdminFilter, token

bot = Bot(token=token)

router = Router()

@router.message(Command(commands=['admin', 'cancel']), AdminFilter())
async def adminka(message: Message, state: FSMContext):
    await state.clear()
    if message.text == '/cancel':
        await message.answer("Отменено")
    buttons = [
        [InlineKeyboardButton(text='Рассылка✉', callback_data='sendtoall')],
        [InlineKeyboardButton(text="Статистика📃", callback_data='count')],
        [InlineKeyboardButton(text="sql-запрос💉", callback_data='sql')],
        #[InlineKeyboardButton(text="Скинуть базу .db файлом", callback_data='file')],
        [InlineKeyboardButton(text="Обязательная подписка✔", callback_data="OP")],
        [InlineKeyboardButton(text="Рефералка для рекламы🔗", callback_data="ref")]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.send_message(message.chat.id, "Что далее", reply_markup=kb)
