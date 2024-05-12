import traceback
import pprint
import html
from telegram import CallbackQuery
from telegram.ext import ContextTypes

import config
from utils import printlog


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    await printlog(update, f"{tb_string}", error=True)
    rawtext = pprint.pformat(update.to_dict())
    # print(rawtext)
    rawtext = html.escape(rawtext)

    if isinstance(update, CallbackQuery):
        user = update.from_user
        chat_id = update.message.chat.id
    else:
        user = update.effective_user
        chat_id = update.effective_chat.id
    link_chat_id = str(chat_id).replace("-100", "")

    message_id = None

    if update.effective_message and update.effective_message.message_id:
        message_id = update.effective_message.message_id

    emoji_link = ''
    if link_chat_id and message_id:
        emoji_link = f'<a href="t.me/c/{link_chat_id}/{message_id}">🔗</a> '
    
    await context.bot.send_message(
        chat_id=config.ID_BOTCENTRAL,
        text=f'{emoji_link}ERRORE!',
        parse_mode="HTML",
    )
    await update.message.forward(config.ID_BOTCENTRAL)
    await context.bot.send_message(
        chat_id=config.ID_BOTCENTRAL,
        text=f'<pre><code class="language-python">{rawtext}</code></pre>',
        parse_mode="HTML",
    )
    await context.bot.send_message(
        chat_id=config.ID_BOTCENTRAL,
        text=f'<pre><code class="language-python">{tb_string[:4000]}</code></pre>',
        parse_mode="HTML",
    )

