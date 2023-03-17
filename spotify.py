import os
import asyncio

from spotdl import Spotdl
from spotdl.types.options import DownloaderOptions

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext, ContextTypes

import config

from spotdl.download.downloader import Downloader

from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do

# Questi erano dentro il codice di spotdl, prima o poi uso i miei
client_id = "5f573c9620494bae87890c0f08a60293"
client_secret = "212476d9b0f3472eaa762d90b19b0ba8"

# dlder_options = DownloaderOptions(output='mp3/', overwrite='force', simple_tui=False)
dlder_options: DownloaderOptions = {
    "audio_providers": ["youtube-music"],
    "lyrics_providers": ["genius", "azlyrics", "musixmatch"],
    "playlist_numbering": False,
    "scan_for_songs": False,
    "m3u": None,
    "output": "{artists} - {title}.{output-ext}",
    "overwrite": "force",
    "search_query": None,
    "ffmpeg": "ffmpeg",
    "bitrate": None,
    "ffmpeg_args": None,
    "format": "mp3",
    "save_file": None,
    "filter_results": True,
    "threads": 4,
    "cookie_file": None,
    "restrict": False,
    "print_errors": False,
    "sponsor_block": False,
    "preload": False,
    "archive": None,
    "load_config": True,
    "log_level": "INFO",
    "simple_tui": True,
    "fetch_albums": False,
    "id3_separator": "/",
    "ytm_data": False,
    "add_unavailable": False,
    "geo_bypass": False,
    "generate_lrc": False,
    "force_update_metadata": False,
}



spotdl = Spotdl(client_id, client_secret, downloader_settings=dlder_options)

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
    
    downloader = Downloader(loop=asyncio.get_event_loop(), settings=dlder_options)

    blocking_download = asyncio.to_thread(downloader.search_and_download, songs[0])
    song, path = await blocking_download

    caption = f"{song.display_name}\nfrom {song.album_name} ({song.year})"
    try:
        await update.message.reply_audio(audio=open(path, "rb"), caption=caption)
    except Exception as e:
        await update.message.reply_text(f"Niente non riesco a mandare il file, amen.")

    await msg.delete()
    os.remove(path) 
 