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
from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.models.update import Update
from keyboards import *
bot = Bot(token=token, parse_mode="HTML")

expiration = 20
router = Router()
MIN_SUM_DEP = 2
@router.callback_query(Text(text="deposit"))
async def deposit(call: CallbackQuery, state: FSMContext):
    kb = [
        [InlineKeyboardButton(text="Cryptobot 3%", callback_data="cryptobot")],
        [InlineKeyboardButton(text="Назад", callback_data="main")]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=kb,
    )
    await call.message.edit_text("Выберите способ пополнения", reply_markup=keyboard)

@router.callback_query(Text(text="cryptobot"))
async def cryptobot_deposit(call: CallbackQuery, state: FSMContext):
    await state.set_state(Deposit.cryptobot)
    await call.message.edit_text("Введите сумму пополнения", reply_markup=cancel_keyboard)

@router.message(Deposit.cryptobot)
async def cryptobot(message: Message, state: FSMContext):
    if float_to_int_str(message.text).isdigit():
        if (float(float_to_int_str(message.text)) >= MIN_SUM_DEP):
            summ = round(float(message.text), 2)
            invoice = await crypto.create_invoice(asset='USDT', amount=float(message.text)*1.03, expires_in=60 * expiration,
                                                  payload=str(message.text))
            buttons = [
                [InlineKeyboardButton(text="Оплатить↗", url=invoice.pay_url)],
                [InlineKeyboardButton(text="Проверить оплату✅",
                                      callback_data=Check(foo="check", id_=str(invoice.invoice_id)).pack())],
                [InlineKeyboardButton(text="⬅Закрыть", callback_data="main")],
            ]
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer(
                f"Оплата покупки на сумму {float(message.text)*1.03} USDT\nВремя на оплату - {expiration} мин.\nID платежа - {invoice.invoice_id}\nВремя создания платежа - {invoice.created_at.strftime('%y-%m-%d %H-%M')}",
                reply_markup=kb, disable_web_page_preview=True)
        else:
            await message.answer(f"Сумма должна быть больше {MIN_SUM_DEP}")

    else:
        await message.answer("Сумма должна быть целым числом", reply_markup=cancel_keyboard)

@router.callback_query(Check.filter(F.foo == "check"))
async def cryptocheck(call: CallbackQuery, state: FSMContext, callback_data: Check):
    invoice = await crypto.get_invoices(invoice_ids=int(callback_data.id_))
    if invoice.status == 'expired':
        await call.message.answer("Время на оплату вышло, вы не успели оплатить счет, создайте новый")
    elif invoice.status == 'active':
        await call.message.answer("Вы не оплатили счет❗")
    elif invoice.status == 'paid':
        await call.message.delete()
        await UserDb.update_balance(call.message.chat.id, round(float(invoice.payload), 2))
        await UserDb.new_deposit(call.message.chat.id, float(invoice.payload), "cryptobot")
        await call.message.answer("<b>✅ Оплата прошла успешео. ✅</b>\n\n<b><i>Вы успешно оплатили, свяжитесь по кнопке ниже с Администратором магазина.</i></b>", parse_mode="HTML", reply_markup=cancel_keyboard)
