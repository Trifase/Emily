import JustIRC
import requests
import config

bot = JustIRC.IRCConnection()
def send_tg_message(sender: str, message: str, chat_id=config.ID_DIOCHAN):
        TELEGRAM_URL = "https://api.telegram.org/bot"
        BOT_TOKEN = config.BOT_TOKEN
        # < with &lt;, > with &gt; and & with &amp;
        message = f"<{sender}> {message}"
        message = message.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
        }

        response = requests.post(
            f"{TELEGRAM_URL}{BOT_TOKEN}/sendMessage", data=data
        )


def on_connect(bot):
    bot.set_nick("EmiliaParanoica")
    bot.send_user_packet("EmiliaParanoica")

def on_welcome(bot):
    bot.join_channel("#diochan")

def on_message(bot, channel, sender, message):
    send_tg_message(sender, message)

bot.on_connect.append(on_connect)
bot.on_welcome.append(on_welcome)
bot.on_public_message.append(on_message)
# bot.on_packet

bot.connect("irc.rizon.org")
bot.run_loop()