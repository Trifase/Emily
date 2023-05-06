from rich import print
from telegram import Update
from telegram.ext import ContextTypes

import config
from utils import no_can_do, printlog

# Asphalto
async def azzurro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    if await no_can_do(update, context):
        return
    await printlog(update, "usa azzurro")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} usa azzurro')

    bot = context.bot
    testo = " ".join(context.args)

    try:
        await context.bot.get_chat_member(config.ID_ASPHALTO, update.effective_user.id)
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
        await update.message.reply_text('Per azzurrare manda un messaggio tipo /azzurro nickname@messaggio')
    return
