import time
import deepl 
import tempfile
import upsidedown
import datetime
import requests
import lichess.api
import random
import os
import aiohttp

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from telegram import Update, Bot
from telegram.ext import ContextTypes

from PIL import Image
from rich import print
from gtts import gTTS
from pydub import AudioSegment
from dateutil.parser import parse, parserinfo
from aiohttp_client_cache import CachedSession, FileBackend

import config

from utils import printlog, no_can_do, get_now, get_chat_name, expand, get_display_name, InlineButton, print_progressbar, crea_sondaggino
from twitter import tweet
from pyrog import get_user_from_username, send_reaction, pyro_bomb_reaction


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationHandlerStop


async def wikihow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    count = 3

    url_text = "https://hargrimm-wikihow-v1.p.rapidapi.com/steps"
    url_images = "https://hargrimm-wikihow-v1.p.rapidapi.com/images"

    querystring = {"count":f"{count}"}
    headers = {
        "X-RapidAPI-Key": "6b1eba0153msh8cd62219142c90fp1f3ea3jsn5e757aabd168",
        "X-RapidAPI-Host": "hargrimm-wikihow-v1.p.rapidapi.com"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url_text, headers=headers, params=querystring) as resp:
            response_text = await resp.json()
        async with session.get(url_images, headers=headers, params=querystring) as resp:
            response_images = await resp.json()
        
    
    # response_text = requests.request("GET", url_text, headers=headers, params=querystring).json()
    # response_images = requests.request("GET", url_images, headers=headers, params=querystring).json()
    await printlog(update, "chiede aiuto a wikihow")
    mystring = ""
    for k, v in response_text.items():
        mystring += f"{k}. {v}\n"

    images = [url for url in response_images.values()]
    medialist = [InputMediaPhoto(media=url) for url in images]
    await update.message.reply_media_group(media=medialist, caption=mystring)

async def aoc_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat.id not in [config.ID_TIMELINE, config.ID_AOC]:
        return

    if await no_can_do(update, context):
        return

    if update.message.chat.id == config.ID_TIMELINE:
        await update.message.reply_html(f"<code>https://www.youtube.com/watch?v=6Z3QJ4L1Bg0</code>")
        return
        LB_ID = 799277
    else:
        LB_ID = 8518
    
    SESSION = config.AOC_SESSION

    url = f"https://adventofcode.com/2022/leaderboard/private/view/{LB_ID}.json"
    headers = {'Cookie': f'session={SESSION}'}

    cache = FileBackend(cache_name='aiohttp_cache', use_temp=True, expire_after=900)

    async with CachedSession(cache=cache) as session:
        response = await session.get(url, headers=headers)
    response = await response.json()

    leaderboard = []
    classifica = ""

    for member in response['members']:
        m = []
        member = response['members'][member]
        m.append(int(member.get('local_score')))
        if member.get('name'):
            m.append(member.get('name'))
        else:
            m.append(f"Anonymous User #{member.get('id')}")
        m.append(member.get('stars'))
        leaderboard.append(m)

    top5 = sorted(leaderboard, reverse=True)[:10]

    for i, value in enumerate(top5, start=1):
        classifica += f"{i: >2})\t[{value[0]}] {value[2]: >2} ?????? {value[1]}\n"

    await update.message.reply_html(f"<code>{classifica}</code>")

async def random_trifase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return

    trifasi_dir = "images/trifasi/"
    random_list = os.listdir(trifasi_dir)
    random_file = random.choice(random_list)
    pos = random_list.index(random_file)
    name = random_file[:-4]
    name = name.replace('Luca', 'Trifase')
    name = f"[{pos}/{len(random_list)}] ?? {name}"
    await printlog(update, "chiede un'immagine di trifase random", name)
    await update.message.reply_photo(open(f"{trifasi_dir}{random_file}", "rb"), caption=name)

async def polls_callbackqueryhandlers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    query = update.callback_query

    # print(query.to_dict())
    MAX_TIMEOUT = 28800 # 8 ore

    await query.answer()

    mybutton = query.data
    votazione = context.chat_data['votazioni_attive'][mybutton.original_msg_id]
    domanda = votazione.get('domanda')

    if (update.effective_user.id != config.ID_TRIF) and (update.effective_user.id in votazione['voters']):
        return
    else:
        votazione['voters'].append(update.effective_user.id)

    await printlog(update, "ha votato", mybutton.vote)

    if (mybutton.vote == 's??') and (votazione['current_votes'] < votazione['max_votes']):
        votazione['current_votes'] += 1
    elif (mybutton.vote == 'no') and (votazione['current_votes'] > 0):
        votazione['current_votes'] -= 1

    messaggio = f"<code>{domanda if domanda else ''}Conferme: {votazione['current_votes']}/{votazione['max_votes']}\n"
    messaggio += f"{print_progressbar(votazione['current_votes'], votazione['max_votes'], votazione['max_votes'])}</code>"
    # print(f"Sondaggio originale: {votazione['timestamp']} - ora voto {int(time.time())}: {int(time.time()) - votazione['timestamp']}")
    if (int(time.time()) - votazione['timestamp']) > MAX_TIMEOUT:
        messaggio += "\n\nTempo scaduto."
        context.chat_data['votazioni_attive'].pop(mybutton.original_msg_id, None)
        context.bot.callback_data_cache.clear_callback_data(time_cutoff=time.time() - (MAX_TIMEOUT + 10))
        await query.edit_message_text(messaggio)
        return

    if votazione['current_votes'] == votazione['max_votes']:
        messaggio += "\n\nRisultato Raggiunto!"
        if update.effective_chat.id in [config.ID_ASPHALTO]:
            await query.unpin_message()

        await query.delete_message()
        # await query.edit_message_text(messaggio)
        context.chat_data['votazioni_attive'].pop(mybutton.original_msg_id, None)

        try:
            context.args = mybutton.original_update.message.text.split()[1:]
        except Exception as e:
            context.args = []

        function_to_call = mybutton.callable
        await function_to_call(mybutton.original_update, context, poll_passed=True)
        return

    elif votazione['current_votes'] == 0:
        messaggio += "\n\nMi dispiace."
        if update.effective_chat.id in [config.ID_ASPHALTO]:
            await query.unpin_message()
        context.bot.callback_data_cache.clear_callback_data(time_cutoff=time.time() - 150)
        context.chat_data['votazioni_attive'].pop(mybutton.original_msg_id, None)
        await query.edit_message_text(messaggio)

    else:
        await query.edit_message_text(messaggio, reply_markup=query.message.reply_markup)

    return

async def is_safe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    from nudenet import NudeClassifier, NudeDetector
    
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return

    await printlog(update, "controlla una foto per NSFW")

    picture = update.message.reply_to_message.photo[-1]
    # tempphoto = tempfile.mktemp(suffix='.jpg')
    tempphoto = tempfile.NamedTemporaryFile(suffix='.jpg')

    actual_picture = await picture.get_file()
    await actual_picture.download_to_drive(custom_path=tempphoto.name)

    classifier = NudeClassifier()
    results = classifier.classify(tempphoto.name)

    unsafeness = results[tempphoto.name]['unsafe']
    safeness = results[tempphoto.name]['safe']
    limit = 0.80

    text = f"Safe: ({str(safeness * 100)[:4]}%)\nUnsafe: ({str(unsafeness * 100)[:4]}%)\n\n{'??? NOT' if unsafeness > safeness else '???'} SAFE"
    msg = await update.message.reply_html(text)

    if '-why' in context.args:
        detector = NudeDetector()
        results = detector.detect(tempphoto.name)
        text += "\n\n"
        original_text = text

        if results:
            for r in results:
                text += f"<code>{r['label']}: {str(r['score'] * 100)[:4]}%</code>\n"
        else:
            text += "Nessuna feature trovata"

        await msg.edit_text(text, parse_mode='HTML')

async def greet_BT_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in [config.ID_TIMELINE]:
        return

    greets = [
        "Weeee, da quanto tempo!",
        "Weeeeeee quanto tempo!",
        "We! Da quanto tempo",
        "weeeeee!",
        "Weeee da quanto tempo",
        "Weee anche tu qua",
        "Weeeee da quanto tempo!",
        "Weeeeee quanto tempo",
        "Weeeeeeee quanto tempo"
    ]

    await update.message.reply_html(random.choice(greets))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = """
Ciao!
Questo ?? un bot multi-funzione con una numero variabile di comandi, molti neanche documentati.

Continuando ad usarlo, accetti le seguenti cose:
  ?? Quello che scrivi potrebbe essere salvato da qualche parte;
  ?? Hai la completa responsabilit?? delle cose che fai;
  ?? L'uso dei comandi non ?? un diritto e pu?? essere negato in qualunque momento per qualunque ragione.

Detto ci??, se vuoi usare il comando /ai per generare testo, <b>non funzioner?? in privato</b>.

Se ti piace il bot, puoi usare il comando /donazione per effettuare una piccola donazione, per aiutare lo sviluppo.

Se hai altre domande, puoi chiedere qui: @Trifase
"""
    await update.message.reply_html(message)
    return

async def get_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    if update.effective_user.id not in config.ADMINS:
        return
    if not context.args:
        return
    print(f"get_user_settings {context.args[0]}")
    user_summary = await get_user_from_username(context.args[0])
    print(user_summary)
    await update.message.reply_html(user_summary)

async def set_auto_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    if update.effective_user.id not in config.ADMINS:
        return
    if not update.message.reply_to_message:
        return

    user_id = update.message.reply_to_message.from_user.id

    if not context.args or context.args[0] == "-off":
        context.application.user_data[user_id].pop('auto_reaction')
        await update.message.reply_text("Auto reaction disabilitata")
        await printlog(update, "disabilita auto reaction", f"{user_id} ({update.message.reply_to_message.from_user.username})")
        # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} disabilita Auto Reaction su {user_id} ({update.message.reply_to_message.from_user.username})')
        return

    context.application.user_data[user_id]['auto_reaction'] = context.args[0]
    await update.message.reply_text(f"Auto reaction abilitata: {context.args[0]}")
    await printlog(update, "abilita auto reaction", f"{user_id} ({update.message.reply_to_message.from_user.username})")

async def send_auto_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    if context.user_data.get('auto_reaction'):
        await send_reaction(update.message.chat_id, update.message.message_id, context.user_data['auto_reaction'])

async def bomb_react(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    if update.effective_user.id not in config.ADMINS:
        return
    if not update.message.reply_to_message:
        return

    user_id = update.message.reply_to_message.from_user.id
    username = update.message.reply_to_message.from_user.username
    displayname = await get_display_name(update.message.reply_to_message.from_user)
    await printlog(update, "lancia una bombreact a", displayname)

    await pyro_bomb_reaction(update.message.chat_id, username, limit=120, sample=20)

async def bioritmo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    specificdate = False
    if not context.args or "/" not in context.args[0]:
        await update.message.reply_text("Devi fornire la data di nascita (lo so), tipo <code>/bioritmo 08/03/1987</code> o simile.")
        return
    if len(context.args) == 2 and "/" in context.args[0] and "/" in context.args[1]:
        specificdate = True
    await printlog(update, "chiede il bioritmo")

    try:
        settings = parserinfo(dayfirst=True, yearfirst=False)
        dt_bd = parse(context.args[0], parserinfo=settings)
    except Exception as e:
        await update.message.reply_text(f"{e}")
        return
    if specificdate:
        dt_now_ymd = parse(context.args[1], parserinfo=settings)
    else:
        dt_now = datetime.datetime.now()
        dt_now_ymd = datetime.datetime(dt_now.year, dt_now.month, dt_now.day)


    dt_diff = dt_now_ymd - dt_bd
    dt_diff_days = dt_diff.days


    dt_start_delta = 7

    dt_end_delta = 7


    dt_start = dt_now_ymd - datetime.timedelta(days=dt_start_delta)

    dt_end = dt_now_ymd + datetime.timedelta(days=dt_end_delta)

    dt_range = dt_end - dt_start  + datetime.timedelta(days=1)

    dates = [dt_start + datetime.timedelta(days=i) for i in range(dt_range.days)]

    vals1 = [np.sin(2 * np.pi * (i + dt_diff_days - dt_start_delta) / 23) for i in range(dt_range.days)]

    vals2 = [np.sin(2 * np.pi * (i + dt_diff_days - dt_start_delta) / 28) for i in range(dt_range.days)]

    vals3 = [np.sin(2 * np.pi * (i + dt_diff_days - dt_start_delta) / 33) for i in range(dt_range.days)]


    plt.figure(figsize=plt.figaspect(0.5))

    ax = plt.subplot()
    ax.axvline(x=dt_start + datetime.timedelta(days=7), color='k')
    ax.axhline(y=0, xmin=0, xmax=1, color='k')
    ax.plot(dates, vals1, color='red')
    ax.plot(dates, vals2, color='green')
    ax.plot(dates, vals3, color='blue')

    xfmt = mdates.DateFormatter('%m/%d')
    xloc = mdates.DayLocator()
    ax.xaxis.set_tick_params(rotation=90)

    ax.xaxis.set_major_locator(xloc)

    ax.xaxis.set_major_formatter(xfmt)


    ax.text(dt_start + datetime.timedelta(days=1), 1.2, 'Fisico', color='red')

    ax.text(dt_start + datetime.timedelta(days=5), 1.2, 'Emotivo', color='green')

    ax.text(dt_start + datetime.timedelta(days=9), 1.2, 'Intellettuale', color='blue')


    ax.set_xlim(dt_start, dt_end)

    ax.grid(True)

    plt.savefig('images/bioritmo.png')
    await update.message.reply_photo(open('images/bioritmo.png', 'rb'))

async def condominioweb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import io
    import json
    from dataclassy import dataclass
    from datetime import datetime
    import random
    import pprint
    import time
    import asyncio
    from codetiming import Timer
    import zstandard
    import jsonlines


    @dataclass
    class Comment:
        text: str
        dateCreated: datetime
        author_name: str

    @dataclass
    class DiscussionForumPosting:
        """Small subset of https://schema.org/DiscussionForumPosting"""
        discussionUrl: str
        headline: str
        text: str
        dateCreated: datetime
        author_name: str
        comment: list[Comment]

    def generate_condominioweb_threads(zip=True):
        if zip:
            with open('db/condominioweb.jsonl.zst', 'rb') as fh:
                dctx = zstandard.ZstdDecompressor()
                stream_reader = dctx.stream_reader(fh)
                text_stream = io.TextIOWrapper(stream_reader, encoding='utf-8')
                for line in text_stream:
                    obj = json.loads(line)
                    yield obj
        else:
            with jsonlines.open('db/condominioweb.jsonl') as reader:
                for obj in reader:
                    yield obj

    def generate_condominioweb_objs(thread):
        for msgs in thread:
            comment = []
            for c in msgs.get('comment', []):
                comment.append(Comment(c['text'], datetime.fromisoformat(c['dateCreated'][0:19]), c['author']['name']))
            yield DiscussionForumPosting(
                msgs['discussionUrl'],
                msgs['headline'],
                msgs['text'],
                # fromisoformat does NOT accept the timezone because reasons, have to truncate here
                datetime.fromisoformat(msgs['dateCreated'][0:19]),
                msgs['author']['name'],
                comment
            )

    if update.effective_chat.id != config.ID_RITALY:
        return

    await printlog(update, "cerca su condominioweb")
    await context.bot.send_message(config.ID_RITALY, "Ok, un attimo, vado a scegliere un thread casuale", parse_mode='HTML', disable_web_page_preview=True)
    with Timer(name="unzip"):
        threadlist = [thread for thread in generate_condominioweb_threads()]
    thread = random.choice(threadlist)
    author = thread.get('author').get('name')
    url = thread.get('discussionUrl')
    title = thread.get('name')
    text = thread.get('text')
    message = f"<a href='{url}'><b>{title}</b></a>\n{author} ha scritto:\n{text}"
    og = await context.bot.send_message(config.ID_RITALY, message, parse_mode='HTML', disable_web_page_preview=True)
    # print(message)
    # print("=====")
    time.sleep(1)

    if not thread.get('comment'):
        await context.bot.send_message(config.ID_RITALY, "Nessuno ha mai risposto.", parse_mode='HTML')
        return
    
    for comment in thread.get('comment'):
        author = comment.get('author').get('name')
        text = comment.get('text')
        message = f"{author} risponde:\n{text}"
        # print(message)
        # print()
        await context.bot.send_message(config.ID_RITALY, message, parse_mode='HTML')
        time.sleep(1.5)

async def traduci(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply = False

    if await no_can_do(update, context):
        return

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} richiede una traduzione')
    await printlog(update, "chiede una traduzione")
    translator = deepl.Translator(config.DEEPL_API_KEY) 
    target_language = "EN-GB"
    languages = ["BG", "CS", "DA", "DE", "EL", "EN-GB", "EN-US", "ES", "ET", "FI", "FR", "HU", "IT", "JA", "LT", "LV", "NL", "PL", "PT-PT", "PT-BR", "RO", "RU", "SK", "SL", "SV", "TR", "ZH"]

    if update.message.reply_to_message:  # ?? una reply
        reply = True
        if context.args:  # c'?? qualcosa oltre a traduci
            if context.args[0].startswith('@'):  # la prima parola ?? @
                if context.args[0][1:].upper() not in languages:  # non ?? una lingua accettata
                    await update.message.reply_text("Non riconosco quella lingua.")
                    return
                else:
                    target_language = context.args[0][1:].upper()  # imposto la lingua
                text = " ".join(context.args[1:]) 
                if not text:
                    text = update.message.reply_to_message.text
            else:
                text = " ".join(context.args)
        else:
            text = update.message.reply_to_message.text

    else:
        if context.args:
            if context.args[0].startswith('@'):  # la prima parola ?? @
                if context.args[0][1:].upper() not in languages:  # non ?? una lingua accettata
                    await update.message.reply_text("Non riconosco quella lingua.")
                    return
                else:
                    target_language = context.args[0][1:].upper()  # imposto la lingua
                text = " ".join(context.args[1:]) 
                if not text:
                    return
            else:
                text = " ".join(context.args) 
        else:
            return

    result = translator.translate_text(text, target_lang=target_language) 
    translated_text = f'[{target_language}] {result.text}'
    if not translated_text:
        await update.message.reply_text("boh")
    else:
        if reply:
            reply_to = update.message.reply_to_message.message_id
            await update.message.reply_text(translated_text, reply_to_message_id=reply_to)
        else:
            await update.message.reply_text(translated_text)
    return

async def fatfingers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    def get_keys_around(key):
        # lines = "1234567890'??", "qwertyuiop??+", "asdfghjkl??????", "<zxcvbnm,.-"
        lines = "qwertyuiop??+", "asdfghjkl??????", "<zxcvbnm,.-"
        try:
            line_index, index = [(i, l.find(key)) for i, l in enumerate(lines) if key in l][0]
        except IndexError:
            return [key]
        lines = lines[line_index - 1: line_index + 2] if line_index else lines[0: 2]
        return [
            line[index + i] for line in lines for i in [-1, 0, 1]
            if len(line) > index + i and line[index + i] != key and index + i >= 0]

    def substitution(c):
        c = c.replace(c, random.choice(get_keys_around(c)))
        return c

    def insertion(c):
        c = c + random.choice((get_keys_around(c) + [c]))
        return c

    text = " ".join(context.args)
    if update.message.reply_to_message and not text:
        text = update.message.reply_to_message.text

    lunghezza = len(text)
    newtext = []

    omission_rate = 0.80
    insertion_rate = 0.67
    substitution_rate = 1.65
    if lunghezza < 20:
        omission_rate = 3.20
        insertion_rate = 2.68
        substitution_rate = 6.60

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} digita con le dita ciccione!')
    await printlog(update, "digita con le dita ciccionazze")

    for c in text:
        ifupper = c.isupper()
        roll = random.uniform(0, 100)
        # print(roll)
        if c == " ":
            newtext.append(c)
            continue

        if roll <= omission_rate:
            continue

        elif roll <= insertion_rate + omission_rate:
            c = c.lower()
            c = insertion(c)
            if ifupper:
                newtext.append(c.upper())
            else:
                newtext.append(c)
            continue

        elif roll <= substitution_rate + omission_rate + insertion_rate:
            c = c.lower()
            c = substitution(c)
            if ifupper:
                newtext.append(c.upper())
            else:
                newtext.append(c)
            continue

        else:  # corretto
            if ifupper:
                newtext.append(c.upper())
            else:
                newtext.append(c)

    string = ''.join(x for x in newtext)
    string = string.replace("<", "&lt;").replace(">", "&gt;")
    await update.message.reply_to_message.reply_text(f'{string}')

async def spongebob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} spongebob time!')
    await printlog(update, "SpOnGeBoB")
    if update.message.reply_to_message:
        message = update.message.reply_to_message.text
        message_id = update.message.reply_to_message.message_id
    else:
        message = update.message.text[11:]
        message_id = update.message.message_id

    if not message:
        return

    newmessage = []
    for index in range(len(message)):
        if (index % 2 != 0):
            newmessage.append(message[index].lower())
        else:
            newmessage.append(message[index].upper())

    string = ''.join(x for x in newmessage)
    await context.bot.send_photo(update.message.chat.id, photo=open('images/spongebob.jpg', 'rb'), caption=string, reply_to_message_id=message_id)

async def call_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede l\'help!')
    await printlog(update, "chiede aiuto")

    if update.message.chat.id == config.ID_ASPHALTO:
        await update.message.reply_markdown_v2(
            f'Ciao {update.effective_user.username}, i comandi disponibili in questo canale sono:\n`/square`\n`/set`, `/listaset` e `/deleteset`\n`/remindme`,`/reminderlist` e `remindelete`\n`/tweet` in risposta, `/tweet <qualcosa>` o `/tweets` per la lista, `/listaset` e `deleteset`\n`/azzurro nome@messaggio` \(in pvt\)\.')
        return
    elif update.message.chat.id == config.ID_DIOCHAN:
        await update.message.reply_markdown_v2(
            f'Ciao {update.effective_user.username}, i comandi disponibili in questo canale sono:\n`/square`\n`/set`, `/listaset` e `/deleteset`\n`/remindme`,`/reminderlist` e `remindelete`\n`/tweet` in risposta, `/tweet <qualcosa>` o `/tweets` per la lista\.')
    else:
        await update.message.reply_markdown_v2(
            f'Ciao {update.effective_user.username}, i comandi disponibili in questo canale sono:\n`/square`\n`/set`, `/listaset` e `/deleteset`\n`/remindme`,`/reminderlist` e `remindelete`\n`/tweet` in risposta, `/tweet <qualcosa>` o `/tweets` per la lista\.')

async def square(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # SQUARE!
    if await no_can_do(update, context):
        return
    if not context.args:
        await update.message.reply_text('Devi scrivere qualche cosa.')
        return

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {get_chat(update.message.chat.id)} triggera SQUARE!')  # debug
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} triggera SQUARE!')  # debug
    await printlog(update, "triggera SQUARE")

    text = " ".join(context.args)  # SQUARE (6) "S Q U A R E" (6*2)-1 = 11
    if len(text) == 1:
        await update.message.reply_text(f'Fallo tu un quadrato con un carattere solo, coglione')
        return
    inversetext = text[::-1]  # ERAUQS
    lung = (len(text) * 2) - 1
    fill = (lung - 2) * ' '
    message = []
    message.append("`" + expand(text) + "`")
    for i in range(1, len(text) - 1):
        message.append("`" + text[i] + fill + inversetext[i] + "`")
    message.append("`" + expand(inversetext) + "`")
    squared = "\n".join(message)
    await update.message.reply_markdown_v2(f'{squared}')

async def fascio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} fascio time!')
    await printlog(update, "mette a posto un fascista")
    message = " ".join(context.args)

    if update.message.reply_to_message and not message:
        message = update.message.reply_to_message.text

    try:
        if update.message.reply_to_message.photo:
            if update.message.reply_to_message.caption:
                message = update.message.reply_to_message.caption
            elif not message:
                message = ""
            else:
                message = message
            picture = update.message.reply_to_message.photo[-1]
            # tempphoto = tempfile.mktemp(suffix='.jpg')
            tempphoto = tempfile.NamedTemporaryFile(suffix='.jpg')
            actual_picture = await picture.get_file()
            await actual_picture.download_to_drive(custom_path=tempphoto.name)
            im = Image.open(tempphoto.name)
            out = im.rotate(180, expand=True)
            out.save(tempphoto.name)
            await update.message.reply_photo(tempphoto, caption=upsidedown.transform(message))
            tempphoto.close()

    except AttributeError:
        pass
    if message:
        newmessage = upsidedown.transform(message)
        await update.message.reply_text(newmessage)
        return
    else:
        return

async def scacchi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in [yellow1]{update.effective_chat.title[:10]}[/yellow1] ({str(update.message.chat.id)[4:]}) interroga lichess!')
    await printlog(update, "interroga lichess")
    

    token = config.LICHESS_API
    nick = " ".join(context.args)
    apiurl = "https://lichess.org/api/challenge/open"
    limit = 60 * 10
    increment = 3
    if nick == "aurora":
        nick = "orezesirunusss"

    if nick == "amichevole":
        post_data = {
            'rated': 'false',
            'clock.limit': limit,
            'clock.increment': increment, 
            'variant': 'standard', 
            'name': 'r/italy scacchi'
        }
        is_rated = "false"
        response = requests.post('https://lichess.org/api/challenge/open', data=post_data)
        reply = response.json()
        url = reply['challenge']['url']
        await update.message.reply_html(f'Nuova partita creata!\n{url}\nTipo di partita: amichevole 10+3', disable_web_page_preview=True)
        return

    if nick == "corrispondenza":
        post_data = {
            'rated': 'false',
            'clock.limit': "",
            'clock.increment': "", 
            'variant': 'standard', 
            'name': 'r/italy scacchi'
        }
        is_rated = "false"
        response = requests.post('https://lichess.org/api/challenge/open', data=post_data)
        reply = response.json()
        url = reply['challenge']['url']
        await update.message.reply_html(f'Nuova partita creata!\n{url}\nTipo di partita: corrispondenza', disable_web_page_preview=True)
        return

    if nick == "rated" or nick == "ranked":
        post_data = {
            'rated': 'true',
            'clock.limit': limit,
            'clock.increment': increment, 
            'variant': 'standard', 
            'name': 'r/italy scacchi'
        }
        is_rated = "true"
        response = requests.post('https://lichess.org/api/challenge/open', data=post_data)
        reply = response.json()
        url = reply['challenge']['url']
        await update.message.reply_html(f'Nuova partita creata!\n{url}\nTipo di partita: classificata 10+3', disable_web_page_preview=True)
        return

    if not nick:
        await update.message.reply_text(f'Inserisci un nick per le statistiche, oppure "rated" per una 10+3 rated, oppure "amichevole" per una 10+3 amichevole')
        return
    try:
        user = lichess.api.user(nick, auth=token)
    except Exception as e:  
        await update.message.reply_text(f'{e}: Nick {nick} non trovato.')
        return
    # print(user['perfs'])
    # print(user['count'])
    giocate = user['count']['all']
    perse = user['count']['loss']
    vinte = user['count']['win']
    last_seen = datetime.datetime.fromtimestamp(int(str(user['seenAt'])[:10])).strftime('%Y-%m-%d %H:%M:%S')
    if int(giocate) == 0:
        vinte_ratio = "100"
    else:
        vinte_ratio = round(int(vinte) / int(giocate) * 100, 2)

    url = user['url']
    messaggio = ""
    messaggio += f"\nVinte: {vinte}/{giocate} ({vinte_ratio}%)\n\n"
    for k, v in user['perfs'].items():
        try:
            messaggio += f"{k.capitalize()}: <code>{v['rating']}</code> ({v['games']} partite)\n"
        except KeyError:
            pass
    messaggio += f"\nLast seen: {last_seen}\n"
    try:
        url_partita = user['playing']
        messaggio = f'<a href="{url}">{nick}</a> <a href="{url_partita}">[in partita]</a>:\n' + messaggio
        await update.message.reply_html(messaggio, disable_web_page_preview=True)
    except KeyError:
        await update.message.reply_html(messaggio, disable_web_page_preview=True)
    pass

async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    def text_to_audio(string):

        language = 'it'
        voice_tts = gTTS(text=string, lang=language, slow=False)
        voice_tts.save("tts/tts_mp3.mp3")
        song = AudioSegment.from_mp3("tts/tts_mp3.mp3")
        song.export("tts/tts_ogg.ogg", format="ogg", codec="libopus")
        return

    bot = context.bot
    text = " ".join(context.args)
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} avvia una sintesi vocale')
    await printlog(update, "avvia TTS voice")

    if text: 
        text = text
    elif update.message.reply_to_message and not text:
        text = update.message.reply_to_message.text
        # text = update.message.reply_to_message.from_user.username + " dice: " + update.message.reply_to_message.text
    else:
        text = f"{update.effective_user.username} non sa che scrivere"
    await update.effective_chat.send_chat_action(action='record_voice')
    text_to_audio(text)
    file = open("tts/tts_ogg.ogg", 'rb')
    await update.effective_chat.send_chat_action(action='upload_voice')
    await bot.send_voice(update.message.chat_id, file, reply_to_message_id=update.message.reply_to_message.id)
    pass

async def alexa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    search_term = context.match.group(1)
    if await no_can_do(update, context):
        return

    if update.message.chat.id not in [config.ID_DIOCHAN, config.ID_ASPHALTO, config.ID_TESTING, config.ID_RITALY]:
        return

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede una canzone ad alexa: {search_term}')
    await printlog(update, "chiede una canzone ad alexa", search_term)
    from youtubesearchpython import VideosSearch
    videosSearch = VideosSearch(search_term, limit=1, region='IT')
    my_video = videosSearch.result()['result'][0]
    message = f"<a href='{my_video['link']}'>{my_video['title']}</a>\n"
    message += f"<a href='{my_video['channel']['link']}'>{my_video['channel']['name']}</a> | {my_video['viewCount']['text']} ?? {my_video['publishedTime']}"
    await update.message.reply_html(message)


