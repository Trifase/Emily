import datetime
import inspect
from typing import Callable
import config
import io
import time


from rich import print
from telegram import Update, Bot, CallbackQuery, User, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from dataclassy import dataclass

@dataclass
class InlineButton:
    chat_id: int
    original_msg_id: int
    from_user_id: str
    callable: Callable
    original_update: Update = None
    vote: str



async def crea_sondaggino(context, update, max_votes, callable, domanda=''):
        current_votes = round(max_votes/2)

        if 'votazioni_attive' not in context.chat_data:
            context.chat_data['votazioni_attive'] = {}
        if domanda:
            domanda = f"{domanda}\n"
        context.chat_data['votazioni_attive'][update.effective_message.id] = {
                # 'callable': callable,
                'timestamp': int(time.time()),
                'domanda': domanda,
                'initiated_by': update.effective_user.id,
                'current_votes': current_votes,
                'max_votes': max_votes,
                'voters': []
            }


        keyboard = [
            [
                InlineKeyboardButton("✅", callback_data=InlineButton(chat_id=update.effective_chat.id, original_msg_id=update.effective_message.id, from_user_id=update.effective_user.id, original_update=update, callable=callable, vote='sì')),
                InlineKeyboardButton("❌", callback_data=InlineButton(chat_id=update.effective_chat.id, original_msg_id=update.effective_message.id, from_user_id=update.effective_user.id, original_update=update, callable=callable, vote='no'))
                ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        messaggio = f"<code>{domanda if domanda else ''}Conferme: {current_votes}/{max_votes}\n{print_progressbar(current_votes, max_votes, max_votes)}</code>"


        to_pin = await update.message.reply_html(messaggio, reply_markup=reply_markup)

        if update.effective_chat.id in [config.ID_ASPHALTO]:
            await to_pin.pin(disable_notification=True)
        return

def is_inline_button(callback_data):
    if isinstance(callback_data, InlineButton):
        return True
    return False

def get_now():
    return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

def function_name():
    
    # print(inspect.stack())
    func_name = inspect.stack()[2][3]
    # print(func_name)  # my_first_function
    return(func_name)

def is_function_enabled(chat_id, function, context):
    if chat_id > 0:  # è una chat privata.
        return True

    setting = function

    if "settings" not in context.chat_data:
        context.chat_data["settings"] = {}

    # print(f"Searching for: {function}")
    if function not in context.chat_data["settings"]:  # non è stata ancora inizializzata
        context.chat_data["settings"][function] = 'enabled'  # default è abilitata
        return True

    elif context.chat_data["settings"].get(function) == "enabled":  # è abilitata
        return True

    elif context.chat_data["settings"].get(function) == "disabled":  # è disabilitata
        return False

    return True  # richiesta malformata: abilitata

async def no_can_do(update, context):
    if "global_bans" not in context.bot_data:
        context.bot_data["global_bans"] = []
    one = update.effective_user.id in context.bot_data['global_bans']
    two = is_function_enabled(update.message.chat.id, function_name(), context)

    if one or not two:
        return True
    return False

async def get_chat_name(chat_id, tolog=False):
    bot = Bot(config.BOT_TOKEN)
    this_chat = await bot.get_chat(chat_id)

    if tolog:
        if this_chat.id > 0:
            return "chat privata"
        else:
            chat_title = this_chat.title
            return f"{chat_title} ({str(this_chat.id)})"


    if this_chat.id > 0:
        return "[deep_sky_blue1]chat privata[/deep_sky_blue1]"
    else:
        chat_title = this_chat.title.split(" ")[0]
        return f"[yellow1]{chat_title}[/yellow1] ({str(this_chat.id)[4:]})"

async def get_display_name(user: User, tolog=False):
    if tolog:
        if user.username:
            return f"{user.full_name} (@{user.username}) [{user.id}]"
        else:
            return f"{user.full_name} [{user.id}]"

    if user.username:
        return f"[deep_pink3]{user.full_name} (@{user.username})[/deep_pink3]"
    else:
        return f"[deep_pink3]{user.full_name}[/deep_pink3]"

async def is_user(update):
    if update.message.chat.type == "private":
        return True
    return False

async def printlog(update, action, additional_data=None):

    if isinstance(update, CallbackQuery):
        user = update.from_user
        chat_id = update.message.chat.id
    else:
        user = update.effective_user
        chat_id = update.effective_chat.id
    current_m = datetime.date.today().strftime("%Y-%m")
    if additional_data:
        print(f'{get_now()} {await get_display_name(user)} in {await get_chat_name(chat_id)} {action}: {additional_data}')
        with open(f'logs/{current_m}-logs.txt', 'a') as f:
             f.write(f"{get_now()} {await get_display_name(user, tolog=True)} in {await get_chat_name(chat_id, tolog=True)} {action}: {additional_data}\n")
    else:
        print(f'{get_now()} {await get_display_name(user)} in {await get_chat_name(chat_id)} {action}')
        with open(f'logs/{current_m}-logs.txt', 'a') as f:
             f.write(f"{get_now()} {await get_display_name(user, tolog=True)} in {await get_chat_name(chat_id, tolog=True)} {action}\n")


async def alert(update, context: CallbackContext, action, errore):

    if isinstance(update, CallbackQuery):
        user = update.from_user
        chat_id = update.message.chat.id
    else:
        user = update.effective_user
        chat_id = update.effective_chat.id

    messaggio = f'{get_now()} {await get_display_name(user, tolog=True)} in {await get_chat_name(chat_id, tolog=True)} {action}: {errore}'
    await context.bot.send_message(config.ID_TESTING, messaggio)

def print_progressbar(current_percentage, complete=100, max_length=20, fill_char="█", empty_char="░", prefix="[", suffix="]"):
    pct = int(current_percentage * max_length / complete)
    bar = prefix + fill_char * pct + empty_char * (max_length - pct) + suffix
    return bar

def expand(s):
    result = ''
    for ch in s:
        result = result + ch + ' '
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
