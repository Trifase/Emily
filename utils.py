import datetime
import inspect
import io
import json
import logging
import logging.handlers
import textwrap
import time
from typing import Callable, Optional, Tuple

from aiohttp import web
from dataclassy import dataclass
from rich import print as cprint
from telegram import (
    Bot,
    CallbackQuery,
    ChatMember,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    User,
)
from telegram.ext import CallbackContext

import config
from database import Chatlog, Reminders


@dataclass
class InlineButton:
    chat_id: int
    original_msg_id: int
    from_user_id: str
    callable: Callable
    original_update: Update = None
    vote: str


@dataclass
class ForgeCommand:
    original_update: Update
    new_text: str
    new_args: list[str] = []
    callable: Callable


# Logging setup
log_level = logging.INFO

logger = logging.getLogger()
logger.setLevel(log_level)

# httpx become very noisy from 0.24.1, so we set it to WARNING
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

fh = logging.handlers.RotatingFileHandler("logs/log.log", maxBytes=1000000, backupCount=5)
fh.setLevel(log_level)


formatter = logging.Formatter("%(asctime)s [%(name)s] %(message)s", datefmt="[%Y-%m-%d %H:%M:%S]")
fh.setFormatter(formatter)

logger.addHandler(fh)


async def crea_sondaggino(context, update, max_votes, _callable, domanda=""):
    current_votes = round(max_votes / 2)

    if "votazioni_attive" not in context.chat_data:
        context.chat_data["votazioni_attive"] = {}
    if domanda:
        domanda = f"{domanda}\n"
    context.chat_data["votazioni_attive"][update.effective_message.id] = {
        # 'callable': callable,
        "timestamp": int(time.time()),
        "domanda": domanda,
        "initiated_by": update.effective_user.id,
        "current_votes": current_votes,
        "max_votes": max_votes,
        "voters": [],
    }

    keyboard = [
        [
            InlineKeyboardButton(
                "✅",
                callback_data=InlineButton(
                    chat_id=update.effective_chat.id,
                    original_msg_id=update.effective_message.id,
                    from_user_id=update.effective_user.id,
                    original_update=update,
                    callable=_callable,
                    vote="sì",
                ),
            ),
            InlineKeyboardButton(
                "❌",
                callback_data=InlineButton(
                    chat_id=update.effective_chat.id,
                    original_msg_id=update.effective_message.id,
                    from_user_id=update.effective_user.id,
                    original_update=update,
                    callable=_callable,
                    vote="no",
                ),
            ),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    messaggio = f"<code>{domanda if domanda else ''}Conferme: {current_votes}/{max_votes}\n{print_progressbar(current_votes, max_votes, max_votes)}</code>"

    to_pin = await update.message.reply_html(messaggio, reply_markup=reply_markup)

    if update.effective_chat.id in [config.ID_ASPHALTO]:
        await to_pin.pin(disable_notification=True)
    return


async def webserver_logs(request) -> web.Response:
    current_m = datetime.date.today().strftime("%Y-%m")
    with open(f"logs/{current_m}-logs.txt", "r") as file:
        last_lines = file.readlines()[-100:]
        my_response = ""

        for line in last_lines:
            my_response += line

    return web.Response(text=my_response)


def make_delete_button(update) -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton("🗑️", callback_data=f"deleteme_{update.effective_user.id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def is_inline_button(callback_data):
    if isinstance(callback_data, InlineButton):
        return True
    return False


def is_forged_command(callback_data):
    if isinstance(callback_data, ForgeCommand):
        return True
    return False


def is_lurkers_list(callback_data):
    if isinstance(callback_data, list) and callback_data[0] == "LURKERS_LIST":
        return True
    return False


def get_now():
    return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def function_name():
    # print(inspect.stack())
    func_name = inspect.stack()[2][3]
    return func_name


def is_function_enabled(chat_id, function, context):
    if chat_id > 0:  # è una chat privata.
        return True

    if "settings" not in context.chat_data:
        context.chat_data["settings"] = {}

    if function not in context.chat_data["settings"]:  # non è stata ancora inizializzata
        context.chat_data["settings"][function] = "enabled"  # default è abilitata
        return True

    elif context.chat_data["settings"].get(function) == "enabled":  # è abilitata
        return True

    elif context.chat_data["settings"].get(function) == "disabled":  # è disabilitata
        return False

    return True  # richiesta malformata: abilitata


async def no_can_do(update, context):
    if "global_bans" not in context.bot_data:
        context.bot_data["global_bans"] = []
    one = update.effective_user.id in context.bot_data["global_bans"]
    two = is_function_enabled(update.effective_chat.id, function_name(), context)

    if one or not two:
        return True
    return False


async def get_chat_name(chat_id, tolog=False, tobot=False):
    bot = Bot(config.BOT_TOKEN)
    this_chat = await bot.get_chat(chat_id)

    if tobot:
        if this_chat.id > 0:
            return "privato"
        else:
            chat_title = this_chat.title
            return f"{chat_title}"

    if tolog:
        if this_chat.id > 0:
            return "chat privata"
        else:
            chat_title = this_chat.title
            return f"{chat_title} ({str(this_chat.id)})"

    if this_chat.id > 0:
        return "[deep_sky_blue1]chat privata[/deep_sky_blue1]"
    else:
        if len(this_chat.title) > 20:
            chat_title = f"{this_chat.title[:20]}..."
        else:
            chat_title = this_chat.title
        return f"[yellow1]{chat_title}[/yellow1] ({str(this_chat.id)})"


async def get_display_name(user: User, tolog=False, tobot=False):
    if tolog:
        if user.username:
            return f"{user.full_name} (@{user.username}) [{user.id}]"
        else:
            return f"{user.full_name} [{user.id}]"

    if tobot:
        if user.username:
            return f"{user.full_name} (@{user.username})"
        else:
            return f"{user.full_name}"

    if user.username:
        return f"[deep_pink3]{user.full_name} (@{user.username})[/deep_pink3]"
    else:
        return f"[deep_pink3]{user.full_name}[/deep_pink3]"


async def is_user(update):
    if update.message.chat.type == "private":
        return True
    return False


async def printlog(update, action, additional_data=None, error=False):
    if error:
        cprint(f"{get_now()} [red1]!! ERROR !![/red1]\n{action}")
        logging.error(f"{action}")
        return

    if isinstance(update, CallbackQuery):
        user = update.from_user
        chat_id = update.message.chat.id
    else:
        user = update.effective_user
        chat_id = update.effective_chat.id
    link_chat_id = str(chat_id).replace("-100", "")

    if update.effective_message:
        message_id = update.effective_message.message_id

    if additional_data:
        cprint(
            f"{get_now()} {await get_display_name(user)} in {await get_chat_name(chat_id)} {action}: {additional_data}"
        )
        message_log = f"{await get_display_name(user, tolog=True)} in {await get_chat_name(chat_id, tolog=True)} {action}: {additional_data}"

        message_bot = f'<a href="t.me/c/{link_chat_id}/{message_id}">🔗</a> <code>{await get_display_name(user, tobot=True)}</code> in <code>{await get_chat_name(chat_id, tobot=True)}</code> {action}: <code>{additional_data}</code>'

    else:
        cprint(f"{get_now()} {await get_display_name(user)} in {await get_chat_name(chat_id)} {action}")
        message_log = (
            f"{await get_display_name(user, tolog=True)} in {await get_chat_name(chat_id, tolog=True)} {action}"
        )
        message_bot = (
            f'<a href="t.me/c/{link_chat_id}/{message_id}">🔗</a> <code>{await get_display_name(user, tobot=True)}</code> in <code>{await get_chat_name(chat_id, tobot=True)}</code> {action}'
        )

    logging.info(message_log)

    LOG_TO_BOT_CENTRAL = config.LOG_TO_BOT_CENTRAL
    if LOG_TO_BOT_CENTRAL:
        bot = Bot(config.BOT_TOKEN)
        await bot.send_message(config.ID_BOTCENTRAL, message_bot, parse_mode="HTML")


async def old_printlog(update, action, additional_data=None):
    if isinstance(update, CallbackQuery):
        user = update.from_user
        chat_id = update.message.chat.id
    else:
        user = update.effective_user
        chat_id = update.effective_chat.id
    current_m = datetime.date.today().strftime("%Y-%m")
    if additional_data:
        print(
            f"{get_now()} {await get_display_name(user)} in {await get_chat_name(chat_id)} {action}: {additional_data}"
        )
        with open(f"logs/{current_m}-logs.txt", "a") as f:
            f.write(
                f"{get_now()} {await get_display_name(user, tolog=True)} in {await get_chat_name(chat_id, tolog=True)} {action}: {additional_data}\n"
            )
    else:
        print(f"{get_now()} {await get_display_name(user)} in {await get_chat_name(chat_id)} {action}")
        with open(f"logs/{current_m}-logs.txt", "a") as f:
            f.write(
                f"{get_now()} {await get_display_name(user, tolog=True)} in {await get_chat_name(chat_id, tolog=True)} {action}\n"
            )


async def alert(update, context: CallbackContext, action, errore):
    if isinstance(update, CallbackQuery):
        user = update.from_user
        chat_id = update.message.chat.id
    else:
        user = update.effective_user
        chat_id = update.effective_chat.id

    messaggio = f"{get_now()} {await get_display_name(user, tolog=True)} in {await get_chat_name(chat_id, tolog=True)} {action}: {errore}"
    await context.bot.send_message(config.ID_BOTCENTRAL, messaggio)


def print_progressbar(
    current_percentage, complete=100, max_length=20, fill_char="█", empty_char="░", prefix="[", suffix="]"
):
    pct = int(current_percentage * max_length / complete)
    bar = prefix + fill_char * pct + empty_char * (max_length - pct) + suffix
    return bar


def expand(s):
    result = ""
    for ch in s:
        result = result + ch + " "
    return result[:-1]


def print_to_string(*args, **kwargs):
    output = io.StringIO()
    print(*args, file=output, **kwargs)
    contents = output.getvalue()
    output.close()
    return contents


async def is_member_in_group(user_id, chat_id, context):
    if chat_id > 0:  # è una chat privata.
        return False
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ["left", "kicked"]:
            return False
        return True
    except Exception as e:
        print(e)
        print(f"chat_id: {chat_id}, user_id: {user_id}")
        return True


def count_k_v(d):
    keys = 0
    values = 0
    if isinstance(d, dict):
        for item in d.keys():
            if isinstance(d[item], (list, tuple, dict)):
                keys += 1
                k, v = count_k_v(d[item])
                values += v
                keys += k
            else:
                keys += 1
                values += 1

    elif isinstance(d, (list, tuple)):
        for item in d:
            if isinstance(item, (list, tuple, dict)):
                k, v = count_k_v(item)
                values += v
                keys += k
            else:
                values += 1

    return keys, values


def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


def ingest_json_to_log_db(filename: str) -> None:
    with open(filename, "r", encoding="utf8") as f:
        data = json.load(f)

    chat_name = data["name"]
    chat_id = data["id"]
    chat_type = data["type"]

    out = {"name": chat_name, "id": chat_id, "type": chat_type, "messages": []}

    for message in data["messages"]:
        m = {}

        if message.get("photo") or message.get("media_type"):
            continue
        if message.get("from_id") == "user1735623047":
            continue
        if message.get("type") == "service":
            continue

        text = "".join([chunk["text"] for chunk in message["text_entities"]])
        if text.startswith("/"):
            continue
        # print(message)
        m["id"] = message["id"]
        m["date"] = datetime.datetime.strptime(message["date"], "%Y-%m-%dT%H:%M:%S")
        m["name"] = message["from"]
        m["user_id"] = int(message["from_id"].replace("user", "").replace("channel", ""))
        m["text"] = text

        if message.get("reply_to_message_id"):
            m["reply_to_message_id"] = message["reply_to_message_id"]
        out["messages"].append(m)

    for message in out["messages"]:
        chat_id = out["id"]
        message_id = message["id"]
        user_id = message["user_id"]
        timestamp = int(datetime.datetime.timestamp(message["date"]))
        name = message["name"]
        text = message["text"]
        reply_to_message_id = None
        if message.get("reply_to_message_id"):
            reply_to_message_id = message["reply_to_message_id"]

        Chatlog.create(
            chat_id=chat_id,
            message_id=message_id,
            user_id=user_id,
            name=name,
            timestamp=timestamp,
            text=text,
            reply_to_message_id=reply_to_message_id,
        )
    return


def print_clean_json(filename: str, min_datetime: datetime, max_datetime: datetime) -> str:
    """
        Genera una stringa con i messaggi contenuti nel file json passato come argomento.
    Al momento, min_datetime and max_datetime devono essere due `Datetime.datetime` e non sono opzionali.

    Args:
        filename (str): Il file json da parsare
        min_datetime (datetime): Data minima per prendere i messaggi
        max_datetime (datetime): Data massima per prendere i messaggi

    Returns:
        str: Stringa coi messaggi formattati
    """
    with open(filename, "r", encoding="utf8") as f:
        data = json.load(f)

    return_string = ""

    if not min_datetime and not max_datetime:
        return

    for message in data["messages"]:
        message_date = datetime.datetime.strptime(message["date"], "%Y-%m-%dT%H:%M:%S")

        if message_date < min_datetime or message_date > max_datetime:
            continue

        if message.get("reply_to_message_id"):
            reply_id = f" (rispondendo a {message['reply_to_message_id']})"
        else:
            reply_id = ""

        return_string += f"{message['id']}: <{message['from']}>{reply_id} {message['text']}\n"
    return return_string


def retrieve_logs_from_db(chat_id: int, min_time: int | float, max_time: int | float) -> str:
    logs = (
        Chatlog.select()
        .where((Chatlog.chat_id == chat_id) & (Chatlog.timestamp >= min_time) & (Chatlog.timestamp <= max_time))
        .order_by(Chatlog.timestamp.asc())
    )
    mystring = ""
    for line in logs:
        if line.reply_to_message_id:
            reply_id = f" (rispondendo a {line.reply_to_message_id})"
        else:
            reply_id = ""

        mystring += f"{line.message_id}: <{line.name}>{reply_id} {line.text}\n"
    return mystring


def get_reminders_from_db() -> dict:
    reminders_list = []
    reminders_da_processare = 0
    reminders_da_aggiungere = 0
    reminders_cancellati = 0

    for reminder in Reminders.select():
        if reminder:
            if datetime.datetime.strptime(reminder.date_to_remind, "%d/%m/%Y %H:%M") < datetime.datetime.now():
                reminders_cancellati += 1
                deletequery = Reminders.delete().where(
                    (Reminders.chat_id == reminder.chat_id) & (Reminders.reply_id == reminder.reply_id)
                )
                deletequery.execute()

            else:
                r = {}
                r["message"] = reminder.message
                r["reply_id"] = reminder.reply_id
                r["user_id"] = reminder.user_id
                r["chat_id"] = reminder.chat_id
                r["date_now"] = datetime.datetime.strptime(reminder.date_now, "%d/%m/%Y %H:%M")
                r["date_to_remind"] = datetime.datetime.strptime(reminder.date_to_remind, "%d/%m/%Y %H:%M")
                reminders_da_aggiungere += 1
                reminders_list.append(r)
            reminders_da_processare += 1
    mydict = {
        "processed": reminders_da_processare,
        "to_add": reminders_da_aggiungere,
        "deleted": reminders_cancellati,
        "reminders": reminders_list,
    }
    return mydict


async def reply_html_long_message(update, context, message):
    if len(message) > 4000:
        lines = textwrap.wrap(message, 4000, break_long_words=False)
        for line in lines:
            await update.message.reply_html(line)
    else:
        await update.message.reply_html(message)


def get_user_settings(context, user_id=None) -> dict:
    if user_id:
        user_data = context.application.user_data[user_id]
    else:
        user_data = context.user_data
    # First time:
    if "user_settings" not in user_data:
        settings = user_default_settings()
        user_data["user_settings"] = settings
        
    # We check if the user has all the settings, otherwise we add them
    for k in config.DEFAULT_USER_SETTINGS:
        chiave = k["chiave"]
        valore = k["default"]
        if chiave not in user_data["user_settings"]:
            user_data["user_settings"][chiave] = valore
    context.application.mark_data_for_update_persistence(user_ids=[user_id])
    return user_data["user_settings"]


def user_default_settings() -> dict:
    s = {}
    for k in config.DEFAULT_USER_SETTINGS:
        chiave = k["chiave"]
        valore = k["default"]
        s[chiave] = valore
    # print(f"user_default_settings: {s}")
    return s
