import json

import random
import tempfile
import requests

from rich import print
from html import escape as parsequote
from bs4 import BeautifulSoup
from telegram import Update, Bot, InlineQueryResultArticle
from telegram.ext import Updater, CommandHandler, CallbackContext, ContextTypes
from telegram.helpers import escape_markdown
import peewee

import config
from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do, expand


# Per le quote
last_search = ""
last_results = []
index_results = 0

db = peewee.SqliteDatabase(config.DBPATH)

class TensorMessage(peewee.Model):
    tensor_text = peewee.TextField()
    tensor_id = peewee.AutoField()

    class Meta:
        database = db
        table_name = 'tensor'

class Quote(peewee.Model):
    quote_text = peewee.TextField()
    quote_id = peewee.AutoField()

    class Meta:
        database = db
        table_name = 'quotes'


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
            await update.message.reply_text(f'Addami sta minchia')
            return

    else:  # il messaggio è dopo il comando
        text_to_add = " ".join(context.args)


        quote_to_add = text_to_add

    newquote = Quote.create(quote_text=quote_to_add)
    newquote.save()

    await update.message.reply_text(f'Fatto', quote=False)


# Diochan
async def diochan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    if update.effective_chat.id not in [config.ID_DIOCHAN, config.ID_TESTING, config.ID_NINJA]:  # Solo su diochan
        return

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} vuole postare su diochan')
    await printlog(update, "vuole postare su diochan")
    listaboard = ['b', 's', 'x', 'hd', '420', 'aco', 'v', 'cul', 'yt', 'ck', 'mu', 'pol', 'p', 'sug']
    board = ""
    message = " ".join(context.args)

    for b in listaboard:
        if f'/{b}/' in message[:5]:
            board = b
            message = message[(len(b) + 2):]

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
            tempphoto = tempfile.mktemp(suffix='.jpg')
            actual_picture = await picture.get_file()
            await actual_picture.download_to_drive(custom_path=tempphoto)

            baseurl = 'https://www.diochan.com/'
            referurl = f'{baseurl}{board}/index.html'

            HEADERS = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36',
                'referer': referurl
            }
            import string
            import random
            delpass = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(8))
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
            image_file_descriptor = open(tempphoto, 'rb')
            files = {'file': image_file_descriptor}
            posturl = f'{baseurl}post.php'
            richiesta = requests.post(posturl, headers=HEADERS, data=payload, files=files)
            image_file_descriptor.close()
            response = richiesta.json()

            try:
                thread_id = response["id"]
                link = f'https://www.diochan.com/{board}/res/{thread_id}.html'
                reply_link = f"Postato! {link}"
                print(f'{get_now()} Fatto! {reply_link} - pass per cancellare: {delpass}')
                await context.bot.send_message(update.message.chat.id, reply_link)
                return
            except Exception as e:
                print(e)
                await context.bot.send_message(update.message.chat.id, richiesta.text)
                return
        else:
            await context.bot.send_message(update.message.chat.id, "Devi rispondere ad una foto con didascalia")
            return
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
        await update.message.reply_text(f'PEPPEREPÈ!!! - Si vede che vi manca, eh?!', quote=False)

    await printlog(update, "ha nominato mon", mon)



# DEPRECATED
# def infartino(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     update.message.reply_animation(open('images/infartino.mp4', 'rb'), quote=False)

# def cacca(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if no_can_do(update, context):
#         return

#     if update.effective_chat.type != 'private':
#         print("non è una chat privata")
#         if update.message.chat.id not in [config.ID_DIOCHAN, config.ID_TESTING]:
#             print("è una chat privata ma è una chat di test o diochan")
#             return

#     print(f'{get_now()} {await get_display_name(update.effective_user)} in {get_chat(update.message.chat.id)} aggiunge una cacata!')
#     import datetime

#     with open('db/cacche.json') as cacche_db:
#         cacche = json.load(cacche_db)


#         today = datetime.datetime.today().strftime('%Y-%m-%d')
#         now = datetime.datetime.now().strftime('%H:%M:%S')
#         user = str(update.effective_user.id)

#         if context.args:
#             note = " ".join(context.args)
#         else:
#             note = "Niente da rilevare"

#         if user not in cacche:
#             cacche[user] = {}

#         if today not in cacche[user]:
#             cacche[user][today] = {}

#         cacche[user][today][now] = note

#         json.dump(cacche, open('db/cacche.json', 'w'), indent=4)


#     if note != "Niente da rilevare":
#         update.message.reply_html(f"Cacca salvata! Ho aggiunto a margine: <i>{note}</i>", quote=False)
#     else:
#         update.message.reply_text(f'Cacca salvata!', quote=False)

#     return

# def lista_cacche(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

#     if no_can_do(update, context):
#         return


#     if update.effective_chat.type != 'private':
#         # print("non è una chat privata")
#         if update.message.chat.id not in [config.ID_DIOCHAN, config.ID_TESTING]:
#             # print("è una chat privata ma è una chat di test o diochan")
#             return

#     print(f'{get_now()} {await get_display_name(update.effective_user)} in {get_chat(update.message.chat.id)} chiede il registro cacate')

#     completa = False
#     data = ""
#     if context.args:
#         if context.args[0] == "-completa":
#             completa = True
#         else:
#             format = '%Y-%m-%d'
#             import datetime
#             try:
#                 datetime.datetime.strptime(context.args[0], format)
#                 data = context.args[0]
#             except ValueError:
#                 update.message.reply_text(f"Inserisci una data valida in formato YYYY-MM-DD.\nAd esempio: {datetime.datetime.today().strftime('%Y-%m-%d')}")
#                 return

#     with open('db/cacche.json') as cacche_db:
#         cacche = json.load(cacche_db)
#         user = str(update.effective_user.id)

#         if user not in cacche:
#             update.message.reply_text("Il tuo registro cacche è vuoto, mangia più fibre.")
#             return

#         lista_cacche = cacche[user]
#         registro_cacche = ""

#         if data:
#             if data not in lista_cacche:
#                 update.message.reply_text("Non ci sono cacche quel giorno.")
#                 return
#             registro_cacche += f"<b>{data}</b>\n"
#             for ora in lista_cacche[data]:
#                 registro_cacche += f"<code>|{ora[:5]}| </code><i>{lista_cacche[data][ora]}</i>\n"
#             update.message.reply_html(f"{registro_cacche}")
#             return

#         if completa:
#             for giorno in reversed(cacche[user]):
#                 registro_cacche += f"<b>{giorno}</b>\n"
#                 for ora in lista_cacche[giorno]:
#                     registro_cacche += f"<code>|{ora[:5]}| </code><i>{lista_cacche[giorno][ora]}</i>\n"
#                 registro_cacche += "\n"
#             update.message.reply_html(f"{registro_cacche}")
#             return

#         n = 0
#         for giorno in reversed(cacche[user]):
#             if n == 3:
#                 update.message.reply_html(f"{registro_cacche}")
#                 return
#             registro_cacche += f"<b>{giorno}</b>\n"
#             for ora in lista_cacche[giorno]:
#                 registro_cacche += f"<code>|{ora[:5]}| </code><i>{lista_cacche[giorno][ora]}</i>\n"
#             registro_cacche += "\n"
#             n += 1
#         update.message.reply_html(f"{registro_cacche}")
