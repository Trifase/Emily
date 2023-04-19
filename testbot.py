from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters

import config


async def fragolone_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("testo un sacco")
    


def main():
    builder = ApplicationBuilder()
    builder.token(config.BOT_TOKEN_FRAGOLONE)
    app = builder.build()


    # app.add_handler(MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r"([0-9]+):([a-zA-Z0-9_-]{35})", re.IGNORECASE)), echo_test))
    app.add_handler(CommandHandler(['wikihow'], fragolone_test, filters=~filters.UpdateType.EDITED))
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


main()

