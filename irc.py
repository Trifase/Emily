import JustIRC
import requests
import config

token = config.BOT_TOKEN_FRAGOLONE
# chat_id = config.ID_DIOCHAN
chat_id = config.ID_TESTING

ircbot = JustIRC.IRCConnection()


def send_tg_message(sender: str, message: str, chat_id=chat_id):
    TELEGRAM_URL = "https://api.telegram.org/ircbot"
    ircbot_TOKEN = config.ircbot_TOKEN
    # < with &lt;, > with &gt; and & with &amp;
    message = f"<{sender}> {message}"
    message = message.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }

    requests.post(f"{TELEGRAM_URL}{ircbot_TOKEN}/sendMessage", data=data)


def on_connect(ircbot):
    ircbot.set_nick("EmiliaParanoica")
    ircbot.send_user_packet("EmiliaParanoica")


def on_welcome(ircbot):
    ircbot.join_channel("#diochan")


def on_message(ircbot, channel, sender, message):
    send_tg_message(sender, message)


ircbot.on_connect.append(on_connect)
ircbot.on_welcome.append(on_welcome)
ircbot.on_public_message.append(on_message)
# ircbot.on_packet

ircbot.connect("irc.rizon.org")
ircbot.run_loop()
