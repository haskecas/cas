import asyncio
from aiogram import Router
from aiogram import Bot, Dispatcher
from admin import mainadm, mailing, count, sql, senddb, op, ref
from bot import mainbot, mainrouter, deposit, withdraw
from aiogram.fsm.storage.memory import MemoryStorage
from databaseclass import *
from filters import ThrottlingMiddleware
from background import keep_alive


async def main():
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    await ChannelDb.cash_link_id()
    keep_alive()
    routers = [
        mainadm.router,
        mailing.router,
        count.router,
        sql.router,
        senddb.router,
        op.router,
        ref.router,
        mainbot.router,
        mainrouter.router,
        deposit.router,
        withdraw.router
               ]
    for i in routers:
        dp.include_router(i)
    #await bot.delete_webhook(drop_pending_updates=True)
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
