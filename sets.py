import json
from collections import defaultdict

from telegram import Update
from telegram.ext import ContextTypes

import config
from utils import crea_sondaggino, get_now, make_delete_button, no_can_do, printlog

jukebox_id = 0

# Set
async def addset(update: Update, context: ContextTypes.DEFAULT_TYPE, poll_passed=False) -> None:
    if await no_can_do(update, context):
        return

    with open('db/sets.json') as sets_db:
        sets = json.load(sets_db)
    chat_id = str(update.message.chat.id)

    if chat_id not in sets:
        sets[chat_id] = {}

    chatdict = sets[chat_id]
    message = update.message.text[5:]

    try:
        trigger = message.split(' ')[0].lower()
        comando = message.split(' ', 1)[1]
    except IndexError:
        trigger = message.split(' ')[0].lower()
        if update.message.reply_to_message:
            if not update.message.reply_to_message.effective_attachment:
                await update.message.reply_html('Usa: <code>/set /trigger messaggio</code>, oppure <code>/set /trigger</code> in risposta ad un media')
                return
            else:
                if update.message.reply_to_message.animation:
                    comando = f"media:animation:{update.message.reply_to_message.animation.file_id}"
                elif update.message.reply_to_message.document:
                    comando = f"media:document:{update.message.reply_to_message.document.file_id}"
                elif update.message.reply_to_message.audio:
                    comando = f"media:audio:{update.message.reply_to_message.audio.file_id}"
                elif update.message.reply_to_message.photo:
                    comando = f"media:photo:{update.message.reply_to_message.photo[-1].file_id}"
                elif update.message.reply_to_message.sticker:
                    comando = f"media:sticker:{update.message.reply_to_message.sticker.file_id}"
                elif update.message.reply_to_message.video:
                    comando = f"media:video:{update.message.reply_to_message.video.file_id}"
                elif update.message.reply_to_message.voice:
                    comando = f"media:voice:{update.message.reply_to_message.voice.file_id}"
                elif update.message.reply_to_message.video_note:
                    comando = f"media:video_note:{update.message.reply_to_message.video_note.file_id}"
        else:
            await update.message.reply_html('Uso: \n<code>/set /trigger [messaggio]</code>\noppure\n<code>/set /trigger</code> in risposta ad un media')
            return

    if update.message.from_user.id not in config.ADMINS:
        if trigger[0] != "/":
            await update.message.reply_text('Il trigger deve essere un /comando.')
            return
   
    if chatdict.get(trigger.lower()) and not poll_passed:
        max_votes = 4
        await crea_sondaggino(context, update, max_votes, addset, domanda="Il set è già presente, vuoi sostituirlo?")
        return

    chatdict[trigger.lower()] = comando
    await printlog(update, "aggiunge un set", f"{trigger} -> {comando}")

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} aggiunge un set: {trigger} -> {comando}')
    await update.message.reply_text('Daje.')

    json.dump(sets, open('db/sets.json', 'w'), indent=4)

    # we refresh the in-memory copy of sets
    if 'current_sets' not in context.bot_data:
        context.bot_data['current_sets'] = {}
    with open('db/sets.json') as sets_db:
        sets = json.load(sets_db)
        context.bot_data['current_sets'] = sets

async def listaset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    # with open('db/sets.json') as sets_db:
    #     sets = json.load(sets_db)
    if 'current_sets' not in context.bot_data:
        context.bot_data['current_sets'] = {}

    sets = context.bot_data['current_sets']

    chat_id = str(update.message.chat.id)

    if context.args:
        if context.args[0].lstrip("-").isdigit():
            chat_id = context.args[0]

    message = ""
    await printlog(update, "chiede la lista dei set")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede la lista dei set di {chat_id}')

    # if chat_id not in sets:
    #     sets[chat_id] = {}

    chatdict = sets.get(chat_id)

    if not chatdict:
        await update.message.reply_text('Non ci sono set.')
        return

    cat_names = {'audio': '🔈 Audio', 'photo': '🖼 Immagini', 'video': '🎥 Video', 'voice': '🎙 Registrazioni vocali', 'document': '📎 Files', 'video_note': '📹 Registrazioni video', 'sticker': '🏷 Stickers', 'animation': '🎬 GIFs'}

    textlist = []
    medialist = defaultdict(list)


    if '-listona' in context.args:
        for key in sorted(chatdict.keys()):
            comando = chatdict[key]

            if comando.lower().startswith('nsfw'):
                    comando = "[NSFW whitespace]"

            if comando.startswith('media:'):
                comando = f"[{comando.split(':')[1]}]"

            message += f"{key} → {(comando[:25] + '...') if len(comando) > 25 else comando}\n"
        await update.message.reply_text(f'{message}', disable_notification=True, disable_web_page_preview=True)
        return

    for key in chatdict.keys():
        comando = chatdict[key]

        if comando.startswith('media:'):
            medialist[comando.split(':')[1]].append(key)
       
        else:
       
            if comando.lower().startswith('nsfw'):
                comando = "[NSFW whitespace]"

            textlist.append(f"{key} → {(comando[:25] + '...') if len(comando) > 25 else comando}")

    for line in sorted(textlist):
        message += f"{line}\n"

    message += "\n"

    for cat in cat_names.keys():
        if medialist.get(cat):
            message += f"{cat_names[cat]}:\n"
            message += f"{' · '.join(sorted(medialist[cat]))}\n\n"

    await update.message.reply_text(f'{message}', disable_notification=True, disable_web_page_preview=True, reply_markup=make_delete_button(update))

async def deleteset(update: Update, context: ContextTypes.DEFAULT_TYPE, poll_passed=False) -> None:
    if await no_can_do(update, context):
        return

    with open('db/sets.json') as sets_db:
        sets = json.load(sets_db)

    chat_id = str(update.message.chat.id)

    if chat_id not in sets:
        sets[chat_id] = {}
    chatdict = sets[chat_id]
    trigger = " ".join(context.args)
    await printlog(update, "vuole eliminare il trigger", trigger)

    if chatdict.get(trigger.lower()) and not poll_passed:
        max_votes = 4
        await crea_sondaggino(context, update, max_votes, deleteset, domanda="Vogliamo cancellare questo set?")
        return

    if trigger in chatdict:
        try:
            del chatdict[trigger]
            print(f'{get_now()} Fatto!')
            await update.message.reply_text('Fatto.', quote=False)
            json.dump(sets, open('db/sets.json', 'w'), indent=4)
            # we refresh the in-memory copy of sets
            if 'current_sets' not in context.bot_data:
                context.bot_data['current_sets'] = {}
            with open('db/sets.json') as sets_db:
                sets = json.load(sets_db)
                context.bot_data['current_sets'] = sets
            return
        except KeyError:
            await update.message.reply_text('Per qualche ragione non riesco.')
            return
    else:
        await update.message.reply_text('Non ci sta, controlla meglio con /listaset')
        return

async def jukebox(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    # if update.message.chat.id != config.ID_DIOCHAN:
    #     return


    # with open('db/sets.json') as sets_db:
    #     sets = json.load(sets_db)
    if 'current_sets' not in context.bot_data:
        context.bot_data['current_sets'] = {}

    sets = context.bot_data['current_sets']

    chat_id = str(update.message.chat.id)
    message = ""
    await printlog(update, "chiede la lista jukebox di", chat_id)
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede la lista dei set di {chat_id}')

    if chat_id not in sets:
        sets[chat_id] = {}
    chatdict = sets[chat_id]
    for key in chatdict.keys():
        comando = chatdict[key]
        if comando.startswith('media:'):
            comando = f"{comando.split(':')[1]}"

        if comando == 'audio':
            message += f"🎶 ̄· {key}\n"
        if comando == 'voice':
            message += f"🎤 ̄· {key}\n"


    if message == "":
        await update.message.reply_text('Non ci sono audio.')
        return
    await update.message.reply_text(f'{message}', disable_notification=True)
