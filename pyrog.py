import asyncio
import random
from collections import defaultdict

from pyrogram import Client
from telegram import Update
from telegram.ext import ContextTypes

import config
from utils import no_can_do, printlog

api_id = config.API_ID
api_hash = config.API_HASH



async def get_user_from_username(username):
    async with Client("db/pyro-session-trifase.session", api_id, api_hash) as pyro:
        myuser = await pyro.get_users(username)
        mymessage = f"Username: {myuser.username}\n"
        mymessage += f"ID: {myuser.id}\n"
        mymessage += f"Status: {myuser.status}"
        return mymessage

async def get_user_from_user_id(user_id):
    async with Client("db/pyro-session-trifase.session", api_id, api_hash) as pyro:
        myuser = await pyro.get_users(user_id)
        return myuser

async def get_chatmember_pyrog(chat_id, user_id):
    async with Client("db/pyro-session-trifase.session", api_id, api_hash) as pyro:
        mychatmember = await pyro.get_chat_member(chat_id, user_id)
        return mychatmember

async def get_all_chatmembers(chat_id):
    async with Client("db/pyro-session-trifase.session", api_id, api_hash) as pyro:
        members = []
        async for member in pyro.get_chat_members(chat_id):
            members.append(member)
        return members


async def get_reaction_count(user_id, chat_id):
    r = defaultdict(int)
    n = 0
    n_2022 = 0
    n_r = 0

    async with Client("db/pyro-session-trifase.session", api_id, api_hash) as pyro:
        async for message in pyro.search_messages(chat_id, "", from_user=user_id):
            n += 1
            try:
                if message.date.year <= 2021:
                    continue
            except Exception as e:
                print(e)

            else:
                n_2022 += 1
                if message.reactions:
                    n_r += 1
                    for reac in message.reactions:
                        r[reac.emoji] += int(reac.count)
        if not r:
            return None

        r = sorted(r.items(), key=lambda kv: kv[1], reverse=True)
        data = {}
        data['user_id'] = user_id
        data['chat_id'] = chat_id
        data['messages_total'] = n
        data['messages_reacted'] = n_r
        data['reactions'] = {}

        for reaction in r:
            data['reactions'][reaction[0]] = reaction[1]

        return data


async def send_reaction(chat_id: int, message_id: int, emoji="👎"):
    async with Client("db/pyro-session-trifase.session", api_id, api_hash) as pyro:
        await pyro.send_reaction(chat_id, message_id, emoji)

async def pyro_bomb_reaction(chat_id, user_id, limit=100, sample=20):
    async with Client("db/pyro-session-trifase.session", api_id, api_hash) as pyro:
        msglist = []
        async for message in pyro.search_messages(chat_id, "", from_user=user_id, limit=limit):
            msglist.append(message)
        for message in random.sample(msglist, sample):
            try:
                await pyro.send_reaction(chat_id, message.id, random.choice(["👎", "💩", "🤡", "🤮"]))
            except Exception as e:
                print(e)
                continue
            await asyncio.sleep(0.5)

async def reaction_karma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return
    if update.effective_user.id not in config.ADMINS:
        return

    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
    else:
        user_id = update.message.from_user.id

    chat_id = update.message.chat.id

    await printlog(update, "fa l'elenco delle reaction dell'utente", user_id)
    mymsg = await update.message.reply_html("Controllo, un attimo.")

    r = await get_reaction_count(user_id, chat_id)

    if not r:
        await mymsg.edit_text("Non trovo un cazzo, scusa.")
        return

    message = f"Ecco il bilancio su {r['messages_total']} messaggi ({r['messages_reacted']} messaggi con reazioni).\n"
    message += f"Utente: {user_id}\n"
    message += f"Chat ID: {chat_id}\n\n"

    m = ""
    for react in r['reactions'].items():
        m += f"{react[0]} {react[1]}\n"
    message += m
    await mymsg.edit_text(message)
    # await update.message.reply_html(message)

def get_dialogs():
    with Client("db/pyro-session-trifase.session", api_id, api_hash) as pyro:
        mydialogs = pyro.get_dialogs()
        for d in mydialogs:
            print(f"{d.chat.id}\t{d.chat.first_name or d.chat.title}")
        print(f"Chat totali: {pyro.get_dialogs_count()}")

def get_reactions_from_post_id(chat_id, message_id):
    with Client("db/pyro-session-trifase.session", api_id, api_hash) as pyro:
        message = pyro.get_messages(chat_id, message_id)
        post_reactions = message.reactions
        reactions = {}

        for react in post_reactions.reactions:
            reactions[react.emoji] = react.count

        return reactions



# print(get_reactions_from_post_id(-1001155308424, 629368))



