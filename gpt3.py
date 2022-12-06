
import openai
import time
import re
import random
import aiohttp

from telegram import Update, Bot
from telegram.ext import CallbackContext, ContextTypes
from telegram.constants import ChatMemberStatus
from rich import print
from utils import printlog, get_display_name, no_can_do, get_now, get_chat_name
import config



async def ai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    if update.effective_chat.id in [config.ID_TIMELINE]:
        try:
            this_user = await context.bot.get_chat_member(update.message.chat.id, update.effective_user.id)
        except Exception as e:
            return
        if this_user.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return

    elif update.effective_chat.id not in [config.ID_ASPHALTO, config.ID_DIOCHAN, config.ID_LOTTO, config.ID_RITALY, config.ID_NINJA, ] and update.message.from_user.id != config.ID_TRIF:
        # await update.effective_message.delete()
        return

    model = 'text-davinci-003'
    if update.effective_user.id == 214582784: # ChrisQQ
        model = 'text-davinci-001'

    price_per_1k = 0.02

    try:

        input = update.message.text[4:]

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config.OPENAI_API_KEY}',
        }

        data = {
            "prompt": f"{input}",
            "model": model,
            "temperature": 1,
            "max_tokens": 300,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.openai.com/v1/completions", json=data, headers=headers) as r:
                response = await r.json()
        output = response['choices'][0]['text'].strip()

        total_tkns = response['usage']['total_tokens']
        total_price = (price_per_1k/1000)*total_tkns
        rounded_price = str(round(total_price, 4))

        await printlog(update, "interroga OpenAI", f"{total_tkns} tokens, circa ${rounded_price}")

        await update.message.reply_html(f"<b>{input}</b>\n{output}\n<i>______</i>\n<i>Questo messaggio è costato circa ${rounded_price}</i>")

    except Exception as e:
        await update.message.reply_text(f"{e}")


async def ai_blank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    if update.effective_chat.id in [config.ID_DIOCHAN, config.ID_RITALY, config.ID_ASPHALTO]:
        pass
    else:
        if update.effective_user.id in config.ADMINS:
            pass
            # if update.effective_chat.id == config.ID_RITALY:
            #     delmessage = update.message.reply_text(f"!askdavinci {update.message.text[4:]}")
            #     time.sleep(1)
            #     bot.delete_message(chat_id=update.effective_chat.id, message_id=delmessage.message_id)
            # return
        else:
            return
    await printlog(update, "interroga OpenAI")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} interroga OpenAI')

    try:
        input = update.message.text[7:]

        if input.count("BLANK") != 1:
            await update.message.reply_text("Devi inserire un BLANK nel testo.")
            return

        fixes = re.split('(BLANK)', input)

        openai.api_key = config.OPENAI_API_KEY
        response = openai.Completion.create(
            engine="text-davinci-001",
            prompt=f"{fixes[0]}",
            suffix=f"{fixes[2]}",
            temperature=0.9,
            max_tokens=300,
            top_p=1,
            frequency_penalty=0.2,
            presence_penalty=0.5
        )
        # print(input)
        # print()
        # print(fixes[0])
        # print()
        # print(fixes[2])
        # print()
        # print(response)
        output = response['choices'][0]['text'].replace("\n\n", "\n")

        await update.message.reply_html(f"{fixes[0]}<b>{output}</b>{fixes[2]}")

    except Exception as e:
        await update.message.reply_text(f"{e}")


async def ai_tarocchi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    # if update.effective_chat.id in [config.ID_DIOCHAN, config.ID_ASPHALTO]:
    #     pass
    # else:
    #     if update.effective_user.id not in config.ADMINS:
    #         if update.effective_chat.id == config.ID_RITALY:
    #             delmessage = update.message.reply_text(f"!askdavinci {update.message.text[4:]}")
    #             time.sleep(1)
    #             await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=delmessage.message_id)
    #             return
    #         return

    try:
        input_list = [
            "previsioni dei tarocchi di oggi",
            "tarocchi previsioni del giorno",
            "le previsioni di oggi coi tarocchi",
            "cosa accadrà oggi secondo i tarocchi",
            "tarocchi: le previsioni odierne",
            "lettura dei tarocchi di oggi"
        ]

        input = random.choice(input_list)

        openai.api_key = config.OPENAI_API_KEY
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"{input}",
            temperature=1,
            max_tokens=300,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        output = response['choices'][0]['text'].strip()
        await printlog(update, "chiede i tarocchi ad OpenAI")
        # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} interroga OpenAI')
        await update.message.reply_html(f"<b>{input}</b>\n{output}")

    except Exception as e:
        await update.message.reply_text(f"{e}")
