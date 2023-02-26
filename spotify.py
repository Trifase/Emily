import os
import asyncio

from spotdl import Spotdl

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext, ContextTypes

import config

from spotdl.download import Downloader

from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do

# Questi erano dentro il codice di spotdl, prima o poi uso i miei
client_id = "5f573c9620494bae87890c0f08a60293"
client_secret = "212476d9b0f3472eaa762d90b19b0ba8"

spotdl = Spotdl(client_id, client_secret, output='mp3/')

async def spoty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    url = context.match.group(0)
    if 'album' in url and 'spotify:track:' in url:
        song_uid = url.split('spotify:track:')[-1]
        url = f"https://open.spotify.com/track/{song_uid}"

    results = None
    if url:
        try:
            songs = spotdl.search([url])
            results = spotdl.get_download_urls(songs)[0]
        except Exception as e: 
            await update.message.reply_text(f"Non capisco:  {e}")

    if not results:
        await update.message.reply_text(f"Non riesco a trovarla su youtube music per scaricarla, scusami.")
        return

    await printlog(update, "posta una canzone di spotify", results)
    msg = await update.message.reply_text(f"Arriva, dammi un minuto.")
    
    downloader = Downloader(loop=asyncio.get_event_loop(), overwrite='force', output='mp3/')

    blocking_download = asyncio.to_thread(downloader.search_and_download, songs[0])
    song, path = await blocking_download

    caption = f"{song.display_name}\nfrom {song.album_name} ({song.year})"
    await update.message.reply_audio(audio=open(path, "rb"), caption=caption)

    await msg.delete()
    os.remove(path) 
 