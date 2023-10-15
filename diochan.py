import datetime
import html
import json
import random
import tempfile
from html import escape as parsequote

import httpx
from database import TensorMessage, Quote
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ContextTypes

import config
from utils import (
    expand,
    extract_status_change,
    get_now,
    no_can_do,
    printlog,
)

# Per le quote
last_search = ""
last_results = []
index_results = 0

# Tensor
async def save_tensor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(update.message.text) <= 25:
        return

    message_to_add = update.message.text

    if message_to_add.startswith("/"):
        return
    if message_to_add == "":
        return

    newtensor = TensorMessage.create(tensor_text=message_to_add)
    newtensor.save()

async def random_tensor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return

    if update.message.chat.id not in [config.ID_DIOCHAN, config.ID_NINJA]:
        return
    await printlog(update, "invoca tensorbot")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} invoca tensorbot!')

    tensors = TensorMessage.select()
    tensor_message = random.choice(tensors).tensor_text

    await update.message.reply_text(tensor_message, quote=False)

# Quotes
async def search_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    def get_quotes(searchterm=""):
        global last_search
        global last_results
        global index_results

        if searchterm == "":  # nessuna ricerca
            quotes = Quote.select()
            quote = random.choice(quotes).quote_text

            return ("0", "0", quote)


        else:  # qualcosa da cercare
            if searchterm == last_search:  # abbiamo appena cercato
                if index_results + 1 == len(last_results):  # ultima
                    index_results = 0
                    return (str(len(last_results)), str(len(last_results)), last_results[len(last_results) - 1])
                index_results += 1
                return (str(index_results), str(len(last_results)), last_results[index_results - 1])
            else:
                last_search = searchterm
                query = searchterm
                last_results = []
                index_results = 0

                quotes = Quote.select().where(Quote.quote_text.contains(query))

                if not quotes:
                    last_search = ""
                    return ("-1", "-1", "-1")

                for quote in quotes:
                    last_results.append(quote.quote_text)

                index_results += 1
                return (str(index_results), str(len(last_results)), last_results[index_results - 1])

    global last_search
    if update.message.chat.id != config.ID_DIOCHAN:
        return
    await printlog(update, "cerca una quote di diochan")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} cerca una quote')
    searchquery = " ".join(context.args)

    if searchquery == "-list":
        if update.effective_user.id not in config.ADMINS:
            return
        quotes = Quote.select()
        mymessage = ""
        for quote in quotes:
            mymessage += f"{quote.quote_text}\n-----\n"

        URL = "https://hastebin.com"
        response = requests.post(URL + "/documents", mymessage.encode('utf-8'))

        r = json.loads(response.text)

        pastebin_url = f"{URL}/raw/{r['key']}"
        await update.message.reply_html(f'<a href="{pastebin_url}">Ecco a te</a>', quote=False)
        return



    quote = get_quotes(searchquery)  # ('1', '8', 'text')
    if quote[0] == "0":  # random quote
        myquote = parsequote(quote[2])
        await update.message.reply_html(myquote, quote=False)

    elif quote[0] == "-1":  # Nessun risultato
        await update.message.reply_html("Nessun risultato trovato", quote=False)

    elif quote[0] == quote[1]:  # ultima quote
        myquote = parsequote(quote[2])
        message_text = f"Quote {quote[0]} di {quote[1]}: ultima\n{myquote}"
        await update.message.reply_html(message_text, quote=False)
        last_search = ""

    else:
        myquote = parsequote(quote[2])
        message_text = f"Quote {quote[0]} di {quote[1]}\n{myquote}"
        await update.message.reply_html(message_text, quote=False)

async def add_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    if update.message.chat.id != config.ID_DIOCHAN:
        return
    await printlog(update, "vuole aggiungere una quote di diochan")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} vuole aggiungere una quote')


    if not context.args:  # il messaggio non ha testo

        if update.message.reply_to_message.text:  # è una reply
            user_id = update.message.reply_to_message.from_user.id
            chat_id = update.message.chat.id
            text_to_add = update.message.reply_to_message.text

            member = await context.bot.get_chat_member(chat_id, user_id)

            nickname = member.user.first_name
            if member.user.last_name:
                nickname = nickname + " " + member.user.last_name

            quote_to_add = "<" + nickname + "> " + text_to_add

        else:  # non è una reply
            await update.message.reply_text('Addami sta minchia')
            return

    else:  # il messaggio è dopo il comando
        text_to_add = " ".join(context.args)


        quote_to_add = text_to_add

    newquote = Quote.create(quote_text=quote_to_add)
    newquote.save()

    await update.message.reply_text('Fatto', quote=False)

# Diochan
async def diochan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    if update.effective_chat.id not in [config.ID_DIOCHAN, config.ID_TESTING, config.ID_NINJA]:  # Solo su diochan
        return
    chiave = config.CHIAVE_DIOCHAN
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} vuole postare su diochan')
    await printlog(update, "vuole postare su diochan")
    listaboard = ['b', 's', 'x', 'hd', '420', 'aco', 'v', 'cul', 'yt', 'ck', 'mu', 'pol', 'p', 'sug']
    board = ""
    message = " ".join(context.args)

    for b in listaboard:
        if f'/{b}/' in message[:5]:
            board = b
            message = message[(len(b) + 2):]
        elif f'/{b}' in message[:5]:
            board = b
            message = message[(len(b) + 1):]

    if not board:
        await context.bot.send_message(update.message.chat.id, "Devi specificare una board")
        return

    try:
        if update.message.reply_to_message.photo:
            if update.message.reply_to_message.caption:
                message = update.message.reply_to_message.caption
            else:
                if len(context.args[1:]) > 0:
                    message = " ".join(context.args[1:])
                else:
                    message = "Ho il culo pieno di ovatta"
            picture = update.message.reply_to_message.photo[-1]
            # tempphoto = tempfile.mktemp(suffix='.jpg')
            tempphoto = tempfile.NamedTemporaryFile(suffix='.jpg')
            actual_picture = await picture.get_file()
            await actual_picture.download_to_drive(custom_path=tempphoto.name)

            baseurl = 'https://www.diochan.com/'
            referurl = f'{baseurl}{board}/index.html'

            HEADERS = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36',
                'referer': referurl
            }
            # delpass = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(8))
            delpass = chiave
            # delpass = f"emily-{update.message.reply_to_message.id}"
            payload = {
                "name": "",
                "email": "",
                "subject": "",
                "body": message,
                "imageurl": "",
                "embed": "",
                "password": delpass,
                "json_response": "0"
            }

            r = requests.get(baseurl + board + "/", headers=HEADERS)
            soup = BeautifulSoup(r.text, 'html.parser')

            # Get every input
            for tag in soup.find_all('input'):
                tag = str(tag).strip()
                htmltag = BeautifulSoup(tag, 'html.parser').input
                try:
                    name = str(htmltag['name'])
                    value = str(htmltag['value'])
                except (ValueError, KeyError):
                    continue
                if name not in ['report', 'delete', 'password']:
                    payload[name] = value

            # Get every textarea
            for tag in soup.find_all('textarea'):
                tag = str(tag).strip()
                htmltag = BeautifulSoup(tag, 'html.parser').textarea
                try:
                    name = str(htmltag['name'])
                    value = htmltag.string
                except ValueError:
                    continue
                if name not in ['body']:
                    payload[name] = value

            # Textboox upload multipart-encoded files with Requests
            image_file_descriptor = tempphoto
            files = {'file': image_file_descriptor}
            posturl = f'{baseurl}post.php'
            richiesta = requests.post(posturl, headers=HEADERS, data=payload, files=files)
            image_file_descriptor.close()
            response = richiesta.json()
            print(response)

            try:
                thread_id = response["id"]
                link = f'https://www.diochan.com/{board}/res/{thread_id}.html'
                reply_link = f"Postato! {link}"
                print(f'{get_now()} Fatto! {reply_link} - pass per cancellare: {delpass}')
                await context.bot.send_message(update.message.chat.id, reply_link)

            except Exception as e:
                print(e)
                await context.bot.send_message(update.message.chat.id, richiesta.text)
            tempphoto.close()
        else:
            await context.bot.send_message(update.message.chat.id, "Devi rispondere ad una foto con didascalia")

    except AttributeError:
        return

async def ascendi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    await printlog(update, "A S C E N D E")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} A S C E N D E')
    message = ' '.join(context.args)
    if not message:
        try:
            message = update.message.reply_to_message.text
        except AttributeError:
            await update.message.reply_text("O rispondi a qualcosa o scrivi qualcosa. S C E M O.")
            return

    newmessage = "```\n" + expand(message.upper()) + "\n```"

    string = ''.join(newmessage)
    await update.message.reply_markdown_v2(f'{string}', quote=False)
    return

async def mon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    if update.message.chat.id != config.ID_DIOCHAN:
        return

    if "numero_di_mon" not in context.bot_data:
        context.bot_data["numero_di_mon"] = 0

    mon = context.bot_data["numero_di_mon"]
    mon += 1
    context.bot_data["numero_di_mon"] = mon

    await update.message.reply_html(f'<i>({mon})</i>', quote=False)

    if mon % 100 == 0:
        await update.message.reply_text('PEPPEREPÈ!!! - Si vede che vi manca, eh?!', quote=False)

    await printlog(update, "ha nominato mon", mon)

async def get_thread_from_dc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in config.ADMINS:
        return
    BOARDS = ['b', 's', 'x', 'hd', 'aco', 'v', 'cul', 'yt', 'pol']

    async def get_last_threads_from_board(board):
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f'https://www.diochan.com/{board}/catalog.json')
            response.raise_for_status()
            return response.json()

    if context.args[0] not in BOARDS:
        await update.message.reply_text(f"Board non valida. Devi usare una di queste: {', '.join(BOARDS)}")
        return


    if len(context.args) < 2:
        await update.message.reply_text("Devi specificare il numero del thread")
        return

    board = context.args[0]
    thread_no = int(context.args[1])

    boards = await get_last_threads_from_board(board)

    post = []
    for page in boards:
        for thread in page['threads']:
            if thread['no'] == thread_no:
                t = {
                    'board': board,
                    'thread': thread['no'],
                    'time': thread['time'],
                    'title': thread.get('sub'),
                    'text': thread['com'],
                    'thread_url' : f"https://www.diochan.com/{board}/res/{thread['no']}.html"
                }

                if thread.get('tim'):
                    t['image_url'] = f"https://www.diochan.com/{board}/src/{thread['tim']}{thread['ext']}"
                    t['is_video'] = False

                elif thread.get('embed'):
                    t['is_video'] = True
                    youtube_id = thread['embed'].split('"')[11][39:]
                    t['image_url'] = f'http://i3.ytimg.com/vi/{youtube_id}/hqdefault.jpg'
                    t['video_url'] = f"https://www.youtube.com/watch?v={youtube_id}"
                post.append(t)

    if not post:
        await update.message.reply_html("Thread non trovato")
        return

    await printlog(update, 'richiede un post da diochan', f"/{board}/ | No.{thread_no}")

    for thread in post:
        timestamp = datetime.datetime.fromtimestamp(thread['time']).strftime('%d/%m/%Y %H:%M')
        text = thread['text']
        if len(text) > 2000:
            text = text[:2000] + "..."
        link = f"<a href='{thread['thread_url']}'>/{thread['board']}/ | No.{thread['thread']}</a> | {timestamp}"

        if thread['is_video']:
            link += f"\n<a href='{thread['video_url']}'>[YouTube]</a>"

        text = html.unescape(text)
        text = text.replace('<br/>','\n').replace('<span class="quote">', '').replace('<span class="spoiler">', '').replace('</span>', '')
        message = f"{link}\n{text}"

        await update.message.reply_html(text=message)

async def greet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != config.ID_DIOCHAN2:
        return

    # https://docs.python-telegram-bot.org/en/stable/examples.chatmemberbot.html
    result = extract_status_change(update.chat_member)

    if result is None:
        return
    was_member, is_member = result

    greetings = context.chat_data.get('greeting', 'Benvenuto $FIRST_NAME!')
    greeting_pic = context.chat_data.get('greeting_pic')

    first_name = update.chat_member.new_chat_member.user.first_name if update.chat_member.new_chat_member.user.first_name else ''
    last_name = update.chat_member.new_chat_member.user.last_name if update.chat_member.new_chat_member.user.last_name else ''
    username = update.chat_member.new_chat_member.user.username if update.chat_member.new_chat_member.user.username else ''
    chat_title = update.effective_chat.title if update.effective_chat.title else ''

    greetings = greetings.replace('$FIRST_NAME', first_name)
    greetings = greetings.replace('$LAST_NAME', last_name)
    greetings = greetings.replace('$USERNAME', username)
    greetings = greetings.replace('$CHAT_TITLE', chat_title)

    if not was_member and is_member:
        await printlog(update, 'è entrato su diochan2')
        if greeting_pic:
            await update.effective_chat.send_photo(greeting_pic, caption=greetings, parse_mode='HTML')
        else:
            await update.effective_chat.send_message(greetings)
    elif was_member and not is_member:
        await printlog(update, 'è uscito da diochan2')
        await update.effective_chat.send_message('👋')

async def set_greet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != config.ID_DIOCHAN2:
        return

    if len(context.args) < 1:
        await update.message.reply_text("Devi specificare il messaggio di benvenuto")
        return
   
    if '-help' in context.args:
        await update.message.reply_text("Puoi usare le seguenti variabili:\n$FIRST_NAME\n$LAST_NAME\n$USERNAME\n$CHAT_TITLE")
        return

    context.chat_data['greeting'] = ' '.join(context.args)
    await update.message.reply_text("Messaggio di benvenuto impostato")

async def set_greet_pic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != config.ID_DIOCHAN2:
        return

    if '-delete' in context.args:
        context.chat_data['greeting_pic'] = None
        await update.message.reply_text("Immagine di benvenuto rimossa")
        return

    if update.message.reply_to_message:
        if update.message.reply_to_message.photo:
            greeting_pic_id = f"{update.message.reply_to_message.photo[-1].file_id}"

            context.chat_data['greeting_pic'] = greeting_pic_id
            await update.message.reply_text("Immagine di benvenuto impostata")
        else:
            await update.message.reply_text("Devi rispondere ad un'immagine")
    else:
        await update.message.reply_text("Devi rispondere ad un'immagine")
