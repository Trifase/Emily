import warnings
warnings.filterwarnings("ignore")

import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ApplicationHandlerStop

import config

from admin import getchat, lista_chat, listen_to, add_ban
from smarthome import toggle_light, get_light_label
from utils import printlog, no_can_do, is_member_in_group, is_user, ForgeCommand


async def drop_update_from_banned_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        raise ApplicationHandlerStop

async def exit_from_banned_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Auto exit on banned groups
    chat_id = int(update.effective_chat.id)

    if chat_id in config.BANNED_GROUPS:
        await context.bot.leave_chat(chat_id)

async def nuova_chat_rilevata(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'lista_chat' not in context.bot_data:
        context.bot_data['lista_chat'] = []

    if "listen_to" not in context.bot_data:
        context.bot_data['listen_to'] = []

    chat_id = int(update.effective_chat.id)
    SPY = True

    # Se non è in lista chat, invio un sommario su emily spia
    if chat_id not in context.bot_data['lista_chat']:
        context.bot_data['lista_chat'].append(chat_id)
        is_presente = await is_member_in_group(config.ID_TRIF, chat_id, context)
        if chat_id < 0 and chat_id not in context.bot_data['listen_to'] and SPY:

            
            if not is_presente:
                context.bot_data['listen_to'].append(chat_id)
            else:
                pass
                
        elif chat_id not in context.bot_data['listen_to'] and SPY:
            context.bot_data['listen_to'].append(chat_id)

        if not await is_user(update):
            
            message = ""
            mychat = await context.bot.get_chat(chat_id)
            utenti = await context.bot.get_chat_member_count(chat_id)

            if chat_id in context.bot_data['listen_to']:
                message += "Nuova chat di gruppo rilevata! (Spio)\n\n"

            else:
                message += "Nuova chat di gruppo rilevata! (Non spio)\n\n"

            message += f"<b>Nome: {mychat.title}</b>\n"
            message += f"ID: <code>{mychat.id}</code>\n"
            message += f"Tipo: {mychat.type}\n"
            message += f"Utenti: {utenti}\n"
            message += f"Invite Link: {mychat.invite_link}\n"
            message += f"Descrizione:\n{mychat.description}\n\n"

            message += f"Messaggio: {update.effective_user.mention_html()}: {update.effective_message.text}"

        else:
            message = ""
            utente = await context.bot.get_chat(chat_id)
            if chat_id in context.bot_data['listen_to']:
                message += "Nuova chat utente rilevata! (Spio)\n\n"
            else:
                message += "Nuova chat utente rilevata! (Non spio)\n\n"
            message += f"Nome: {utente.first_name} {utente.last_name}\n"
            message += f"Nickname: @{utente.username}\n"
            message += f"ID: <code>{utente.id}</code>\n"
            message += f"Bio: {utente.bio}\n\n"
            message += f"Messaggio: {update.effective_user.mention_html()}: {update.effective_message.text}"

        cbdata_listen_to = ForgeCommand(original_update=update, new_text=f"/listen_to {chat_id}", new_args=[chat_id], callable=listen_to)
        cbdata_getchat = ForgeCommand(original_update=update, new_text=f"/getchat {chat_id}", new_args=[chat_id], callable=getchat)
        cbdata_ban = ForgeCommand(original_update=update, new_text=f"/ban {chat_id}", new_args=[chat_id], callable=add_ban)
        cbdata_delete = ForgeCommand(original_update=update, new_text=f"/listachat -delete {chat_id}", new_args=['-delete', chat_id], callable=lista_chat)

        keyboard = [
            [
                InlineKeyboardButton(f"{'🔊 Spia' if chat_id not in context.bot_data['listen_to'] else '🔇 Non spiare'}", callback_data=cbdata_listen_to),
                InlineKeyboardButton("ℹ️ Info", callback_data=cbdata_getchat)
            ],
            [
                InlineKeyboardButton("🚫 Banna", callback_data=cbdata_ban),
                InlineKeyboardButton("🗑 Del chatlist", callback_data=cbdata_delete),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(config.ID_SPIA, message, reply_markup=reply_markup)

    # Se è nella lista spiati, inoltra il messaggio su emily spia
    if chat_id in context.bot_data['listen_to']:
        my_chat = await context.bot.get_chat(chat_id)
        msg_from = "👤 chat privata"
        if my_chat.title:
            msg_from = f"💬 {my_chat.title}"
        text = f"[SPIO] Messaggio su {msg_from}:\nID: <code>{my_chat.id}</code>\n{update.effective_user.mention_html()}: {update.effective_message.text}"
    
        cbdata_listen_to = ForgeCommand(original_update=update, new_text=f"/listen_to {chat_id}", new_args=[chat_id], callable=listen_to)
        cbdata_getchat = ForgeCommand(original_update=update, new_text=f"/getchat {chat_id}", new_args=[chat_id], callable=getchat)
        cbdata_ban = ForgeCommand(original_update=update, new_text=f"/ban {chat_id}", new_args=[chat_id], callable=add_ban)
        cbdata_delete = ForgeCommand(original_update=update, new_text=f"/listachat -delete {chat_id}", new_args=['-delete', chat_id], callable=lista_chat)

        keyboard = [
            [
                InlineKeyboardButton(f"{'🔊 Spia' if chat_id not in context.bot_data['listen_to'] else '🔇 Non spiare'}", callback_data=cbdata_listen_to),
                InlineKeyboardButton("ℹ️ Info", callback_data=cbdata_getchat)
            ],
            [
                InlineKeyboardButton("🚫 Banna", callback_data=cbdata_ban),
                InlineKeyboardButton("🗑 Del chatlist", callback_data=cbdata_delete),
            ]
        ]



        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=config.ID_SPIA, text=text, reply_markup=reply_markup)

async def update_timestamps_asphalto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    chat_id = int(update.effective_chat.id)

    # Timestamp per asphalto
    if chat_id == config.ID_ASPHALTO:
        if 'timestamps' not in context.bot_data:
            context.bot_data['timestamps'] = {}
        if chat_id not in context.bot_data['timestamps']:
            context.bot_data['timestamps'][chat_id] = {}

        if update.effective_user:
            user_id = int(update.effective_user.id)
            context.bot_data['timestamps'][chat_id][user_id] = int(time.time())

async def check_for_sets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    chat_id = int(update.effective_chat.id)

    # I messaggi privati vengono ignorati.
    if update.message.chat.type == "private":
        return

    # Sets
    # with open('db/sets.json') as sets_db:
    #     sets = json.load(sets_db)
    if 'current_sets' not in context.bot_data:
        context.bot_data['current_sets'] = {}

    sets = context.bot_data['current_sets']
    chat_id = str(update.message.chat.id)
    messaggio = update.effective_message.text

    if chat_id not in sets:
        sets[chat_id] = {}
    chatdict = sets[chat_id]
    if messaggio.lower().endswith('@emilia_superbot'):
        messaggio = messaggio[:-16]

    if messaggio.lower() in chatdict:
        # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} triggera {messaggio}')
        await printlog(update, "triggera", messaggio)
        set_text: str = chatdict[messaggio.lower()]
        is_reply = False
        if update.message.reply_to_message:
            is_reply = True
            reply_id = update.message.reply_to_message.message_id
        if set_text.startswith('media:'):  # 'media:media_type:media_id'
            media_type = set_text.split(':')[1]
            media_id = set_text.split(':')[2]
            try:
                if media_type == "photo":
                    if is_reply:
                        await context.bot.send_photo(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_photo(chat_id, media_id)
                elif media_type == "video":
                    if is_reply:
                        await context.bot.send_video(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_video(chat_id, media_id)
                elif media_type == "sticker":
                    if is_reply:
                        await context.bot.send_sticker(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_sticker(chat_id, media_id)
                elif media_type == "audio":
                    if is_reply:
                        await context.bot.send_audio(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_audio(chat_id, media_id)
                elif media_type == "voice":
                    if is_reply:
                        await context.bot.send_voice(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_voice(chat_id, media_id)
                elif media_type == "document":
                    if is_reply:
                        await context.bot.send_document(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_document(chat_id, media_id)
                elif media_type == "animation":
                    if is_reply:
                        await context.bot.send_animation(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_animation(chat_id, media_id)
                elif media_type == "video_note":
                    if is_reply:
                        await context.bot.send_video_note(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_video_note(chat_id, media_id)
                else:
                    await update.message.reply_text("Tipo di media non riconosciuto")
                return
            except Exception as e:
                await update.message.reply_html(f'<b>Errore:</b> {e}')
                return
        else:
            if is_reply:
                await update.message.reply_text(f'{chatdict[messaggio.lower()]}', quote=False, disable_web_page_preview=True, reply_to_message_id=reply_id)
            else:
                await update.message.reply_text(f'{chatdict[messaggio.lower()]}', quote=False, disable_web_page_preview=True)
            return

# async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

#     query = update.callback_query
#     await query.answer()

#     # Example of update.callback_query.data it receives:
#     # cmd:ban:123456789

#     # splitting the string into command and args
#     command = query.data.split(":")[1]
#     args = query.data.split(":")[2]

#     # becase v20b makes TelegramObjects frozen (as in: Immutable), we need to warm up them a bit before 
#     # we can edit them - there is an internal context manager ready that unfreezes and freezes on exit

#     query._unfreeze()
#     query.message._unfreeze()

#     # forging a fake message.text
#     query.message.text = f"/{command} {args}"

#     # creating an empty context.args
#     if not context.args:
#         context.args = []

#     # forging a fake context.args
#     for arg in args.split(" "):
#         context.args.append(arg)

#     # calling actual functions with the forged callback_query and forged context
#     # add_ban is the same function that would be called by /add_ban <user_id>
#     if command == 'toggle':
#         if query.from_user.id not in config.ADMINS:
#             await query.answer(f"Non puoi.")
#             return

#         await toggle_light(update.callback_query, context)
#         bulbs = ["salotto", "pranzo", "cucina", "penisola"]

#         luci_keyb = [
#             [
#                 InlineKeyboardButton(f"{get_light_label(bulbs[0])}", callback_data=f"cmd:toggle:{bulbs[0]}"),
#                 InlineKeyboardButton(f"{get_light_label(bulbs[1])}", callback_data=f"cmd:toggle:{bulbs[1]}"),
#             ],
#             [
#                 InlineKeyboardButton(f"{get_light_label(bulbs[2])}", callback_data=f"cmd:toggle:{bulbs[2]}"),
#                 InlineKeyboardButton(f"{get_light_label(bulbs[3])}", callback_data=f"cmd:toggle:{bulbs[3]}"),
#             ]
#         ]

#         reply_markup = InlineKeyboardMarkup(luci_keyb)
#         await query.message.edit_text("Luci:", reply_markup=reply_markup)

async def new_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    await query.answer()
    mybutton: ForgeCommand = query.data

    query._unfreeze()
    query.message._unfreeze()

    query.message.text = mybutton.new_text
    context.args = mybutton.new_args
    function_to_call = mybutton.callable

    await function_to_call(query, context)
