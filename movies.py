
from justwatch import JustWatch
from imdb import Cinemagoer
import requests

from rich import print
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CallbackContext, ContextTypes


from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do

async def get_doveguardo_result(titolo: str, index_n):

    just_watch = JustWatch(country='IT')

    results = just_watch.search_for_item(query=titolo)

    if not results['items']:
        raise ValueError('Movie not found')

    providers = {
                'nfx': 'Netflix',
                'prv': 'Amazon Prime Video',
                'dnp': 'Disney+',
                'wki': 'Rakuten TV',
                'itu': 'Apple iTunes',
                'atp': 'Apple TV+',
                'hay': 'Hayu',
                'ply': 'Google Play Movies',
                'skg': 'Sky Go',
                'ntv': 'Now TV',
                'msp': 'Mediaset Play',
                'chi': 'Chili',
                'mbi': 'MUBI',
                'tvi': 'Timvision',
                'inf': 'Infinity',
                'dzn': 'DAZN',
                'ssp': 'Sky Sport',
                'rai': 'Rai Play',
                'uci': 'UCIcinemas',
                'gdc': 'GuideDoc',
                'nxp': 'Nexo+',
                'ytr': 'YouTube Premium',
                'msf': 'Microsoft Store',
                'dpe': 'Discovery+',
                'adp': 'Discovery+ Amazon Ch.',
                'vvv': 'VVVVID',
                'cts': 'Curiosity Stream',
                'dsv': 'DOCSVILLE',
                'sfx': 'Spamflix',
                'ast': 'Starz Play Amazon Ch.',
                'plx': 'Plex',
                'wow': 'WOW Presents+',
                'mgl': 'Magellan TV',
                'bhd': 'BroadwayHD',
                'fmz': 'Filmzie',
                'dkk': 'Dekkoo',
                'trs': 'True Story',
                'daf': 'DocAlliance Films',
                'hoc': 'Hoichoi',
                'amz': 'Amazon Video',
                'ptv': 'Pluto TV',
                'eve': 'Eventive',
                'atv': 'ShortsTV Amazon Ch.',
                'ctx': 'Cultpix',
                'sly': 'Serially',
                'flb': 'FilmBox+',
                'f1t': 'F1TV',
                'isa': 'Infinity Selection Amazon Ch.',
                'cga': 'CG Collection Amazon Ch.',
                'iwa': 'iWonder Full Amazon Ch.',
                'faa': 'Full Action Amazon Ch.',
                'cca': 'Cine Comico Amazon Ch.',
                'amu': 'MUBI Amazon Ch.',
                'amg': 'MGM Amazon Ch.',
                'ahy': 'Hayu Amazon Ch.',
                'hpa': 'HistoryPlay Amazon Ch.',
                'rns': 'Rai News',
                'eus': 'Eurosport',
                'ngp': 'NFL Game Pass',
                'pmp': 'Paramount+',
                'app': 'Paramount+ Amazon Ch.',
                'nlp': 'NBA League Pass',
                'tak': 'Takflix',
                'sup': 'SuperTennis',
                'twc': 'Twitch',
                'lgu': 'Lionsgate+',
                'snx': 'Sun Nxt',
                'cla': 'Classix',
                'nfa': 'Netflix basic with Ads',
                'ras': 'Rai Sport',
                'epl': 'ESPN Player'
            }

    offerte = {}
    message = ""
    imdb_id = 0
    imdb_url = ""
    imdb_text = ""

    title = results['items'][int(index_n)]

    name = title['full_path'].split('/')[-1]
    poster_id = title['poster'][:-9]
    poster_url = f"https://images.justwatch.com/{poster_id}s592/{name}.jpg"

    name_title = f"<b>{title['title']}</b>, <i>{title['object_type']}</i>, {title['original_release_year']}"


    id = title['id']
    infos = just_watch.get_title(title_id=id, content_type=title['object_type'])
    external_ids = infos['external_ids']
    for ids in external_ids:
        if ids['provider'] == 'imdb':
            imdb_id = ids['external_id']
            imdb_url = f'https://www.imdb.com/title/{imdb_id}/'
            rarbg_url = f'https://proxyrarbg.org/torrents.php?imdb={imdb_id}'
            break

    for k in title['scoring']:
        if k['provider_type'] == 'imdb:score':
            if imdb_url:
                imdb_text = f"{k['value']}/10 su <a href='{imdb_url}'>IMDb</a>\n<a href='{rarbg_url}'>⬇️ Cerca torrent</a>\n"
            else:
                imdb_text = f"{k['value']}/10 su IMDb\n<a href='{rarbg_url}'>⬇️ Cerca torrent</a>\n"

    if not imdb_text:
        imdb_text = "<i>No IMDb result</i>"
    streaming_places = ""

    if title.get('offers'):
        for offer in title['offers']:
            if offer['monetization_type'] == 'flatrate':
                offer_type = "Streaming"
            elif offer['monetization_type'] == 'buy':
                offer_type = "Buy"
            elif offer['monetization_type'] == 'rent':
                offer_type = "Rent"
            elif offer['monetization_type'] == 'ads':
                offer_type = "Streaming (ads)"
            else:
                offer_type = offer['monetization_type']

            if offer['package_short_name'] == 'dnp':
                urls = offer['urls']['standard_web'].split("u=")
                url = urls[1].split("&")
                url = url[0]
            else:
                url = offer['urls']['standard_web']

            if url not in offerte:
                offerte[url] = {"providers": "", "type": set(), "stagioni": 0}
            offerte[url]['providers'] = offer['package_short_name']
            offerte[url]['type'].add(offer_type)

        for url, details in offerte.items():
            lista_tipi = ""
            for t in details['type']:
                lista_tipi += t + ", "
            provider = providers.get(details['providers'], details['providers'])
            streaming_places += f"[{provider}]: <a href='{requests.utils.unquote(url)}'>{lista_tipi[:-2]}</a>\n"

    else:
        streaming_places = "Non ho trovato posti in cui guardarlo, scusa"

    message = f"{name_title}\n{imdb_text}\n{streaming_places}"



    return message, poster_url, len(results['items'])

async def doveguardo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    if not context.args:
        await update.message.reply_text("Inserisci un termine di ricerca")
        return

    if len(context.args) == 1:
        query = context.args[0]
    elif len(context.args) > 1:
        query = " ".join(context.args)
    else:
        await update.message.reply_text("Inserisci qualcosa da cercare.")
        return

    await printlog(update, "cerca dove guardare qualcosa", query)

    try:
        message, poster_url, max_results = await get_doveguardo_result(query, 0)

        if max_results > 5:
            max_results = 5

        keyboard = []
        keyboard.append([InlineKeyboardButton(f"{i + 1}", callback_data=f"dvg_{query};;{i}") for i in range(max_results)])
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await update.message.reply_photo(poster_url, caption=message, reply_markup=reply_markup)

        except Exception as e:
                await update.message.reply_html(message, disable_web_page_preview=True, reply_markup=reply_markup)
    except ValueError:
        await update.message.reply_html("Non ho trovato niente")


async def doveguardo_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id in context.bot_data['global_bans']:
        return
    """Parses the CallbackQuery and updates the message text."""
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query = update.callback_query
    await query.answer()

    argomenti = query.data
    searchquery, index_n = argomenti.split(";;")
    searchquery = searchquery[4:]

    try:
        message, poster_url, max_results = await get_doveguardo_result(searchquery, index_n)

        if max_results > 5:
            max_results = 5

        keyboard = []
        keyboard.append([InlineKeyboardButton(f"{i + 1}", callback_data=f"dvg_{searchquery};;{i}") for i in range(max_results)])
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_media(media=InputMediaPhoto(poster_url, caption=message), reply_markup=reply_markup)

        except Exception as e:
            await query.edit_message_media(message, disable_web_page_preview=True, reply_markup=reply_markup)
    except ValueError:
        await query.reply_html("Non ho trovato niente")


async def imdb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    if await no_can_do(update, context):
        return

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} cerca qualcosa su imdb')

    if not context.args:
        await update.message.reply_text("Inserisci un termine di ricerca")
        return

    if len(context.args) == 1:
        query = context.args[0]
    elif len(context.args) > 1:
        query = " ".join(context.args)
    else:
        await update.message.reply_text("Inserisci qualcosa da cercare.")
        return

    ia = Cinemagoer()

    searchquery = ia.search_movie(query)
    await printlog(update, "cerca qualcosa su imdb", query)
    # print(searchquery)
    try:
        movie_id = searchquery[0].movieID
    except IndexError:
        await update.message.reply_text("Non trovo un cazzo.")
        return
    movie = ia.get_movie(movie_id)
    imdb_id = movie['imdbID']
    imdb_url = f'https://www.imdb.com/title/tt{imdb_id}/'
    # print(f"{query} - {imdb_url}")
    try:
        year = movie['year']
    except KeyError:
        year = "N/A"

    titles = f"<b>{movie['localized title']}</b>, {year}"
    try:
        generi = f"{', '.join(movie['genres'])}"
    except KeyError:
        generi = ""

    try:
        rating = f"{movie['rating']}/10"
    except KeyError:
        rating = "N/A"
    try:
        tipo = movie['kind']
        if tipo == 'tv series':
            tipo = 'Una serie TV'
        elif tipo == 'movie':
            tipo = 'Un film'
    except KeyError:
        tipo = "N/A"

    try:
        regista = movie['directors'][0]['name']
    except KeyError:
        try:
            regista = movie['creator'][0]['name']
        except KeyError:
            regista = "N/A"

    imdb_url = f'https://www.imdb.com/title/tt{imdb_id}/'

    summary = ""
    summary += f"{titles}\n"
    summary += f"{tipo} di {regista}\n"
    summary += f"{rating} su <a href='{imdb_url}'>IMDb</a>\n"
    if tipo == 'Una serie TV':
        summary += f"{movie['seasons']} stagioni, {movie['series years']}\n"
    summary += f"{generi}\n"


    searchstring = f"{movie['localized title'].replace(' ', '+')}+{year}"
    for x in [':', '?', '&', '=', '%', '#', '@', '!', '$', '^', '*', '(', ')', '-', '_', '.', ',', "'"]:
        searchstring = searchstring.replace(x, '')
        
    t1_name = '[rarbg]'
    t1 = f'https://proxyrarbg.org/torrents.php?imdb=tt{imdb_id}&order=seeders&by=DESC'

    t2_name = '[1337x]'
    t2 = f'https://1337xx.to/sort-search/{searchstring}/seeders/desc/1/'

    torrents = f"<a href='{t1}'>{t1_name}</a> <a href='{t2}'>{t2_name}</a>"
    message = f"{summary}\n{torrents}"
    # print(message)
    await update.message.reply_html(message, disable_web_page_preview=True)
