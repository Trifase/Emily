from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes
import config





async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Yo")
#     member = await context.bot.get_chat_member(config.ID_TESTING, 769270800)
#     print(member)
#     print(member.status)
#     if member.status == "left":
#         print("Yes")


test_token = '5404382184:AAHTp_oxftqcsVz8tchV8_Dt8g1sGhX1pFk' # Fragolone


async def my_init( context: ContextTypes.DEFAULT_TYPE):
    print("init begin")
    # wapp = web.Application()
    # wapp.add_routes([web.get('/logs', hello)])
    # runner = web.AppRunner(wapp)
    # await runner.setup()
    # site = web.TCPSite(runner, '0.0.0.0', 8888)
    # await site.start()

    print("Init is go")


app = ApplicationBuilder().token(test_token).post_init(my_init).build()
# 
app.add_handler(CommandHandler("yo", test))

app.run_polling()

