import aiogram.exceptions
from aiogram.types import *
from aiogram.filters import BaseFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot
import aiosqlite
from databaseclass import ChannelDb, token
from cachetools import TTLCache
from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from typing import Any, Awaitable, Callable, Dict
from cachetools import TTLCache
from typing import Optional
DEFAULT_TTL = 0.5
DEFAULT_KEY = "default"

adminlist = [6218950373, 5488988760, 1274251205]
allowedlist = ['creator', 'owner', 'admin', 'member']

bot = Bot(token=token)

class AdminFilter(BaseFilter):
    async def __call__(self, data):
        if(isinstance(data, Message)):
            if data.chat.id in adminlist:
                return True
        else:
            if data.message.chat.id in adminlist:
                return True
        return False

class SubFilter(BaseFilter):
    async def __call__(self, data):
        if(isinstance(data, Message)):
            pass
        else:
            r = ChannelDb.cached_data
            print("cached_data: ", r)
            issub = []
            if r:
                for i in r:
                    print(i[-1])
                    try:
                        issubbed = await bot.get_chat_member(i[-1], data.from_user.id)
                        if issubbed.status in allowedlist:
                            issub.append(True)
                        else:
                            issub.append(False)
                    except aiogram.exceptions.TelegramBadRequest as e:
                        print("aiogram.exceptions.TelegramBadRequest: " ,e)
                        continue
                    except Exception as e:
                        print(type(e).__name__, e)
                        continue
                print(issub)
                if False in issub:
                    builder = InlineKeyboardBuilder()
                    for j in r:
                        builder.button(text='Подписаться🍇', url=j[0])
                    builder.button(text='Проверить🔐', callback_data=data.data)
                    builder.adjust(1)
                    await bot.send_message(data.message.chat.id, text='Подпишись на наших спонсоров чтобы начать зарабатывать голду', reply_markup=builder.as_markup())
                    return False
                else:
                    return True
            else:
                return True

class ThrottlingMiddleware(BaseMiddleware):

    def __init__(
        self,
        *,
        default_key: Optional[str] = DEFAULT_KEY,
        default_ttl: float = DEFAULT_TTL,
        **ttl_map: float,
    ) -> None:
        if default_key:
            ttl_map[default_key] = default_ttl

        self.default_key = default_key
        self.caches: Dict[str, MutableMapping[int, None]] = {}

        for name, ttl in ttl_map.items():
            self.caches[name] = TTLCache(maxsize=10_000, ttl=ttl)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Optional[Any]:
        user: Optional[User] = data.get("event_from_user", None)

        if user is not None:
            throttling_key = get_flag(data, "throttling_key", default=self.default_key)
            if throttling_key and user.id in self.caches[throttling_key]:
                return None
            self.caches[throttling_key][user.id] = None

        return await handler(event, data)