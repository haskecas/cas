import math

import asyncpg
from aiogram.types import Message
import json
import datetime
from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.models.update import Update
user = "bohdandemyanchuk"
password = "AeT8hs9lOLSq"
database = "neondb"
host = "ep-weathered-resonance-391969.eu-central-1.aws.neon.tech"

token = '6931614087:AAFtr7BabDdZZao-aLnWxxIdV5zpgVmIgl4'
ctoken = "12618:AAfz13C23pFlQYAZ8DIZImQVA80BmAWBpjY"
crypto = AioCryptoPay(token=ctoken, network=Networks.TEST_NET)

channel_to_send = -1002049288216

def float_to_int_str(n):
    chars = ".,"
    for c in chars:
        n = n.replace(c, "")
    return n
async def create_tables():
    con = await asyncpg.connect(user=user, password=password, database=database, host=host)
    try:
        await con.execute(
            """CREATE TABLE IF NOT EXISTS ref_cas
(
    name name COLLATE pg_catalog."C" NOT NULL,
    amount integer DEFAULT 0,
    CONSTRAINT ref_pkey PRIMARY KEY (name)
)""")
        await con.execute("""CREATE TABLE IF NOT EXISTS users_cas
(
    id bigint NOT NULL,
    name name COLLATE pg_catalog."C",
    surname name COLLATE pg_catalog."C",
    lang character(10) COLLATE pg_catalog."default",
    date name COLLATE pg_catalog."C",
    is_admin boolean DEFAULT false,
    refs integer DEFAULT 0,
    balance integer DEFAULT 0,
    history jsonb NOT NULL DEFAULT '{"bets": [], "deposits": []}'::jsonb,
    can_withdraw boolean DEFAULT true,
    CONSTRAINT users_pkey PRIMARY KEY (id)
)""")
        await con.execute("""CREATE TABLE IF NOT EXISTS op_cas
(
    id bigint NOT NULL,
    link name COLLATE pg_catalog."C" NOT NULL,
    CONSTRAINT channels_pkey PRIMARY KEY (id)
)"""
        )
    except Exception as e:
        pass
    finally:
        await con.close()

class UserDb:
    def __init__(self, message: Message):
        self.message = message

    async def add_user(self, invited_by):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            await con.execute(
                'INSERT INTO users_cas ("id", "name", "surname", "lang", "date", "invited_by") VALUES ($1, $2, $3, $4, $5, $6)',
                self.message.chat.id, self.message.from_user.first_name, self.message.from_user.last_name, self.message.from_user.language_code, self.message.date.strftime('%Y-%m-%d %H:%M:%S'), int(invited_by) if invited_by is not None else None
            )
            return True
        except asyncpg.exceptions.UniqueViolationError:
            await con.execute(
                'UPDATE users_cas SET "lang" = $1, "name" = $2, "surname" = $3 WHERE "id" = $4',
                self.message.from_user.language_code, self.message.from_user.first_name,
                self.message.from_user.last_name, self.message.chat.id
            )
            return False
        except Exception as e:
            print(e)
        finally:
            await con.close()

    @staticmethod
    async def increase(_id: int):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            await con.execute(
                'UPDATE users_cas SET refs = refs + 1 WHERE id = $1',
                _id
            )
        finally:
            await con.close()

    @staticmethod
    async def get_refs(_id: int):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            return await con.fetchval('select refs from users_cas where id = $1', _id)
        finally:
            await con.close()
    @staticmethod
    async def get_profile(_id: int):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            return await con.fetchrow('select * from users_cas where id = $1', _id)
        finally:
            await con.close()
    @staticmethod
    async def statistic():
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            count_result = await con.fetchval('SELECT count(id) FROM users_cas')

            per_result = await con.fetch(
                'SELECT lang, COUNT(*) as count FROM users_cas GROUP BY lang'
            )
            total_count = sum(row['count'] for row in per_result)

            percentages = []
            for row in per_result:
                language_code = row['lang']
                count = row['count']
                percentage = (count / total_count) * 100
                percentage_formatted = f"{percentage:.2f}% ({count})"
                percentages.append(f"{language_code}:{percentage_formatted}")

            result_str = '\n'.join(percentages)
            return count_result, result_str

        finally:
            await con.close()

    @staticmethod
    async def update_balance(_id: int, amount: float, give_ref: bool = False):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            await con.execute(
                'UPDATE users_cas SET balance = balance + $2 WHERE id = $1',
                _id, amount
            )
            if give_ref:
                data = await UserDb.get_profile(_id)
                await UserDb.update_balance(data["invited_by"], math.fabs(amount*0.2), False)
        finally:
            await con.close()

    @staticmethod
    async def get_users():
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            result = await con.fetch("SELECT id FROM users_cas")
            user_ids = [row["id"] for row in result]
            return user_ids
        finally:
            await con.close()
    @staticmethod
    async def new_bet(_id, game, amount, won, guessed, was):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            query = f'''
                    UPDATE users_cas
                    SET history = jsonb_insert(history, '{{bets, -1}}', $1) where id = $2
                '''

            # Execute the query
            await con.execute(query, json.dumps({"game": game, "amount": amount, "won": won, "time": str(datetime.datetime.utcnow()), "guessed": guessed, "was": was}, sort_keys=True), _id)
        finally:
            await con.close()
    @staticmethod
    async def new_deposit(_id, amount, payment_method):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            query = f'''
                    UPDATE users_cas
                    SET history = jsonb_insert(history, '{{deposits, -1}}', $1) where id = $2
                '''

            # Execute the query
            await con.execute(query, json.dumps({"amount": amount, "payment_method": payment_method, "time": str(datetime.datetime.utcnow())}, sort_keys=True), _id)
        finally:
            await con.close()

    @staticmethod
    async def can_withdraw(_id):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            return await con.fetchval('select can_withdraw from users_cas where id = $1', _id)
        finally:
            await con.close()

class RefDb:
    @staticmethod
    async def increase(name: str):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            await con.execute(
                'UPDATE ref_cas SET amount = amount + 1 WHERE name = $1',
                name
            )
        finally:
            await con.close()

    @staticmethod
    async def add_ref(refname: str):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            await con.execute('INSERT INTO ref_cas (name) VALUES ($1)', refname)
        finally:
            await con.close()

    @staticmethod
    async def reset_ref(refname: str):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            await con.execute(
                'UPDATE ref_cas SET amount = 0 WHERE name = $1', refname
            )
        finally:
            await con.close()

    @staticmethod
    async def get_refs():
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            names = await con.fetch("SELECT name FROM ref_cas")
            result = [name["name"] for name in names]
            return result
        finally:
            await con.close()

    @staticmethod
    async def get_ref(name: str):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            result = await con.fetch('SELECT name, amount FROM ref_cas WHERE name = $1', name)
            return result
        finally:
            await con.close()

    @staticmethod
    async def delete_ref(name: str):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            await con.execute('DELETE FROM ref_cas WHERE name = $1', name)
        finally:
            await con.close()






class ChannelDb:
    cached_data = None
    @staticmethod
    async def cash_link_id():
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            result = await con.fetch('SELECT link, id FROM op_cas')
            ret = []
            for i in result:
                ret.append([i['link'], i['id']])
            ChannelDb.cached_data = ret
        finally:
            await con.close()
    @staticmethod
    async def get_link_id():
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            result = await con.fetch('SELECT link, id FROM op_cas')
            return result
        finally:
            await con.close()

    @staticmethod
    async def delete_channel(_id):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            await con.execute('DELETE FROM op_cas WHERE id = $1', _id)
        finally:
            await con.close()

    @staticmethod
    async def add_channel(_id: int, link: str):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)
        try:
            await con.execute('INSERT INTO op_cas (link, id) VALUES ($1, $2)', link, _id)
        finally:
            await con.close()

class BotDb:
    @staticmethod
    async def sql_execute(query):
        con = await asyncpg.connect(user=user, password=password, database=database, host=host)

        try:
            result = await con.fetch(query)
            return result
        finally:
            await con.close()