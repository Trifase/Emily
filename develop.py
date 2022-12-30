from telegram.ext import ApplicationBuilder, filters, MessageHandler, ContextTypes
import re
from telegram import Update
import config


async def echo_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(context.matches)
    print(context.match)

    for match in context.matches:
        print(match)
    


def main():
    builder = ApplicationBuilder()
    builder.token(config.BOT_TOKEN_FRAGOLONE)
    app = builder.build()


    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r"([0-9]+):([a-zA-Z0-9_-]{35})", re.IGNORECASE)), echo_test))
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


main()

