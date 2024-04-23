from aiogram.types import *
from aiogram.types.dice import DiceEmoji
from aiogram.utils.keyboard import *
from aiogram import Router
from magic_filter import F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Text
from aiogram import Bot
from databaseclass import *
from fsm_classes import *
from keyboards import *
from uuid import uuid4
from aiocryptopay.exceptions import CodeErrorFactory
router = Router()

@router.callback_query(Text(text='withdraw'))
async def withdraw(call: CallbackQuery):
    await call.message.edit_text("Вывод средств на CryptoBot", reply_markup=withdraw_keyboard)

@router.callback_query(Text(text='withdraw_cryptobot'))
async def withdraw(call: CallbackQuery):
    can_withdraw = await UserDb.can_withdraw(call.message.chat.id)
    data = await UserDb.get_profile(call.message.chat.id)
    if data["balance"] < 1:
        await call.message.edit_text("⚠<b><i>Вывод начинаеться от 1</i></b>", parse_mode="HTML", reply_markup=cancel_keyboard)
        return
    if can_withdraw:
        try:
            transfer = await crypto.transfer(call.message.chat.id, "USDT", data["balance"], uuid4().__str__())
            await call.message.edit_text(f"Успешно выведено {round(transfer.amount, 2)} USDT", parse_mode="HTML", reply_markup=cancel_keyboard)
            await UserDb.update_balance(call.message.chat.id, -data["balance"])
        except CodeErrorFactory as e:
            print(e)
            if e.name == 'USER_NOT_FOUND':
                await call.message.edit_text("⚠<b><i>Вы еще не использовали CryptoBot на этом аккаунте</i></b>",parse_mode="HTML", reply_markup=cancel_keyboard)
            else:
                await call.message.edit_text("⚠<b><i>На данный момент по техническим причинам возможность делать вывод недоступна</i></b>", parse_mode="HTML", reply_markup=cancel_keyboard)
    else:
        await call.message.edit_text("⚠<b><i>На данный момент ваша возможность делать вывод заблокирована</i></b>", parse_mode="HTML", reply_markup=cancel_keyboard)