from telegram import Update
from telegram.ext import ApplicationBuilder, AIORateLimiter, CommandHandler, ContextTypes, filters

# import config
import logging

# from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
# from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
# Enable logging

logging.basicConfig(
    level=logging.DEBUG
    # format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG

)

logger = logging.getLogger(__name__)


async def fragolone_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("testo un sacco")
    for i in range(50):
        await msg.edit_text(f"test {i}")


def main():
    builder = ApplicationBuilder()
    # builder.token(config.BOT_TOKEN_FRAGOLONE)
    builder.token("6114487111:AAHchBZDtV2t3hRMH-2S-fY_BhLU9CHdXcM")
    builder.rate_limiter(AIORateLimiter())
    app = builder.build()


    app.add_handler(CommandHandler(['test'], fragolone_test, filters=~filters.UpdateType.EDITED))
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

    # app.run_polling()

main()

