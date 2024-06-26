import datetime
import html
import platform
import pprint
import shutil
import socket
import subprocess
import tempfile
import traceback
import urllib.request
from os import walk

from PIL import ImageGrab
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram import __version__ as TG_VER
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import CallbackContext, ContextTypes
from telegram.error import Forbidden
import config
from cron_jobs import do_global_backup
from scrapers import file_in_limits
from utils import ForgeCommand, get_now, no_can_do, print_to_string, printlog


async def flush_arbitrary_callback_data(update: Update, context: CallbackContext):
    if update.effective_user.id not in config.ADMINS:
        return
    await printlog(update, "flusha callback data e queries")
    context.bot.callback_data_cache.clear_callback_data()
    context.bot.callback_data_cache.clear_callback_queries()
    context.chat_data["votazioni_attive"] = {}
    await update.message.delete()
    return


async def check_temp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in config.ADMINS:
        return
    await printlog(update, "controlla la temperatura")
    mycommand = ["vcgencmd", "measure_temp"]
    response = subprocess.run(mycommand, capture_output=True, encoding="utf-8")  # nosec
    temp = response.stdout.split("=")[1].strip()[:-2]
    await update.message.reply_html(f"Temperatura interna: {temp}° C")


async def trigger_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMINS:
        return
    await printlog(update, "triggera un backup manuale")
    await do_global_backup(context)


async def _eval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMINS:
        return
    await printlog(update, "evoca eval")
    try:
        ret = eval(" ".join(context.args))
        await update.message.reply_html(f"<code>{print_to_string(ret)}</code>")
    except Exception as e:
        await update.message.reply_html(f"<code>{e}</code>")


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMINS:
        return

    if "last_restart" not in context.bot_data:
        context.bot_data["last_restart"] = ""

    context.bot_data["last_restart"] = update.message.chat.id

    await printlog(update, "chiede di riavviare")

    await update.message.reply_text("Provo a riavviarmi...")

    print(f"{get_now()} ### RIAVVIO IN CORSO ###")

    context.application.stop_running()
    # raise SystemExit()


async def commandlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return
    message = ""
    c = 0
    for _, v in context.application.handlers.items():
        for h in v:
            if h.__class__.__name__ == "CommandHandler":
                funzione = h.callback.__name__
                mycommands = list(h.commands)
                if len(mycommands) == 1:
                    trigger = "/" + mycommands[0]

                elif len(mycommands) == 2:
                    trigger = f"/{mycommands[0]}, /{mycommands[1]}"

                else:
                    trigger = f"/{mycommands[0]}, /{mycommands[1]}, etc..."

                message += f"{trigger} → {funzione}()\n"
                c += 1

    message = f"{c} comandi trovati.\n\n{message}"

    if len(message) > 4096:
        for x in range(0, len(message), 4096):
            await update.message.reply_html(message[x : x + 4096])
    else:
        await update.message.reply_html(message)


async def cancella(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.ADMINS:
        return
    myself = await context.bot.get_chat_member(update.message.chat.id, config.ID_EMILY)
    if myself.status == ChatMemberStatus.ADMINISTRATOR and myself.can_delete_messages:
        await context.bot.delete_message(update.message.chat.id, update.message.message_id)
        if update.message.reply_to_message:
            await context.bot.delete_message(update.message.chat.id, update.message.reply_to_message.message_id)
    else:
        try:
            await context.bot.delete_message(update.message.chat.id, update.message.reply_to_message.message_id)
        except Forbidden:
            pass

async def clean_persistence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.ADMINS:
        return


    removed_users = 0
    removed_chats = 0
    for user_id in list(context.application.user_data.keys()):
        if not context.application.user_data[user_id]:
            context.application.drop_user_data(user_id)
            removed_users += 1


    for chat_id in list(context.application.chat_data.keys()):
        if not context.application.chat_data[chat_id]:
            context.application.drop_chat_data(chat_id)
            removed_chats += 1

    await printlog(update, f"Removed {removed_chats} chat_data and {removed_users} user_data keys")


async def send_custom_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.ADMINS:
        return
    if "video" not in context.args and "photo" not in context.args:
        await update.message.reply_html("Uso:\n<code>/send photo URL</code>\noppure\n<code>/send video URL</code>")
        return
    await printlog(update, "manda un media", f"\n{context.args[0]}\n{context.args[1]}")
    if "video" in context.args[0]:
        if file_in_limits(context.args[1]):
            await update.message.reply_video(video=context.args[1])
        else:
            await update.message.reply_text("Il file è oltre i limiti di caricamento da URL.")
    else:
        if file_in_limits(context.args[1]):
            await update.message.reply_photo(photo=context.args[1])
        else:
            await update.message.reply_text("Il file è oltre i limiti di caricamento da URL.")
    return


async def count_lines(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.ADMINS:
        return

    filenames = next(walk("."), (None, None, []))[2]  # [] if no file
    lines = 0
    for file in filenames:
        if file.endswith(".py"):
            lines += sum(1 for line in open(file, "rb"))
    await update.message.reply_html(
        f"Emily <code>{config.VERSION}</code>\nUsing <code>python-telegram-bot v{TG_VER}</code> on Python <code>{platform.python_version()}</code>\nNumero totale di linee di codice: <code>{lines}</code>",
        quote=False,
    )


async def parla(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    if update.message.from_user.id not in config.ADMINS:
        return
    await printlog(update, "mi fa parlare")
    if not context.args:
        return

    try:
        to_chat_id = context.args[0]
        message = " ".join(context.args[1:])
        await context.bot.send_message(to_chat_id, message)
    except Exception as e:
        await update.message.reply_text(f"{e}")


async def executecode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    if update.message.from_user.id not in config.ADMINS:
        return
    await printlog(update, "esegue del codice")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} esegue del codice!')

    try:
        exec_str = update.message.text[6:]
        exec(exec_str)  # nosec
        await update.message.reply_text("Fatto!")
    except Exception as e:
        await update.message.reply_text(f"{e}")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    if update.message.from_user.id not in config.ADMINS:
        return
    # print(update)
    commandlenght = update.message.entities[0].length + 1
    await update.message.reply_text(update.message.text[commandlenght:])


async def tg_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    if update.message.from_user.id not in config.ADMINS:
        return
    await printlog(update, "chiede info su un messaggio")
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
    else:
        user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    text = ""
    text += f"chat_id: {chat_id}\n"
    text += f"user_id: {member.user.id}\n"
    text += f"first_name: {member.user.first_name}\n"
    text += f"last_name: {member.user.last_name}\n"
    text += f"username: {member.user.username}\n"
    text += f"is_bot: {member.user.is_bot}\n"
    text += f"status: {member.status}\n"
    # print(update.message.reply_to_message.__str__())
    # text += update.message.reply_to_message.effective_attachment
    if update.message.reply_to_message:
        if update.message.reply_to_message.animation:
            text += "media type: animation\n"
            file_id = f"ID: <code>{update.message.reply_to_message.animation.file_id}</code>\n"
        elif update.message.reply_to_message.document:
            text += "media type: document\n"
            file_id = f"ID: <code>{update.message.reply_to_message.document.file_id}</code>\n"
        elif update.message.reply_to_message.audio:
            text += "media type: audio\n"
            file_id = f"ID: <code>{update.message.reply_to_message.audio.file_id}</code>\n"
        elif update.message.reply_to_message.photo:
            text += "media type: photo\n"
            file_id = f"ID: <code>{update.message.reply_to_message.photo[-1].file_id}</code>\n"
        elif update.message.reply_to_message.sticker:
            text += "media type: sticker\n"
            file_id = f"ID: <code>{update.message.reply_to_message.sticker.file_id}</code>\n"
        elif update.message.reply_to_message.video:
            text += "media type: video\n"
            file_id = f"ID: <code>{update.message.reply_to_message.video.file_id}</code>\n"
        elif update.message.reply_to_message.voice:
            text += "media type: voice\n"
            file_id = f"ID: <code>{update.message.reply_to_message.voice.file_id}</code>\n"
        elif update.message.reply_to_message.video_note:
            text += "media type: video_note\n"
            file_id = f"ID: <code>{update.message.reply_to_message.video_note.file_id}</code>\n"

        try:
            if context.args[0] == "-raw":
                # pprint.pprint(update.message.__str__())
                rawtext = pprint.pformat(update.message.reply_to_message.to_dict())
                rawtext = html.escape(rawtext)
                if len(rawtext) > 4096:
                    for x in range(0, len(rawtext), 4096):
                        await update.message.reply_html(
                            f'<pre><code class="language-python">{rawtext[x:x + 4096]}</code></pre>'
                        )
                else:
                    await update.message.reply_html(f'<pre><code class="language-python">{rawtext}</code></pre>')
            elif context.args[0] == "-rawfull":
                rawtext = pprint.pformat(update.to_dict())
                # print(rawtext)
                rawtext = html.escape(rawtext)
                if len(rawtext) > 4096:
                    for x in range(0, len(rawtext), 4096):
                        await update.message.reply_html(
                            f'<pre><code class="language-python">{rawtext[x:x + 4096]}</code></pre>'
                        )
                else:
                    await update.message.reply_html(f'<pre><code class="language-python">{rawtext}</code></pre>')
                # pprint.pprint(ast.literal_eval(update.__str__()))
            elif context.args[0] == "-id":
                text += file_id
                await update.message.reply_html(text)
        except IndexError:
            await update.message.reply_html(text)


async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return
    await printlog(update, "fa uno screenshot del raspi")
    im = ImageGrab.grab()
    tempphoto = tempfile.NamedTemporaryFile(suffix=".jpg")
    im.save(tempphoto.name, quality=100, subsampling=0)

    await update.message.reply_photo(photo=open(tempphoto.name, "rb"))
    await update.message.reply_document(document=open(tempphoto.name, "rb"))
    tempphoto.close()


async def getchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return
    await printlog(update, "chiede info su una chat")
    chat_id = int(context.args[0])

    message = ""
    if int(chat_id) < 0:
        try:
            mychat = await context.bot.get_chat(chat_id)
            admins: list = await context.bot.get_chat_administrators(chat_id)
            utenti = await context.bot.get_chat_member_count(chat_id)
        except Exception as e:
            await context.bot.send_message(config.ID_BOTCENTRAL, f"Mi dispiace: {e}")
            return

        # print(mychat.to_dict())

        message += f"ID: {mychat.id}\n"
        message += f"Nome: {mychat.title}\n"
        message += f"Tipo: {mychat.type}\n"
        message += f"Descrizione: {mychat.description}\n"
        message += f"Utenti: {utenti}\n"
        message += f"Invite Link: {mychat.invite_link}\n"
        if mychat.username:
            message += f"Username: @{mychat.username}\n"
        if mychat.linked_chat_id:
            message += f"Linked chat: {mychat.linked_chat_id}\n"
        message += "====\n"

        for admin in admins:
            message += f"{admin.status}: {admin.user.first_name} {admin.user.last_name} ({admin.user.id}) @{admin.user.username}\n"
    else:
        mychat = await context.bot.get_chat(chat_id)
        message += "Utente di telegram\n"
        message += f"ID: {mychat.id}\n"
        message += f"Nome: {mychat.first_name} {mychat.last_name}\n"
        message += f"Nickname: @{mychat.username}\n"
        message += f"Descrizione: {mychat.bio}\n"

    cbdata_listen_to = ForgeCommand(
        original_update=update, new_text=f"/listen_to {chat_id}", new_args=[chat_id], callable=listen_to
    )
    cbdata_ban = ForgeCommand(original_update=update, new_text=f"/ban {chat_id}", new_args=[chat_id], callable=add_ban)

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'Spia' if chat_id not in context.bot_data['listen_to'] else 'Non spiare'}",
                callback_data=cbdata_listen_to,
            ),
            InlineKeyboardButton(
                f"{'Banna' if chat_id not in context.bot_data['global_bans'] else 'Sbanna'}", callback_data=cbdata_ban
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(config.ID_BOTCENTRAL, message, reply_markup=reply_markup)


async def lista_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return

    await printlog(update, "chiede la lista delle chat")
    # print("Lista delle chat")

    if "-wipe" in context.args:
        context.bot_data["lista_chat"] = []
        await update.message.reply_html("Fatto!")
        return

    if "-delete" in context.args:
        for chat_id in context.args[1:]:
            try:
                context.bot_data["lista_chat"].remove(int(chat_id))
            except ValueError:
                await update.message.reply_html(f"{chat_id} non trovato")
        await update.message.reply_html("Fatto!")
        return

    if "-wipeusers" in context.args:
        for chat_id in context.bot_data["lista_chat"].copy():
            if chat_id > 0:
                context.bot_data["lista_chat"].remove(chat_id)
        await update.message.reply_html("Fatto!")
        return

    message = "\n"
    lista_ban = context.bot_data.get("global_bans", [])
    for chat_id in context.bot_data["lista_chat"]:
        try:
            my_chat = await context.bot.get_chat(chat_id)
        except Exception:
            context.bot_data["lista_chat"].remove(chat_id)
            continue

        if my_chat.type == "private":
            is_banned = " "
            if chat_id in lista_ban:
                is_banned = " [B] "

            username = ""
            if my_chat.username:
                username = f"@{my_chat.username} "

            message += f"👤{is_banned}ID: <code>{chat_id}</code> - {username}({my_chat.full_name})\n"  # [:15]

        else:
            username = ""
            if my_chat.username:
                username = f" (@{my_chat.username})"
            message = f"ID: <code>{chat_id}</code> - {my_chat.title}{username}\n" + message  # [:15]

    try:
        await update.message.reply_html(message)
    except Exception as e:
        print(message)
        print(e)


async def listen_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return

    try:
        if "-wipe" in context.args:
            context.bot_data["listen_to"] = []
            await update.message.reply_text("Smetto di spiare.")
            return
        else:
            chat_id = int(context.args[0])
            if chat_id in context.bot_data["listen_to"]:
                context.bot_data["listen_to"].remove(chat_id)
                await update.message.reply_text(f"Non spio: {chat_id}")
            else:
                context.bot_data["listen_to"].append(chat_id)
                await update.message.reply_text(f"Spio: {chat_id}")
            return
    except IndexError:
        message = "\n"
        lista_ban = context.bot_data.get("global_bans", [])
        for chat_id in context.bot_data["listen_to"]:
            my_chat = await context.bot.get_chat(chat_id)
            if chat_id < 0:
                try:
                    message = f"ID: <code>{chat_id}</code> - {my_chat.title}\n" + message  # [:15]
                    # message += f"{chat_id} - {my_chat.title}\n"
                except Exception:
                    message = f"ID: <code>{chat_id}</code> - Nessun accesso\n" + message  # [:15]
                    # message += f"{chat_id} - Nessun accesso\n"
            else:
                mychat = my_chat.to_dict()
                is_banned = " "
                if chat_id in lista_ban:
                    is_banned = " [B] "
                message += f"👤{is_banned}ID: <code>{chat_id}</code> - @{mychat.get('username')} {mychat.get('first_name')} {mychat.get('last_name')}\n"
                # message += f"{chat_id} - @{my_chat.username} {my_chat.first_name} {my_chat.last_name}\n"
        message = "Sto spiando:\n" + message
        await context.bot.send_message(config.ID_BOTCENTRAL, message, parse_mode=ParseMode.HTML)
        return


async def esci(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.ADMINS:
        return

    chatid = int(context.args[0])
    print(f"{get_now()} esce da {chatid}")
    if chatid in context.bot_data["lista_chat"]:
        listachat = context.bot_data["lista_chat"]
        listachat.remove(chatid)
        context.bot_data["lista_chat"] = listachat
        await update.message.reply_text("Key eliminata da lista_chat!", disable_notification=True)
    await context.bot.leave_chat(chatid)
    await update.message.reply_html("Fatto!", disable_notification=True)


async def ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(("10.255.255.255", 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = "127.0.0.1"
        finally:
            s.close()
        return IP

    if update.message.from_user.id not in config.ADMINS:
        return

    await printlog(update, "chiede gli indirizzi IP")
    local_ip = get_ip()
    external_ip = urllib.request.urlopen("https://ident.me").read().decode("utf8")  # nosec
    await update.message.reply_text(f"IP Locale: {local_ip}\nIP Pubblico: {external_ip} o trifase.online")


async def wakeup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.ADMINS:
        return
    await printlog(update, "accende il PC di casa")
    process = subprocess.Popen(  # nosec
        ["sudo", "etherwake", "-i", "eth0", "18:C0:4D:86:AC:82"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()

    if stdout:
        await update.message.reply_text(f"{stdout}")
    elif stderr:
        await update.message.reply_text(f"{stderr}")
    else:
        await update.message.reply_text("Fatto")
    return


async def banlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.ADMINS:
        return
    await printlog(update, "chiede la lista bannati")

    if "global_bans" not in context.bot_data:
        context.bot_data["global_bans"] = []

    message = ""
    if update.message.from_user.id not in config.ADMINS:
        return

    if "-wipe" in context.args:
        context.bot_data["global_bans"].clear()
        await update.message.reply_text("ban list vuota.")
        return

    if "-removeduplicates" in context.args:
        context.bot_data["global_bans"] = list(set(context.bot_data["global_bans"]))
        await update.message.reply_text("Fatto.")
        return

    lista_ban = context.bot_data["global_bans"].copy()

    for user_id in lista_ban:
        try:
            chat = await context.bot.get_chat(user_id)

        except Exception:
            context.bot_data["global_bans"].remove(user_id)
            message += f"ID: <code>{user_id}</code> - Cancellato\n"
            continue

        if chat.type == "private":
            if chat.username:
                message += f"ID: <code>{chat.id}</code> - <code>{chat.full_name} (@{chat.username})</code>\n"
            else:
                message += f"ID: <code>{chat.id}</code> - <code>{chat.full_name}</code>\n"
        else:
            if chat.username:
                message += f"ID: <code>{chat.id}</code> - <code>{chat.title} (@{chat.username})</code>\n"
            else:
                message += f"ID: <code>{chat.id}</code> - <code>{chat.title}</code>\n"

    if not message:
        await update.message.reply_text("Lista ban vuota!", disable_notification=True)
        return
    else:
        await update.message.reply_html(f"{message}", disable_notification=True)
        return


async def add_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return

    lista_ban = context.bot_data.get("global_bans", [])
    if not lista_ban:
        context.bot_data["global_bans"] = []

    if context.args:
        user_id = int(context.args[0])
    elif update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
    else:
        await update.message.reply_text("Non saprei chi bannare")
        return
    if user_id not in lista_ban:
        context.bot_data.get("global_bans").append(user_id)
        await update.message.reply_text("Fatto!", disable_notification=True)
        await printlog(update, "aggiunge alla lista ban", user_id)
    else:
        await update.message.reply_text("È già bannato", disable_notification=True)


async def del_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} cancella un ban!')

    lista_ban = context.bot_data.get("global_bans", [])
    if not lista_ban:
        context.bot_data["global_bans"] = []
        lista_ban = context.bot_data.get("global_bans", [])

    if context.args:
        user_id = int(context.args[0])
        context.bot_data.get("global_bans").remove(user_id)
        await printlog(update, "rimuove un ban", user_id)
        await update.message.reply_text("Fatto!", disable_notification=True)
        return
    user_id = update.message.reply_to_message.from_user.id
    chat_id = update.message.chat.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.user.id in lista_ban:
        context.bot_data.get("global_bans").remove(member.user.id)
        await printlog(update, "rimuove un ban", member.user.id)
        await update.message.reply_text("Fatto!", disable_notification=True)
    else:
        await update.message.reply_text("Non mi sembra bannato.", disable_notification=True)
    return


async def set_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.ADMINS:
        return

    if not context.args:
        await update.message.reply_text("Devi inserire un titolo!", disable_notification=True)
        return
    title = " ".join(context.args)
    await printlog(update, "cambia titolo", title)
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} imposta il nome {title}')
    if 0 > len(title) > 255:
        await update.message.reply_text("Troppo lungo.", quote=False)
    else:
        await context.bot.set_chat_title(update.message.chat.id, title)


async def set_group_picture(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (
        update.message.from_user.id not in config.ADMINS
        or not update.message.reply_to_message
        or not update.message.reply_to_message.photo
    ):
        return

    picture = update.message.reply_to_message.photo[-1]

    with tempfile.NamedTemporaryFile(suffix=".jpg") as tempphoto:
        actual_picture = await picture.get_file()
        await actual_picture.download_to_drive(custom_path=tempphoto.name)

        try:
            await context.bot.set_chat_photo(update.message.chat.id, tempphoto)
            await printlog(update, "cambia la propic al gruppo")

        except Exception:
            print(traceback.format_exc())
            await update.message.reply_text("Non posso farlo")


async def do_manual_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for filename in ["picklepersistence", "sqlite.db", "sets.json"]:
        print(f"{get_now()} [AUTO] Eseguo il backup del file {filename}")
        oldfile = f"db/{filename}"
        newfile = f"db/backups/{datetime.datetime.today().strftime('%Y%m%d_%H%M%S')}-{filename}"
        shutil.copy(oldfile, newfile)
    print(f"{get_now()} [AUTO] Backup eseguito")
    await update.message.reply_text("Fatto!")


async def clean_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return
    user_ids = set()
    chat_ids = set()

    # ====== CHAT DATA ======
    chat_data_remove = ["jackpot", "highest_wins", "count", "votazioni_attive"]
    whitelist_chats = [config.ID_ASPHALTO, config.ID_DIOCHAN, config.ID_TIMELINE]
    for chat, chat_value in list(context.application.chat_data.items()):
        chat_ids.add(chat)
        # remove all chat except whitelist
        if chat not in whitelist_chats:
            print(f'Removing chat_data: {chat} - not in whitelist')
            context.application.drop_chat_data(chat)
            # chat_ids.add(chat)
            continue

        # remove empty keys
        if not chat_value:
            print(f'Removing empty chat_data: {chat}')
            context.application.drop_chat_data(chat)
            # chat_ids.add(chat)
            continue

        # remove empty subkeys
        for c_subkey, c_subvalue in list(chat_value.items()):
            if not c_subvalue:
                print(f"Removing {c_subkey} from {chat}: empty")
                context.application.chat_data[chat].pop(c_subkey, None)
                chat_ids.add(chat)

        # remove chat_data_remove
        for c_k in chat_data_remove:
            if c_k in context.application.chat_data[chat]:
                print(f"Removing {c_k} from {chat}: blacklist")
                del context.application.chat_data[chat][c_k]
                chat_ids.add(chat)

        if 'stats' in context.application.chat_data[chat]:
            for day in list(context.application.chat_data[chat]['stats'].keys()):
                # if day YYYY-MM-DD is earlier than 30 days ago
                try:
                    if datetime.datetime.strptime(day, "%Y-%m-%d") < datetime.datetime.today() - datetime.timedelta(days=30):
                        print(f"Key: {chat} | {day} from stats is older than 30 days, removing it")
                        context.application.chat_data[chat]['stats'].pop(day, None)
                        chat_ids.add(chat)
                except ValueError: 
                    pass

    context.application.drop_chat_data(-1001180175690)
    await update.message.reply_text("chat_data pulito!")

    # ====== USER DATA ======
    user_data_remove = [
        'time_indovina',
        'balance',
        'time_scommessa',
        'time_slot',
        'soldi_gratis',
        'time_bowling',
        'ippodromo',
        'lavoro',
        'banca',
        'prelievo_banca',
        'perfavore',
        'time_dado',
        'triviapoints',
        'trivia_points_new',
        'trivia_wrongs',
        'time_cloud_me'
    ]
    user_data_whitelist = [
        'user_settings',
        'default_meteo_city',
        'segno_zodiacale',
        'last_use_ai'
    ]
    for user, user_value in list(context.application.user_data.items()):
        user_ids.add(user)
        # remove empty keys
        if not user_value:
            print(f'Removing empty user_data: {user}')
            context.application.drop_user_data(user)
            user_ids.add(user)
            continue

        # remove empty subkeys
        for u_subkey, u_subvalue in list(user_value.items()):
            if not u_subvalue:
                print(f"Removing {u_subkey} from {user}: empty")
                context.application.user_data[user].pop(u_subkey, None)
                user_ids.add(user)

        # # remove chat_data_remove
        # for u_k in user_data_remove:
        #     context.application.user_data[user].pop(u_k, None)
        for k in list(context.application.user_data[user].keys()):
            if k not in user_data_whitelist:
                print(f"Removing {k} from {user}: not in whitelist")
                context.application.user_data[user].pop(k, None)
                user_ids.add(user)


        # check if all the keys in context.application.user_data[user] are in user_data_remove
        if not set(context.application.user_data[user].keys()).difference(set(user_data_remove)):
            print(f'Removing user_data: {user} - all keys in blacklist')
            context.application.drop_user_data(user)
            user_ids.add(user)
            continue
        else:
            for k in user_data_remove:
                if k in context.application.user_data[user]:
                    print(f"Removing {k} from {user}: blacklist")
                    del context.application.user_data[user][k]
                    user_ids.add(user)
    
        if 'user_settings' in context.application.user_data[user]:
            if 'default_meteo_city' in context.application.user_data[user]:
                context.application.user_data[user]['user_settings']['prometeo_city'] = context.application.user_data[user]['default_meteo_city']
                del context.application.user_data[user]['default_meteo_city']
                user_ids.add(user)

            if 'segno_zodiacale' in context.application.user_data[user]:
                context.application.user_data[user]['user_settings']['segno_zodiacale'] = context.application.user_data[user]['segno_zodiacale']
                del context.application.user_data[user]['segno_zodiacale']
                user_ids.add(user)

    await update.message.reply_text("user_data pulito!")

    # ====== BOT DATA ======
    # print(context.application.bot_data)
    bot_data_remove = [
        "cavalli_esistenti",
        "gara_in_corso",
        "odds_list",
        "scommesse_aperte",
        "scommesse_ippodromo",
        "scommesse_emily",
        "asph_timestamps",
        "user_ids",
        "channel_ids",
        "group_ids",
    ]

    for chiave in bot_data_remove:
        if chiave in context.application.bot_data:
            print(f"Removing {chiave} from bot_data: blacklist")
            context.application.bot_data.pop(chiave, None)

    # context.application.bot_data['trivia'] = {}
    # context.application.bot_data['listen_to'] = []
    # context.application.bot_data['global_bans'] = []
    # context.application.bot_data['lista_chat'] = []
    # context.application.bot_data['timestamps'].pop(-1001406546688, None)
    # context.application.bot_data.pop('metaverso', None)
    # context.application.bot_data.pop('quiz_in_corso', None)

    await update.message.reply_text("bot_data pulito!")
    context.application.mark_data_for_update_persistence(chat_ids=chat_ids, user_ids=user_ids)
