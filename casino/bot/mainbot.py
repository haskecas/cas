import asyncio
import sqlite3
from aiogram.types.dice import DiceEmoji
from aiogram.utils.keyboard import *
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, Text, CommandObject
from aiogram import Bot
import sys
from typing import Union
from fsm_classes import *
sys.path.append('..')
from databaseclass import *
from keyboards import *
bot = Bot(token=token, parse_mode="HTML")
router = Router()
MIN_SUM = 1

@router.callback_query(Text(text='main'))
@router.message(Command(commands=['start']))
async def greets(message: Message, state: FSMContext, command: Union[CommandObject, None] = None):
    user = UserDb(message)
    kb = [
        [InlineKeyboardButton(text="Играть", callback_data="play")],
        [
            InlineKeyboardButton(text="Пополнить", callback_data="deposit"),
            InlineKeyboardButton(text="Вывести", callback_data="withdraw")
        ],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Канал", url="https://t.me/TestnetRoll")]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=kb,
    )
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(f'Привет', reply_markup=keyboard)
        await state.clear()
    else:
        await bot.send_message(message.chat.id, f'Привет', reply_markup=keyboard)
    await user.add_user(command.args if command is not None else None)
    try:
        if command.args:
            if (command.args.isdigit()):
                await UserDb.increase(int(command.args))
                await bot.send_message(command.args, "У вас новый реферал")
            else:
                await RefDb.increase(command.args)
    except sqlite3.IntegrityError as e:
        pass
    except Exception as e:
        print(e)

@router.message(Bet.summ_guess_number)
async def game(message: Message, state: FSMContext):
    data = await UserDb.get_profile(message.chat.id)
    bt = 0
    try:
        bt = float(message.text.replace(",", "."))
        if data["balance"]<bt:
            await message.answer(f"Недостаточно средств", reply_markup=cancel_keyboard)
            return
        if (bt < MIN_SUM):
            await message.answer(f"Минимальная сумма - {MIN_SUM}", reply_markup=cancel_keyboard)
            return
        await state.update_data(bet=float(message.text))
        await state.set_state(Bet.guessing_number_guess_number)
        builder = InlineKeyboardBuilder()
        for i in range(1, 7):
            builder.add(InlineKeyboardButton(text=str(i), callback_data=GuessedNumber(game=GUESS_NUMBER, number=int(i)).pack()))
        builder.adjust(3)
        builder.row(cancel_kb[0][0])
        await message.answer(
            "Выберите число:",
            reply_markup=builder.as_markup(resize_keyboard=True),
        )
    except ValueError as e:
        print(e)
        await message.answer("Сумма должна быть целым числом", reply_markup=cancel_keyboard)

@router.message(Bet.summ_two_dices)
async def game(message: Message, state: FSMContext):
    data = await UserDb.get_profile(message.chat.id)
    bt = 0
    kb = [
        [InlineKeyboardButton(text="Играть еще раз", callback_data=TWO_DICES)],
        [InlineKeyboardButton(text="Назад", callback_data="main")],
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=kb,
    )
    try:
        bt = float(message.text.replace(",", "."))
        if data["balance"]<bt:
            await message.answer(f"Недостаточно средств", reply_markup=cancel_keyboard)
            return
        if (bt < MIN_SUM):
            await message.answer(f"Минимальная сумма - {MIN_SUM}", reply_markup=cancel_keyboard)
            return
        await state.update_data(bet=bt)
        if channel_to_send is not None: await bot.send_message(channel_to_send, f"Новая ставка\nСумма: {bt}")
        dice_1 = await message.answer_dice(emoji=DiceEmoji.DICE)
        if channel_to_send is not None: await dice_1.forward(channel_to_send)
        await asyncio.sleep(2)
        dice_2 = await message.answer_dice(emoji=DiceEmoji.DICE)
        if channel_to_send is not None: await dice_2.forward(channel_to_send)
        await asyncio.sleep(2)
        if (dice_1.dice.value < dice_2.dice.value):
            await message.answer("Вы выиграли!", reply_markup=keyboard)
            if channel_to_send is not None: await bot.send_message(channel_to_send, "Игрок выиграл")
            await UserDb.update_balance(message.chat.id, bt*0.5)
            await UserDb.new_bet(message.chat.id, TWO_DICES, bt, dice_1.dice.value < dice_2.dice.value, dice_1.dice.value, dice_2.dice.value)
        else:
            await message.answer("Вы проиграли!", reply_markup=keyboard)
            if channel_to_send is not None: await bot.send_message(channel_to_send, "Бот выиграл")
            await UserDb.update_balance(message.chat.id, -bt, True)
            await UserDb.new_bet(message.chat.id, TWO_DICES, bt, dice_1.dice.value < dice_2.dice.value,
                                 dice_1.dice.value, dice_2.dice.value)
    except ValueError as e:
            print(e)
            await message.answer("Сумма должна быть целым числом", reply_markup=cancel_keyboard)