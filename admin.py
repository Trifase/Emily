from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat, ChatMember, ChatMemberUpdated
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.ext import CallbackContext, ContextTypes, Updater
from telegram.error import BadRequest

from typing import Optional, Tuple

import subprocess
import tempfile
import datetime
import asyncio

import config
from utils import printlog, get_display_name, print_to_string, get_now, get_chat_name, no_can_do, ForgeCommand
from scrapers import file_in_limits
from cron_jobs import do_global_backup
from rich import print
import sys
import os

# await printlog(update, "lancia una bombreact a", displayname)

async def flush_arbitrary_callback_data(update: Update, context: CallbackContext):
    if update.effective_user.id not in config.ADMINS:
        return
    await printlog(update, "flusha callback data e queries")
    context.bot.callback_data_cache.clear_callback_data()
    context.bot.callback_data_cache.clear_callback_queries()
    context.chat_data['votazioni_attive'] = {}
    await update.message.delete()
    return


async def check_temp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in config.ADMINS:
        return
    await printlog(update, "controlla la temperatura")
    mycommand = ["vcgencmd", "measure_temp"] 
    response = subprocess.run(mycommand, capture_output=True, encoding='utf-8')
    temp = response.stdout.split("=")[1].strip()[:-2]
    await update.message.reply_html(f"Temperatura interna: {temp}° C")


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

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tracks the chats the bot is in."""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return

    was_member, is_member = result

    # Let's check who is responsible for the change
    cause_name = update.effective_user.full_name
    cause_id = update.effective_user.id

    # Handle chat types differently:
    chat = update.effective_chat

    if chat.type == Chat.PRIVATE:
        if not was_member and is_member:
            print(f"{cause_name} started the bot.")
            context.bot_data.setdefault("user_ids", set()).add(chat.id)
        elif was_member and not is_member:
            print(f"{cause_name} ({cause_id}) blocked the bot.")
            context.bot_data.setdefault("user_ids", set()).discard(chat.id)
    elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            print(f"{cause_name} added the bot to the group {chat.title}")
            context.bot_data.setdefault("group_ids", set()).add(chat.id)
        elif was_member and not is_member:
            print(f"{cause_name} removed the bot from the group {chat.title}")
            context.bot_data.setdefault("group_ids", set()).discard(chat.id)
    else:
        if not was_member and is_member:
            print(f"{cause_name} added the bot to the channel {chat.title}")
            context.bot_data.setdefault("channel_ids", set()).add(chat.id)
        elif was_member and not is_member:
            print(f"{cause_name} removed the bot from the channel {chat.title}")
            context.bot_data.setdefault("channel_ids", set()).discard(chat.id)


async def show_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows which chats the bot is in"""

    user_ids = ", ".join(str(uid) for uid in context.bot_data.setdefault("user_ids", set()))
    group_ids = ", ".join(str(gid) for gid in context.bot_data.setdefault("group_ids", set()))
    channel_ids = ", ".join(str(cid) for cid in context.bot_data.setdefault("channel_ids", set()))
    text = (
        f"@{context.bot.username} is currently in a conversation with the user IDs {user_ids}."
        f" Moreover it is a member of the groups with IDs {group_ids} "
        f"and administrator in the channels with IDs {channel_ids}."
    )
    await update.effective_message.reply_text(text)


async def trigger_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMINS:
         return
    await printlog(update, "triggera un backup manuale")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} evoca eval')
    await do_global_backup(context)

async def _eval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMINS:
        return
    await printlog(update, "evoca eval")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} evoca eval')
    try:
        ret = eval(" ".join(context.args))
        await update.message.reply_html(f"<code>{print_to_string(ret)}</code>")
    except Exception as e:
        await update.message.reply_html(f"<code>{e}</code>")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async def shut_down_everything(app):
        args = sys.argv[:]
        args.insert(0, sys.executable)

        await app.stop()
        await app.shutdown()
        print(f'{get_now()} ### RIAVVIO IN CORSO ###')

        os.chdir(os.getcwd())
        os.execv(sys.executable, args)

    if update.effective_user.id not in config.ADMINS:
        return

    # if context.bot_data["gara_in_corso"]:
    #     await update.message.reply_text("Non posso farlo mentre una gara è in corso, mi dispiace.", quote=False)
    #     return

    if 'last_restart' not in context.bot_data:
        context.bot_data['last_restart'] = ""

    context.bot_data['last_restart'] = update.message.chat.id

    await printlog(update, "chiede di riavviare")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede di riavviare')

    # print(f"setting last_restart: {context.bot_data['last_restart']}")

    await update.message.reply_text(f'Provo a riavviarmi...')
    args = sys.argv[:]
    args.insert(0, sys.executable)

    print(f'{get_now()} ### RIAVVIO IN CORSO ###')
    raise SystemExit()


async def commandlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return
    message = ""
    c = 0
    import pprint
    for k, v in context.application.handlers.items():
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
            await update.message.reply_html(message[x:x + 4096])
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
        except Exception as e:
            pass



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
    import platform
    from os import walk
    from telegram import __version__ as TG_VER
    if update.message.from_user.id not in config.ADMINS:
        return

    filenames = next(walk("."), (None, None, []))[2]  # [] if no file
    lines = 0
    for file in filenames:
        if file.endswith(".py"):
            lines += sum(1 for line in open(file, "rb"))
    await update.message.reply_html(f"Emily <code>{config.VERSION}</code>\nUsing <code>python-telegram-bot v{TG_VER}</code> on Python <code>{platform.python_version()}</code>\nNumero totale di linee di codice: <code>{lines}</code>", quote=False)

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
        message = ' '.join(context.args[1:])
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
        exec(exec_str)
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
    text += f'chat_id: {chat_id}\n'
    text += f'user_id: {member.user.id}\n'
    text += f'first_name: {member.user.first_name}\n'
    text += f'last_name: {member.user.last_name}\n'
    text += f'username: {member.user.username}\n'
    text += f'is_bot: {member.user.is_bot}\n'
    text += f'status: {member.status}\n'
    # print(update.message.reply_to_message.__str__())
    # text += update.message.reply_to_message.effective_attachment
    if update.message.reply_to_message:
        if update.message.reply_to_message.animation:
            text += f"media type: animation\n"
            file_id = f"ID: <code>{update.message.reply_to_message.animation.file_id}</code>\n"
        elif update.message.reply_to_message.document:
            text += f"media type: document\n"
            file_id = f"ID: <code>{update.message.reply_to_message.document.file_id}</code>\n"
        elif update.message.reply_to_message.audio:
            text += f"media type: audio\n"
            file_id = f"ID: <code>{update.message.reply_to_message.audio.file_id}</code>\n"
        elif update.message.reply_to_message.photo:
            text += f"media type: photo\n"
            file_id = f"ID: <code>{update.message.reply_to_message.photo[-1].file_id}</code>\n"
        elif update.message.reply_to_message.sticker:
            text += f"media type: sticker\n"
            file_id = f"ID: <code>{update.message.reply_to_message.sticker.file_id}</code>\n"
        elif update.message.reply_to_message.video:
            text += f"media type: video\n"
            file_id = f"ID: <code>{update.message.reply_to_message.video.file_id}</code>\n"
        elif update.message.reply_to_message.voice:
            text += f"media type: voice\n"
            file_id = f"ID: <code>{update.message.reply_to_message.voice.file_id}</code>\n"
        elif update.message.reply_to_message.video_note:
            text += f"media type: video_note\n"
            file_id = f"ID: <code>{update.message.reply_to_message.video_note.file_id}</code>\n"

        try:
            if context.args[0] == "-raw":
                import pprint
                import json
                import html
                # pprint.pprint(update.message.__str__())
                import ast
                rawtext = pprint.pformat(update.message.to_dict())
                # print(rawtext)
                rawtext = html.escape(rawtext)
                if len(rawtext) > 4096:
                    for x in range(0, len(rawtext), 4096):
                        await update.message.reply_html(f'<pre>{rawtext[x:x + 4096]}</pre>')
                else:
                    await update.message.reply_html(f'<pre>{rawtext}</pre>')
                # pprint.pprint(ast.literal_eval(update.__str__()))
            elif context.args[0] == "-id":
                text += file_id
                await update.message.reply_html(text)
        except IndexError:
            await update.message.reply_html(text)

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
        except BadRequest as e:
            await context.bot.send_message(config.ID_SPIA, f"Mi dispiace: {e}")
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
        message += f"====\n"

        for admin in admins:
            message += f"{admin.status}: {admin.user.first_name} {admin.user.last_name} ({admin.user.id}) @{admin.user.username}\n"
    else:
        mychat = await context.bot.get_chat(chat_id)
        message += f"Utente di telegram\n"
        message += f"ID: {mychat.id}\n"
        message += f"Nome: {mychat.first_name} {mychat.last_name}\n"
        message += f"Nickname: @{mychat.username}\n"
        message += f"Descrizione: {mychat.bio}\n"


    cbdata_listen_to = ForgeCommand(original_update=update, new_text=f"/listen_to {chat_id}", new_args=[chat_id], callable=listen_to)
    cbdata_ban = ForgeCommand(original_update=update, new_text=f"/ban {chat_id}", new_args=[chat_id], callable=add_ban)

    keyboard = [
        [
            InlineKeyboardButton(f"{'Spia' if chat_id not in context.bot_data['listen_to'] else 'Non spiare'}", callback_data=cbdata_listen_to),
            InlineKeyboardButton(f"{'Banna' if chat_id not in context.bot_data['global_bans'] else 'Sbanna'}", callback_data=cbdata_ban)
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(config.ID_SPIA, message, reply_markup=reply_markup)


async def lista_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id not in config.ADMINS:
        return

    await printlog(update, "chiede la lista delle chat")
    # print("Lista delle chat")

    if "-wipe" in context.args:
        context.bot_data['lista_chat'] = []
        await update.message.reply_html("Fatto!")
        return

    if "-delete" in context.args:
        for chat_id in context.args[1:]:
            try:
                context.bot_data['lista_chat'].remove(int(chat_id))
            except ValueError:
                update.message.reply_html(f"{chat_id} non trovato")
        await update.message.reply_html("Fatto!")
        return

    if "-wipeusers" in context.args:
        for chat_id in context.bot_data['lista_chat'].copy():
            if chat_id > 0:
                context.bot_data['lista_chat'].remove(chat_id)
        await update.message.reply_html("Fatto!")
        return

    message = "\n"
    lista_ban = context.bot_data.get('global_bans', [])
    for chat_id in context.bot_data['lista_chat']:

        try:
            my_chat = await context.bot.get_chat(chat_id)
        except Exception as e: 
                context.bot_data['lista_chat'].remove(chat_id)
                continue

        if my_chat.type == 'private':
            is_banned = " "
            if chat_id in lista_ban:
                is_banned = f" [B] "

            username = ''
            if my_chat.username:
                username = f"@{my_chat.username} "

            message += f"👤{is_banned}ID: <code>{chat_id}</code> - {username}({my_chat.full_name})\n"  #[:15]

        else:
            username = ''
            if my_chat.username:
                username = f" (@{my_chat.username})"
            message = f"ID: <code>{chat_id}</code> - {my_chat.title}{username}\n" + message #[:15]

    await update.message.reply_html(message)

async def listen_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return

    try:
        if "-wipe" in context.args:
            context.bot_data['listen_to'] = []
            await update.message.reply_text(f"Smetto di spiare.")
            return
        else:
            chat_id = int(context.args[0])
            if chat_id in context.bot_data['listen_to']:
                context.bot_data['listen_to'].remove(chat_id)
                await update.message.reply_text(f"Non spio: {chat_id}")
            else:
                context.bot_data['listen_to'].append(chat_id)
                await update.message.reply_text(f"Spio: {chat_id}")
            return
    except IndexError:
        message = "\n"
        lista_ban = context.bot_data.get('global_bans', [])
        for chat_id in context.bot_data['listen_to']:
            my_chat = await context.bot.get_chat(chat_id)
            if chat_id < 0:
                try:
                    message = f"ID: <code>{chat_id}</code> - {my_chat.title}\n" + message #[:15]
                    # message += f"{chat_id} - {my_chat.title}\n"
                except Exception as e:
                    message = f"ID: <code>{chat_id}</code> - Nessun accesso\n" + message #[:15]
                    # message += f"{chat_id} - Nessun accesso\n"
            else:
                mychat = my_chat.to_dict()
                is_banned = " "
                if chat_id in lista_ban:
                    is_banned = f" [B] "
                message += f"👤{is_banned}ID: <code>{chat_id}</code> - @{mychat.get('username')} {mychat.get('first_name')} {mychat.get('last_name')}\n"
                # message += f"{chat_id} - @{my_chat.username} {my_chat.first_name} {my_chat.last_name}\n"
        message = "Sto spiando:\n" + message
        await context.bot.send_message(config.ID_SPIA, message, parse_mode=ParseMode.HTML)
        return


async def esci(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.ADMINS:
        return
    
    chatid = int(context.args[0])
    print(f'{get_now()} esce da {chatid}')
    if chatid in context.bot_data['lista_chat']:
        listachat = context.bot_data['lista_chat']
        listachat.remove(chatid)
        context.bot_data['lista_chat'] = listachat
        await update.message.reply_text("Key eliminata da lista_chat!", disable_notification=True)
    await context.bot.leave_chat(chatid)
    await update.message.reply_html("Fatto!", disable_notification=True)

async def ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    def get_ip():
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP
    if update.message.from_user.id not in config.ADMINS:
        return
    import urllib.request
    await printlog(update, "chiede gli indirizzi IP")
    local_ip = get_ip()
    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    await update.message.reply_text(f'IP Locale: {local_ip}\nIP Pubblico: {external_ip} o trifase.smelly.cc')

async def wakeup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.ADMINS:
        return
    await printlog(update, "accende il PC di casa")
    process = subprocess.Popen(
        ['sudo', 'etherwake', '-i', 'eth0', '18:C0:4D:86:AC:82'],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()

    if stdout:
        await update.message.reply_text(f'{stdout}')
    elif stderr:
        await update.message.reply_text(f'{stderr}')
    else: 
        await update.message.reply_text(f'Fatto')
    return


async def banlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.ADMINS:
        return
    await printlog(update, "chiede la lista bannati")

    message = ""
    if update.message.from_user.id not in config.ADMINS:
        return

    if "-wipe" in context.args:
        context.bot_data['global_bans'].clear()
        await update.message.reply_text(f"ban list vuota.")
        return
    lista_ban = context.bot_data.get('global_bans', [])
    if not lista_ban:
        context.bot_data['global_bans'] = []

    lista_ban = context.bot_data['global_bans'].copy()

    for user_id in lista_ban:
        try:
            user = await context.bot.getChat(user_id)
        except Exception as e:
            context.bot_data['global_bans'].remove(user_id)
            message += f"{user_id} - Cancellato\n"
            continue
        message += f"ID: {user['id']}\t @{user['username']}\n" 
    if not message:
        await update.message.reply_text("Lista ban vuota!", disable_notification=True)
        return
    else:
        await update.message.reply_html(f"<code>{message}</code>", disable_notification=True)
        return

async def add_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return
    # print(f'{get_now()} [deep_pink3]{update.message.from_user.username}[/deep_pink3] in {await get_chat_name(update.message.chat.id)} aggiunge un ban!')
    lista_ban = context.bot_data.get('global_bans', [])
    if not lista_ban:
        context.bot_data['global_bans'] = []

    if context.args:
        user_id = int(context.args[0])
        context.bot_data.get('global_bans').append(user_id)
    else:
        user_id = update.message.reply_to_message.from_user.id
        chat_id = update.message.chat.id
        member = await context.bot.get_chat_member(chat_id, user_id)
        context.bot_data.get('global_bans').append(member.user.id)
        user_id = member.user.id
    await printlog(update, "aggiunge alla lista ban", user_id)
    await update.message.reply_text("Fatto!", disable_notification=True)
    return

async def del_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} cancella un ban!')

    lista_ban = context.bot_data.get('global_bans', [])
    if not lista_ban:
        context.bot_data['global_bans'] = []
        lista_ban = context.bot_data.get('global_bans', [])

    if context.args:
        user_id = int(context.args[0])
        context.bot_data.get('global_bans').remove(user_id)
        await printlog(update, "rimuove un ban", user_id)
        await update.message.reply_text("Fatto!", disable_notification=True)
        return
    user_id = update.message.reply_to_message.from_user.id
    chat_id = update.message.chat.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.user.id in lista_ban:
        context.bot_data.get('global_bans').remove(member.user.id)
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
        await update.message.reply_text(f'Troppo lungo.', quote=False)
    else:
        await context.bot.set_chat_title(update.message.chat.id, title)

async def set_group_picture(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (update.message.from_user.id not in config.ADMINS or
        not update.message.reply_to_message or
        not update.message.reply_to_message.photo):
        return

    picture = update.message.reply_to_message.photo[-1]
    tempphoto = tempfile.mktemp(suffix='.jpg')
    actual_picture = await picture.get_file()
    await actual_picture.download_to_drive(custom_path=tempphoto)

    try:
        await context.bot.set_chat_photo(update.message.chat.id, open(tempphoto, 'rb'))
        await printlog(update, "cambia la propic al gruppo")
        # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} cambia la propic al gruppo')
    except Exception as e:
        await update.message.reply_text("Non posso farlo")

async def do_manual_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import shutil
    for filename in ['picklepersistence', 'sqlite.db', 'sets.json']:
        print(f"{get_now()} [AUTO] Eseguo il backup del file {filename}")
        oldfile = f"db/{filename}"
        newfile = f"db/backups/{datetime.datetime.today().strftime('%Y%m%d_%H%M%S')}-{filename}"
        shutil.copy(oldfile, newfile)
    print(f"{get_now()} [AUTO] Backup eseguito")
    update.message.reply_text("Fatto!")


