
from telegram.ext import ApplicationBuilder, filters, MessageHandler, ContextTypes, CommandHandler
import re
from telegram import Update, Bot, InputMediaPhoto
import config


async def echo_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    import requests

    count = 3

    url_text = "https://hargrimm-wikihow-v1.p.rapidapi.com/steps"
    url_images = "https://hargrimm-wikihow-v1.p.rapidapi.com/images"

    querystring = {"count":f"{count}"}
    headers = {
        "X-RapidAPI-Key": "6b1eba0153msh8cd62219142c90fp1f3ea3jsn5e757aabd168",
        "X-RapidAPI-Host": "hargrimm-wikihow-v1.p.rapidapi.com"
    }

    response_text = requests.request("GET", url_text, headers=headers, params=querystring).json()
    response_images = requests.request("GET", url_images, headers=headers, params=querystring).json()

    bot = Bot(token=config.BOT_TOKEN)

    mystring = ""
    for k, v in response_text.items():
        mystring += f"{k}. {v}\n"

    images = [url for url in response_images.values()]
    medialist = [InputMediaPhoto(media=url) for url in images]
    await update.message.reply_media_group(media=medialist, caption=mystring)

    # await bot.send_message(config.ID_LOTTO, mystring)
    


def main():
    builder = ApplicationBuilder()
    builder.token(config.BOT_TOKEN_FRAGOLONE)
    app = builder.build()


    # app.add_handler(MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r"([0-9]+):([a-zA-Z0-9_-]{35})", re.IGNORECASE)), echo_test))
    app.add_handler(CommandHandler(['wikihow'], echo_test, filters=~filters.UpdateType.EDITED))
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


main()

