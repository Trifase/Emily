from rich import print
from telegram import Update, Bot
from telegram.ext import CallbackContext, ContextTypes
import time

import config
from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do

# Asphalto
async def azzurro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    if await no_can_do(update, context):
        return
    await printlog(update, "usa azzurro")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} usa azzurro')

    bot = context.bot
    testo = " ".join(context.args)

    try:
        member = await context.bot.get_chat_member(config.ID_ASPHALTO, update.effective_user.id)
        # print(member)
        # print(type(member))
        # if isinstance(member, telegram.chatmember.ChatMemberLeft):
        #     return
        # if isinstance(member, telegram.chatmember.ChatMemberBanned):
        #     return

    except Exception as e:
        print(e)
        return

    if "@" in testo:
        messaggio = testo.split("@")
        nickname = f'<b>{messaggio[0]}</b>'
        newmessage = f'{messaggio[1]}'
        text = f'&lt;{nickname}&gt;: {newmessage}'
        await bot.send_message(config.ID_ASPHALTO, text, parse_mode="HTML")
        if update.message.chat.id == config.ID_ASPHALTO:
            await bot.delete_message(update.message.chat.id, update.message.message_id)
    else:
        await update.message.reply_text(f'Per azzurrare manda un messaggio tipo /azzurro nickname@messaggio')
    return

async def lurkers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    import humanize
    _localize = humanize.i18n.activate("it_IT")

    if await no_can_do(update, context):
        return
    await printlog(update, "controlla i lurkers")
    if update.message.chat.id not in [config.ID_ASPHALTO, config.ID_DIOCHAN2]:
        return

    chat_id = update.message.chat.id
    if "timestamps" not in context.bot_data:
        context.bot_data["timestamps"] = {}
    if chat_id not in context.bot_data["timestamps"]:
        context.bot_data["timestamps"][chat_id] = {}

    deltas = {}

    try:
        max_secs = int(context.args[0])
    except IndexError:
        max_secs = 86400  # 24h

    for user in context.bot_data["timestamps"][chat_id].keys():
        deltas[user] = int(time.time()) - context.bot_data["timestamps"][chat_id][user]

    message = ""

    for lurker in sorted(deltas.items(), key=lambda x: x[1], reverse=True):
        # print(lurker)
        if lurker[1] > max_secs:
            try:
                mylurker = await context.bot.get_chat_member(chat_id, lurker[0])
                message += f'{mylurker.user.first_name} - {str(humanize.precisedelta(lurker[1], minimum_unit="seconds"))} fa\n'
            except Exception:
                pass


    if message:
        await update.message.reply_text(message)
    else:
        await update.message.reply_text(f"Nessuno lurka da più di {max_secs} secondi")
