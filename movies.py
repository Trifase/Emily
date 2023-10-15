
import requests
from aiographql.client import GraphQLClient, GraphQLRequest, GraphQLResponse
from imdb import Cinemagoer
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import ContextTypes

from utils import no_can_do, printlog

# async def get_doveguardo_result(titolo: str, index_n):

#     just_watch = JustWatch(country='IT')

#     results = just_watch.search_for_item(query=titolo)

#     if not results['items']:
#         raise ValueError('Movie not found')
#     providers = {}
#     provider_details = just_watch.get_providers()
#     for p in provider_details:
#         providers[p['short_name']] = p['clear_name'].replace('Channel', 'Ch.')

#     offerte = {}
#     message = ""
#     imdb_id = 0
#     imdb_url = ""
#     imdb_text = ""

#     title = results['items'][int(index_n)]

#     name = title['full_path'].split('/')[-1]
#     if title.get('poster'):
#         poster_id = title['poster'][:-9]
#         poster_url = f"https://images.justwatch.com/{poster_id}s592/{name}.jpg"
#     else:
#         poster_url = "https://i.imgur.com/FEbLwXk.png"

#     name_title = f"<b>{title['title']}</b>, <i>{title['object_type']}</i>, {title['original_release_year']}"


#     id = title['id']
#     infos = just_watch.get_title(title_id=id, content_type=title['object_type'])
#     external_ids = infos['external_ids']
#     for ids in external_ids:
#         if ids['provider'] == 'imdb':
#             imdb_id = ids['external_id']
#             imdb_url = f'https://www.imdb.com/title/{imdb_id}/'
#             rarbg_url = f'https://proxyrarbg.org/torrents.php?imdb={imdb_id}'
#             break

#     for k in title['scoring']:
#         if k['provider_type'] == 'imdb:score':
#             if imdb_url:
#                 imdb_text = f"{k['value']}/10 su <a href='{imdb_url}'>IMDb</a>\n<a href='{rarbg_url}'>⬇️ Cerca torrent</a>\n"
#             else:
#                 imdb_text = f"{k['value']}/10 su IMDb\n<a href='{rarbg_url}'>⬇️ Cerca torrent</a>\n"

#     if not imdb_text:
#         imdb_text = "<i>No IMDb result</i>"
#     streaming_places = ""

#     if title.get('offers'):
#         for offer in title['offers']:
#             if offer['monetization_type'] == 'flatrate':
#                 offer_type = "Streaming"
#             elif offer['monetization_type'] == 'buy':
#                 offer_type = "Buy"
#             elif offer['monetization_type'] == 'rent':
#                 offer_type = "Rent"
#             elif offer['monetization_type'] == 'ads':
#                 offer_type = "Streaming (ads)"
#             else:
#                 offer_type = offer['monetization_type']

#             if offer['package_short_name'] == 'dnp':
#                 urls = offer['urls']['standard_web'].split("u=")
#                 url = urls[1].split("&")
#                 url = url[0]
#             else:
#                 url = offer['urls']['standard_web']

#             if url not in offerte:
#                 offerte[url] = {"providers": "", "type": set(), "stagioni": 0}
#             offerte[url]['providers'] = offer['package_short_name']
#             offerte[url]['type'].add(offer_type)

#         for url, details in offerte.items():
#             lista_tipi = ""
#             for t in details['type']:
#                 lista_tipi += t + ", "
#             provider = providers.get(details['providers'], details['providers'])
#             streaming_places += f"[{provider}]: <a href='{requests.utils.unquote(url)}'>{lista_tipi[:-2]}</a>\n"

#     else:
#         streaming_places = "Non ho trovato posti in cui guardarlo, scusa"

#     message = f"{name_title}\n{imdb_text}\n{streaming_places}"



#     return message, poster_url, len(results['items'])

async def get_titles(query_text: str, format=True) -> dict:

    client = GraphQLClient(endpoint='https://apis.justwatch.com/graphql')

    query = """
    query GetSuggestedTitles($country: Country!, $language: Language!, $first: Int!, $filter: TitleFilter) {
    popularTitles(country: $country, first: $first, filter: $filter) {
        edges {
        node {
            ...SuggestedTitle
            __typename
        }
        __typename
        }
        __typename
    }
    }

    fragment SuggestedTitle on MovieOrShow {
    id
    objectType
    objectId
    content(country: $country, language: $language) {
        fullPath
        title
        originalReleaseYear
        posterUrl
        fullPath
        __typename
    }
    __typename
    }
    """

    variables = {
    "country": "IT",
    "language": "it",
    "first": 5,
    "filter": {
        "searchQuery": f"{query_text}"
    }
    }

    request = GraphQLRequest(query=query, variables=variables, validate=False)

    response: GraphQLResponse = await client.query(request=request)
    if format:
        return format_titles(response.data)
    else:
        return response.data

async def get_title_detail(fullpath: str, format=True) -> dict:

    client = GraphQLClient(endpoint='https://apis.justwatch.com/graphql')

    query = """
        query GetUrlTitleDetails($fullPath: String!, $country: Country!, $language: Language!, $platform: Platform! = WEB, $filterAll: OfferFilter!) {
          urlV2(fullPath: $fullPath) {
            id
            heading1
            node {
              id
              ... on MovieOrShowOrSeason {
                objectType
                objectId
                flatrateOffers: offers(country: $country, platform: $platform, filter: $filterAll) {
                  id
                  standardWebURL
                  package {
                    id
                    packageId
                    clearName
                    monetizationTypes
                    technicalName
                  }
                }
                content(country: $country, language: $language) {
                  externalIds {
                    imdbId
                  }
                  fullPath
                  fullPosterUrl: posterUrl(profile: S718, format: JPG)
                  scoring {
                    imdbScore
                    imdbVotes
                  }
                  ... on SeasonContent {
                    seasonNumber
                  }
                }
              }
              ... on Show {
                totalSeasonCount
              }
              ... on Season {
                totalEpisodeCount
              }
            }
          }
        }

        """

    variables = {
    "platform": "WEB",
    "fullPath": f"{fullpath}",
    "language": "it",
    "country": "IT",
    "filterAll": {
        "monetizationTypes": [
            "FLATRATE",
            "FLATRATE_AND_BUY",
            "ADS",
            "FREE",
            "CINEMA",
            "RENT",
            "BUY"
        ],
        "bestOnly": True
        }
    }

    request = GraphQLRequest(query=query, variables=variables, validate=False)
    response: GraphQLResponse = await client.query(request=request)
    if format:
        return format_title_details(response.data)
    else:
        return response.data

def format_titles(response: dict) -> list[dict]:
    results = response['popularTitles']['edges']
    data = []
    for result in results:
        res = {}
        node = result['node']
        content = node['content']
        res['title'] = content['title']
        res['fullPath'] = content['fullPath']
        res['posterUrl'] = content['posterUrl']
        res['originalReleaseYear'] = content['originalReleaseYear']
        res['id'] = node['id']
        res['objectId'] = node['objectId']
        res['objectType'] = node['objectType']
        data.append(res)
    return data

def format_title_details(response: dict) -> list[dict]:
    results = response['urlV2']
    content = results['node']['content']
    data = {}
    data['title'] = results['heading1']
    data['id'] = results['id']
    data['full_poster_url'] = content['fullPosterUrl']
    data['imdb_id'] = content['externalIds']['imdbId']
    data['score'] = content['scoring']['imdbScore']
    data['offers'] = []
    for offer in results['node']['flatrateOffers']:
        off = {}
        off['clearname'] = offer['package']['clearName']
        off['techname'] = offer['package']['technicalName']
        off['monetization'] = offer['package']['monetizationTypes']
        off['url'] = offer['standardWebURL']
        data['offers'].append(off)
    return data

async def aggregate_justwatch_results(query: str) -> dict:
    data = []
    response = await get_titles(query)
    for result in response:
        title = result['fullPath']
        response = await get_title_detail(title)
        r = {}
        r['full_path'] = result['fullPath']
        r['id'] = result['id']
        r['title'] = result['title']
        r['year'] = result['originalReleaseYear']
        r['type'] = result['objectType']

        details = await get_title_detail(title)
        r['score'] = details['score']
        r['full_poster_url'] = details['full_poster_url']
        r['imdb_id'] = details['imdb_id']
        r['imdb_score'] = details['score']
        r['offers'] = details['offers']
        data.append(r)
    return data

async def get_doveguardo_result(titolo: str, index_n):

    results = await aggregate_justwatch_results(query=titolo)
    if not results:
        raise ValueError('Movie not found')

    title = results[int(index_n)]

    name = title['title']
    if title.get('full_poster_url'):
        poster_url = f"https://images.justwatch.com/{title.get('full_poster_url')}"
    else:
        poster_url = "https://i.imgur.com/FEbLwXk.png"

    name_title = f"<b>{name}</b>, <i>{title['type'].lower()}</i>, {title['year']}"

    imdb_text = ''
    if title.get('imdb_score') and title.get('imdb_id'):
        imdb_url = f'https://www.imdb.com/title/{title["imdb_id"]}/'
        imdb_text = f"{title['imdb_score']}/10 su <a href='{imdb_url}'>IMDb</a>\n"

    if not imdb_text:
        imdb_text = "<i>No IMDb result</i>"

    streaming_places = ''

    if title.get('offers'):
        for offer in title['offers']:
            monetization = ', '.join([x.capitalize() for x in offer['monetization']]).replace('Flatrate', 'Streaming')
            url = offer['url']
            provider = offer['clearname'].replace('Channel', 'Ch.')
            streaming_places += f"[{provider}]: <a href='{requests.utils.unquote(url)}'>{monetization}</a>\n"

    else:
        streaming_places = "Non ho trovato posti in cui guardarlo, scusa"

    message = f"{name_title}\n{imdb_text}\n{streaming_places}"

    return message, poster_url, len(results)

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

        except Exception:
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

        except Exception:
            await query.edit_message_media(message, reply_markup=reply_markup)
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
