# IGDB INTEGRATION
import httpx
import datetime

from telegram import Update
from telegram.ext import ContextTypes

import config
from utils import no_can_do, printlog

client_id = config.twitch_client_id
client_secret = config.twitch_client_secret

async def get_token_from_twitch(client_id, client_secret) -> str:
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"

    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://id.twitch.tv/oauth2/token",data=data)
        response.raise_for_status()
        return response.json()

async def igdb_headers(client_id, token):
    return {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}"
    }

async def igdb_request(endpoint, headers, data):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"https://api.igdb.com/v4/{endpoint}/", data=data, headers=headers)
        response.raise_for_status()
        return response.json()

async def get_games_from_igdb(search_game):
    response = await get_token_from_twitch(client_id, client_secret)
    twitch_token = response['access_token']

    headers = await igdb_headers(client_id, twitch_token)
    data = f'search "{search_game}"; fields name,category,total_rating,status,cover,first_release_date,genres.name,platforms.abbreviation,game_modes.name,themes.name; where category = 0 & version_title = null; limit 1;'
    response = await igdb_request('games', headers, data)
    games = []
    for game in response:
        g = {}
        if game.get('cover'):
            data = f'fields *; where id = {game.get("cover")};'
            cover_url = await igdb_request('covers', headers, data)
            cover_url = f"https://images.igdb.com/igdb/image/upload/t_cover_big_2x/{cover_url[0].get('image_id')}.jpg"
            g['cover'] = cover_url

        if not game.get('first_release_date'):
            g['release'] = 'Not yet released!'
        else:
            g['release'] = datetime.datetime.utcfromtimestamp(int(game['first_release_date'])).strftime('%d/%m/%Y')
            
        g['name'] = game['name']
        g['genres'] = game.get('genres')
        if g.get('genres'):
            g['genres_str'] = ', '.join([x.get('name') for x in g['genres']])
        g['platforms'] = game.get('platforms')
        if g.get('platforms'):
            g['platforms_str'] = ', '.join([x.get('abbreviation') for x in g['platforms']])
        g['themes'] = game.get('themes')
        if g.get('themes'):
            g['themes_str'] = ', '.join([x.get('name') for x in g['themes']])
        games.append(g)
    return games

def format_game(g: dict) -> str:
    game_str = ''
    game_str += f"Name: {g.get('name')}"
    game_str += f"\nRelease: {g.get('release')}"

    if g.get('platforms_str'):
        game_str += f"\nPlatforms: {g.get('platforms_str')}"
    if g.get('genres_str'):
        game_str += f"\nGenres: {g.get('genres_str')}"
    if g.get('themes_str'):
        game_str += f"\nThemes: {g.get('themes_str')}"
    # if g.get('cover'):
    #     game_str += f"\nCover: {g.get('cover')}"
    return game_str

async def giochino(update: Update, context: ContextTypes.DEFAULT_TYPE, poll_passed=False) -> None:
    if await no_can_do(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /giochino <game>")
        return
    
    search_game = ' '.join(context.args)

    await printlog(update, "cerca un giochino", search_game)

    games = await get_games_from_igdb(search_game)

    if not games:
        await update.message.reply_text("No games found!")
        return
    
    for game in games:
        if game.get('cover'):
            await update.message.reply_photo(game.get('cover'), caption=format_game(game))
        else:
            await update.message.reply_text(format_game(game))