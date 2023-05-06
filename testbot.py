from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters

import config

# from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
# from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

async def fragolone_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("testo un sacco")


def main():
    builder = ApplicationBuilder()
    builder.token(config.BOT_TOKEN_FRAGOLONE)
    app = builder.build()


    app.add_handler(CommandHandler(['wikihow'], fragolone_test, filters=~filters.UpdateType.EDITED))
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

    # app.run_polling()

main()

