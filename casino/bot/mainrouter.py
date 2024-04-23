from aiogram.types import *
from aiogram.types.dice import DiceEmoji
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import *
from aiogram import Router
from magic_filter import F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Text
from aiogram import Bot
from databaseclass import *
from fsm_classes import *
from keyboards import *
import asyncio
bot = Bot(token=token, parse_mode="HTML")
router = Router()


@router.callback_query(Text(text='profile'))
async def greets(call: CallbackQuery):
    data = await UserDb.get_profile(call.message.chat.id)
    print(data)
    kb = [
        [InlineKeyboardButton(text="Реферальная система", callback_data="ref_system")],
        [InlineKeyboardButton(text="Назад", callback_data="main")],
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=kb,
    )
    await call.message.edit_text(f"🆔: {call.message.chat.id}\nБаланс: {data['balance']}\nСтавок: {len(json.loads(data['history'])['bets'])}", reply_markup=keyboard)

@router.callback_query(Text(text='ref_system'))
async def ref(call: CallbackQuery):
    await call.message.edit_text(f"20% проиграша идет вам на баланс\n\n{await create_start_link(bot, str(call.message.chat.id))}", reply_markup=cancel_keyboard)
@router.callback_query(Text(text='play'))
async def greets(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="Угадать число", callback_data=GUESS_NUMBER)],
        [InlineKeyboardButton(text="Два броска", callback_data=TWO_DICES)],
        [InlineKeyboardButton(text="Назад", callback_data="main")]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=kb,
    )
    await call.message.edit_text(f"Выберите игру", reply_markup=keyboard)

@router.callback_query(Text(text=GUESS_NUMBER))
async def greets(call: CallbackQuery, state: FSMContext):
    cancel_kb = [
        [InlineKeyboardButton(text="Назад", callback_data="main")],
    ]
    cancel_keyboard = InlineKeyboardMarkup(
        inline_keyboard=cancel_kb,
    )
    await state.set_state(Bet.summ_guess_number)
    await call.message.edit_text(f"Введите ставку", reply_markup=cancel_keyboard)

@router.callback_query(Text(text=TWO_DICES))
async def greets(call: CallbackQuery, state: FSMContext):
    cancel_kb = [
        [InlineKeyboardButton(text="Назад", callback_data="main")],
    ]
    cancel_keyboard = InlineKeyboardMarkup(
        inline_keyboard=cancel_kb,
    )
    await state.set_state(Bet.summ_two_dices)
    await call.message.edit_text(f"Введите ставку", reply_markup=cancel_keyboard)

@router.callback_query(GuessedNumber.filter(F.game == GUESS_NUMBER), Bet.guessing_number_guess_number)
async def calculate_guess_number(call: CallbackQuery, callback_data: GuessedNumber, state: FSMContext):
    if channel_to_send is not None: await bot.send_message(channel_to_send, f"Пользователь выбрал {callback_data.number}")
    await call.message.delete()
    dice_sent = await bot.send_dice(chat_id=call.message.chat.id, emoji=DiceEmoji.DICE)
    if channel_to_send is not None: await dice_sent.forward(channel_to_send)
    await asyncio.sleep(1.5)
    data = await state.get_data()
    if dice_sent.dice.value == callback_data.number:
        res = "<b><i>✅Вы угадали</i></b>"
        await UserDb.update_balance(call.message.chat.id, data["bet"]*0.5)
        if channel_to_send is not None: await bot.send_message(channel_to_send, "Игрок выиграл")
    else:
        res = "<b><i>❌Вы не угадали</i></b>"
        await UserDb.update_balance(call.message.chat.id, -data["bet"], True)
        if channel_to_send is not None: await bot.send_message(channel_to_send, "Бот выиграл")
    kb = [
        [InlineKeyboardButton(text="Играть еще раз", callback_data=callback_data.game)],
        [InlineKeyboardButton(text="Назад", callback_data="main")],
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=kb,
    )
    await call.message.answer(f"Вы предсказали {callback_data.number}\n\nВыпало: {dice_sent.dice.value}\n\n{res}", parse_mode="HTML", reply_markup=keyboard)
    await UserDb.new_bet(call.message.chat.id, callback_data.game, data["bet"], dice_sent.dice.value == callback_data.number, callback_data.number, dice_sent.dice.value)
    await state.clear()
