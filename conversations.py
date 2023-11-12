from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest as TGBardRequest
from telegram.ext import ContextTypes, ConversationHandler

import config
from utils import get_user_settings, no_can_do, printlog

# Settings menu
#    h[-21] = [ConversationHandler(
#        entry_points=[CommandHandler("settings", settings, filters=~filters.UpdateType.EDITED)],
#        states={
#            "WAIT_FOR_SETTING": [CallbackQueryHandler(settings_change_show, pattern="^sett:")],
#            "CHANGE_SETTING": [MessageHandler(~filters.UpdateType.EDITED & filters.TEXT, settings_change_actual)],
#            -2 : [
#                TypeHandler(Update, end_conversation)
#            ]
#        },
#        fallbacks=[],
#        conversation_timeout=30)
#        ]

# L'utente fa /settings
# : se è con gli argomenti chiave e valore, setto il setting e finisce la conv.
# : se è senza argomenti, mando la lista di bottoni con payload sett:NOMESETTING, più un bottone con sett:CANCELLA e mi metto su stato WAIT_FOR_SETTING
# stato WAIT_FOR_SETTING:
# : se premo sett:CANCELLA finisce la conv
# : se premo sett:NOMESETTING, gli mando un messaggio in cui gli scrivo le impostazioni di default e la descrizione del setting, e mi metto su stato CHANGE_SETTING
# stato CHANGE_SETTING:
# : se l'utente scrive annulla, finisce la conv
# : se l'utente scrive un valore, lo setto a NOMESETTING e rimando la lista di bottoni con payload sett:NOMESETTING, più un bottone con sett:CANCELLA e mi rimetto su stato WAIT_FOR_SETTING

# timeout a 30secondi con conversation end


# ENTRY POINT
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    await printlog(update, "controlla le impostazioni")

    if "-help" in context.args:
        message = "<code>/settings</code> per vedere e cambiare i settings personali;\n<code>/settings [chiave] [valore]</code> per impostare una chiave direttamente."
        await update.message.reply_html(message, quote=False, allow_sending_without_reply=True)
        context.user_data.pop("conversation_settings", None)
        return ConversationHandler.END
    try:
        await update.message.delete()
    except TGBardRequest:
        pass
    user_settings = get_user_settings(context)

    if not context.args:
        bottoni = []
        all_settings = config.DEFAULT_USER_SETTINGS

        for sett in all_settings:
            bottoni.append(
                [
                    InlineKeyboardButton(
                        f"{sett['label']}: {user_settings[sett['chiave']]}", callback_data=f"sett:{sett['chiave']}"
                    )
                ]
            )
        bottoni.append([InlineKeyboardButton("Annulla", callback_data="sett:annulla")])

        reply_markup = InlineKeyboardMarkup(bottoni)

        messaggio = "Ecco le tua impostazioni attuali!\nClicca su un pulsante per cambiare valore, oppure su [Annulla] per uscire."
        await update.message.reply_html(messaggio, reply_markup=reply_markup)
        context.user_data["conversation_settings"] = {}
        return "WAIT_FOR_SETTING"

    elif len(context.args) == 2:
        message = ""
        key = context.args[0]
        value = context.args[1]

        if key in user_settings:
            message += f"Impostazione attuale di <code>{key}</code> = <code>'{user_settings[key]}'</code>\n"
            message += f"Cambio <code>{key}</code> in <code>'{value}'</code>"
            user_settings[key] = value
            context.user_data["user_settings"] = user_settings
            await printlog(update, f"cambia {key} da {user_settings[key]} a {value}")

        else:
            message += f"Chiave <code>'{key}'</code> non trovata. Prova <code>/settings</code> senza parametro per il menu interattivo."

        await update.message.reply_html(message)
        context.user_data.pop("conversation_settings", None)
        return ConversationHandler.END

    elif len(context.args) > 2:
        message += "Non ho capito, scusa. Prova <code>/settings -help</code> e fallo bene."
        await update.message.reply_html(message)
        context.user_data.pop("conversation_settings", None)
        return ConversationHandler.END


# WAIT_FOR_SETTING
async def settings_change_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chiave = query.data.split(":")[1]
    all_commands = {}
    for k in config.DEFAULT_USER_SETTINGS:
        all_commands[k["chiave"]] = k

    if chiave == "annulla":
        try:
            await query.message.delete()
        except TGBardRequest:
            pass
        context.user_data.pop("conversation_settings", None)
        return ConversationHandler.END

    user_settings = get_user_settings(context)
    message = f"Stai per cambiare il valore di <code>{chiave}</code>.\n"
    message = f'Descrizione: <code>{all_commands[chiave]["descrizione"]}</code>\n'
    message += f"Valore attuale: <code>{user_settings[chiave]}</code>\n"
    message += f'Valore di default: <code>{all_commands[chiave]["default"]}</code>\n\n'
    message += "Invia il nuovo valore, oppure scrivi <code>annulla</code> per annullare."

    msg = await query.message.edit_text(message)
    context.user_data["conversation_settings"]["chiave"] = chiave
    context.user_data["conversation_settings"]["message_to_delete"] = []
    context.user_data["conversation_settings"]["message_to_delete"].append(msg.message_id)
    return "CHANGE_SETTING"


# CHANGE_SETTING
async def settings_change_actual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chiave = context.user_data["conversation_settings"]["chiave"]
    user_settings = get_user_settings(context)

    if update.message.text.lower() == "annulla":
        context.user_data["conversation_settings"]["message_to_delete"].append(update.effective_message.id)

        await delete_all_messages(
            context, update.effective_chat.id, context.user_data["conversation_settings"]["message_to_delete"]
        )
        context.user_data.pop("conversation_settings", None)

        return ConversationHandler.END

    print(f"Cambio {chiave} da {user_settings[chiave]} a {update.message.text}")

    user_settings[chiave] = update.message.text
    context.user_data["user_settings"] = user_settings

    await update.effective_chat.send_message(
        f"Valore di <code>{chiave}</code> cambiato in <code>{update.message.text}</code>!"
    )

    await printlog(update, f"cambia {chiave} da {user_settings[chiave]} a {update.message.text}")

    context.user_data["conversation_settings"]["message_to_delete"].append(update.message.message_id)

    await delete_all_messages(
        context, update.effective_chat.id, context.user_data["conversation_settings"]["message_to_delete"]
    )
    context.user_data.pop("conversation_settings", None)

    return ConversationHandler.END


# TIMEOUT
async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("conversation_settings", None)

    return ConversationHandler.END


async def delete_all_messages(context: ContextTypes.DEFAULT_TYPE, chat_id, message_list):
    for msg_id in message_list:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except TGBardRequest:
            pass
    return True

