import time
import re
import tempfile
import pprint

from telegram import Update, Bot
from telegram.ext import CallbackContext, ContextTypes
from rich import print
from utils import printlog, get_display_name, no_can_do, get_now, get_chat_name, alert
import config
import sys


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} testa tantissimo!')
    await printlog(update, "testa tantissimo")
    await alert(update, context, "ha testato tantissimo", "errore di prova")
    # pprint.pprint(sys.modules['space'])
    await update.message.reply_text("Test fallito.")

async def getfile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    picture = update.message.reply_to_message.photo[-1]
    actual_picture = await picture.get_file()
    pprint.pprint(actual_picture.to_dict())