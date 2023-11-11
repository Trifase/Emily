import datetime
from pprint import pprint

import httpx
from howlongtobeatpy import HowLongToBeat
from telegram import Update
from telegram.ext import ContextTypes

import config
from utils import no_can_do, printlog

client_id = config.twitch_client_id
client_secret = config.twitch_client_secret
itad_api_key = config.itad_api_key


async def get_token_from_twitch(client_id, client_secret) -> str:
    data = {"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://id.twitch.tv/oauth2/token", data=data)
        response.raise_for_status()
        return response.json()


async def igdb_headers(client_id, token):
    return {"Client-ID": client_id, "Authorization": f"Bearer {token}"}


async def igdb_request(endpoint, headers, data):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"https://api.igdb.com/v4/{endpoint}/", data=data, headers=headers)
        response.raise_for_status()
        return response.json()


async def itad_request(endpoint, params):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"https://api.isthereanydeal.com/{endpoint}/", params=params)
        response.raise_for_status()
        return response.json()


async def get_igdb_game(search_game, debug=False):
    response = await get_token_from_twitch(client_id, client_secret)
    twitch_token = response["access_token"]

    headers = await igdb_headers(client_id, twitch_token)
    data = f'search "{search_game}"; fields name,category,total_rating,status,cover,first_release_date,genres.name,platforms.abbreviation,game_modes.name,themes.name; where category = 0 & version_title = null; limit 3;'
    response = await igdb_request("games", headers, data)
    if debug:
        pprint("[IGDB] response")
        pprint(response)
    games = []
    selected_game = response[0]
    for game in response:
        if game.get("name").lower() == search_game.lower():
            if debug:
                pprint(
                    f"{game.get('name').lower()} == {search_game.lower()}: {game.get('name').lower() == search_game.lower()}"
                )
            selected_game = game
            break

    game = selected_game
    g = {}
    if game.get("cover"):
        data = f'fields *; where id = {game.get("cover")};'
        cover_url = await igdb_request("covers", headers, data)
        cover_url = f"https://images.igdb.com/igdb/image/upload/t_cover_big_2x/{cover_url[0].get('image_id')}.jpg"
        g["cover"] = cover_url

    if not game.get("first_release_date"):
        g["release"] = "Not yet released!"
    else:
        g["release"] = datetime.datetime.utcfromtimestamp(int(game["first_release_date"])).strftime("%d/%m/%Y")

    g["name"] = game["name"]
    g["genres"] = game.get("genres")
    if g.get("genres"):
        g["genres_str"] = ", ".join([x.get("name") for x in g["genres"]])
    g["platforms"] = game.get("platforms")
    if g.get("platforms"):
        g["platforms_str"] = ", ".join([x.get("abbreviation") for x in g["platforms"]])
    g["themes"] = game.get("themes")
    if g.get("themes"):
        g["themes_str"] = ", ".join([x.get("name") for x in g["themes"]])
    if game.get("total_rating"):
        g["rating"] = game.get("total_rating")
    games.append(g)
    return games


async def get_hltb_game(search_game, debug=False):
    hltb_results = await HowLongToBeat().async_search(search_game)

    if hltb_results is not None and len(hltb_results) > 0:
        hltb_game = max(hltb_results, key=lambda element: element.similarity)
        if debug:
            pprint("[HLTB] hltb_game")
            pprint(hltb_game.__dict__)
        g = {}
        g["hltb_story"] = hltb_game.main_story
        g["hltb_extra"] = hltb_game.main_extra
        g["hltb_completionist"] = hltb_game.completionist
        return g
    else:
        return None


async def get_itad_game(search_game, debug=False):
    req = await itad_request("v02/game/plain", {"key": itad_api_key, "shop": "steam", "title": search_game})
    if debug:
        pprint("[ITAD] plain")
        pprint(req)
    try:
        plain = req["data"]["plain"]
    except ValueError:
        return None

    params = {
        "key": itad_api_key,
        "country": "IT",
        "plains": plain,
    }
    overview = await itad_request("v01/game/overview", params=params)
    if debug:
        pprint("[ITAD] overview")
        pprint(overview)

    g = {}
    data = overview["data"][plain]
    g["best_price"] = data["price"]["price"]
    g[
        "best_price_str"
    ] = f'<a href="{data["price"]["url"]}">{data["price"]["price_formatted"]} ({data["price"]["store"]})</a>'
    g["lowest_price"] = data["lowest"]["price"]
    g[
        "lowest_price_str"
    ] = f'<a href="{data["lowest"]["url"]}">{data["lowest"]["price_formatted"]} ({data["lowest"]["store"]})</a>'
    return g


async def aggregate_game(search_game, debug=False):
    games = await get_igdb_game(search_game, debug)
    if not games:
        return None
    igdb_game = games[0]

    hltb_game = await get_hltb_game(search_game, debug)
    itad_game = await get_itad_game(search_game, debug)

    game = {}
    game.update(igdb_game)
    if hltb_game:
        game.update(hltb_game)
    if itad_game:
        game.update(itad_game)
    return game


def format_game(g: dict) -> str:
    game_str = ""
    game_str += f"Name: {g.get('name')}"
    game_str += f"\nRelease: {g.get('release')}"

    if g.get("rating"):
        game_str += f"\n\nRating: {round(g.get('rating'), 2)}/100\n"

    if g.get("platforms_str"):
        game_str += f"\nPlatforms: {g.get('platforms_str')}"
    if g.get("genres_str"):
        game_str += f"\nGenres: {g.get('genres_str')}"
    if g.get("themes_str"):
        game_str += f"\nThemes: {g.get('themes_str')}"

    if g.get("hltb_story"):
        game_str += f"\n\nHow long to beat:\nMain: {g.get('hltb_story')}h | Main + Sides: {g.get('hltb_extra')}h | Completionist: {g.get('hltb_completionist')}h"

    if g.get("best_price_str"):
        game_str += f"\n\nBest price: {g.get('best_price_str')}"
    if g.get("lowest_price_str"):
        game_str += f"\nHistorical Low : {g.get('lowest_price_str')}"
    return game_str


async def giochino(update: Update, context: ContextTypes.DEFAULT_TYPE, poll_passed=False) -> None:
    if await no_can_do(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /giochino <game>")
        return
    debug = False
    search_game = " ".join(context.args)
    if "-debug" in context.args:
        debug = True
        search_game = search_game.replace("-debug", "").strip()

    await printlog(update, "cerca un giochino", search_game)

    game = await aggregate_game(search_game, debug)

    if not game:
        await update.message.reply_text("No game found!")
        return

    if game.get("cover"):
        await update.message.reply_photo(game.get("cover"), caption=format_game(game))
    else:
        await update.message.reply_text(format_game(game))
