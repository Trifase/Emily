import json
import pprint
import random
import time
import urllib

import asyncpraw
import ffmpy
import requests
from asyncprawcore.exceptions import Forbidden, NotFound, Redirect
from bs4 import BeautifulSoup
from telegram import InputMediaPhoto, InputMediaVideo, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

import config
from scrapers import file_in_limits
from utils import get_now, no_can_do, printlog


async def reddit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    start_time = time.perf_counter()
    # reddit = asyncpraw.Reddit(client_id=config.REDDIT_ID, client_secret=config.REDDIT_SECRET, user_agent="Emily Bot", username=config.REDDIT_USERNAME, password=config.REDDIT_PASSWORD)
    reddit = asyncpraw.Reddit(
        client_id=config.REDDIT_ID,
        client_secret=config.REDDIT_SECRET,
        user_agent="Emily Bot"
        )

    try:
        subreddit_name = context.args[0]
    except IndexError:
        await update.message.reply_html("Specifica un subreddit.")
        await reddit.close()
        return

    if subreddit_name.lower().startswith("r/"):
        subreddit_name = subreddit_name[2:]
    await printlog(update, "cerca su", f"r/{subreddit_name}")
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} cerca su r/{subreddit_name}')
    n = 0
    try:
        if len(context.args) > 1 and context.args[1] not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "-list"]:
            await update.message.reply_html("i 👏 subreddit 👏 non 👏 hanno 👏 gli 👏 spazi")
            await reddit.close()
            return

        if context.args[1] == '-list':
            print("Chiesta lista contenuti")
            message = ""
            listapost = await reddit.subreddit(subreddit_name, fetch=True)
            postlist = [sub async for sub in listapost.hot(limit=20)]
            i = 1
            for post in postlist:
                if len(post.title) > 50:
                    title = post.title[:50] + "..."
                else:
                    title = post.title
                message += f"<a href='{post.url}'>[{str(i).zfill(2)}]</a> {title}\n"
                i += 1
            await update.message.reply_html(message, disable_web_page_preview=True)
            await reddit.close()
            return
        elif int(context.args[1]) in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]:
            n = int(context.args[1])
            print(f"Chiesto contenuto specifico: {n}")
        else:
            pass
    except IndexError:
        pass


    try:
        listapost = await reddit.subreddit(subreddit_name, fetch=True)
        if n:
            submission = [sub async for sub in listapost.hot(limit=20)][n - 1]
        else:
            submission = random.choice([sub async for sub in listapost.hot(limit=20) if not sub.is_self])
    except Redirect:
        await update.message.reply_html("Subreddit non trovato")
        await reddit.close()
        return
    except IndexError:
        await update.message.reply_html("Non trovo immagini su questo subreddit")
        await reddit.close()
        return
    except NotFound:
        await update.message.reply_html("Errore: subreddit non trovato")
        await reddit.close()
        return
    except Forbidden:
        await update.message.reply_html("Errore: subreddit privato")
        await reddit.close()
        return

    submission._fetch()  # Popolo la submission

    if hasattr(submission, "crosspost_parent"):  # controllo se è un crosspost
        submission = await reddit.submission(id=submission.crosspost_parent.split("_")[1])

    permalink = f"https://reddit.com{submission.permalink}"
    title = submission.title
    sub = f"r/{submission.subreddit}"
    upvotes = submission.score
    url = submission.url
    gallery = []

    await printlog(update, "trova il seguente link", permalink)

    if submission.is_self:
        if len(submission.selftext) > 900:
            text = f"{submission.selftext[:900]}... <a href='{permalink}'>[continua su reddit]</a>"
        else:
            text = submission.selftext
        message = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n<b>{title}</b>\n{text}"
        await update.message.reply_html(message, disable_web_page_preview=True)
        await reddit.close()
        return

    if "youtube" in url or 'youtu.be' in url:
        await update.message.reply_html(f"<b>{sub}: {title}</b>\n{upvotes} upvotes\n\n{url}", disable_web_page_preview=False)
        await reddit.close()
        return

    if "redd.it" in url:
        if "gallery" in url:
            ids = [i['media_id'] for i in submission.gallery_data['items']]

            for reddit_id in ids:
                url = submission.media_metadata[reddit_id]['p'][0]['u']
                url = url.split("?")[0].replace("preview", "i")
                if await file_in_limits(url):
                    gallery.append(url)
            await context.bot.send_media_group(reply_to_message_id=update.message.message_id, chat_id=update.message.chat.id, media=[InputMediaPhoto(url) for url in gallery[:10]])

        else:
            if submission.url.endswith(".gif"):
                url = submission.preview['images'][0]['variants']['mp4']['source']['url']
                caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}"
                if not await file_in_limits(url):
                    await update.message.reply_html(f"Il file è troppo grande, ecco un <a href='{url}'>link</a>\n{caption}")
                else:
                    await update.message.reply_video(video=url, caption=caption, parse_mode='HTML')
            else:
                if submission.url.startswith("https://v.redd"):
                    # v.redd.it ha audio e video separati. Alternativamente bisogna scaricare l'audio a parte e unirli via ffmpeg.

                    url = submission.media['reddit_video']['fallback_url']
                    url = url.replace("?source=fallback", "")
                    url_audio = url.replace("1080", "audio")
                    url_audio = url_audio.replace("720", "audio")
                    url_audio = url_audio.replace("360", "audio")
                    width = submission.media['reddit_video']['width']
                    height = submission.media['reddit_video']['height']

                    # pprint.pprint(vars(submission))
                    try:
                        link_thumb = submission.preview['images'][0]['source']['url']
                    except AttributeError:
                        link_thumb = "https://i.imgur.com/znuE4Fn.jpg"

                    caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}\n\nIl video arriva in un attimo"
                    messaggio = await update.message.reply_photo(photo=link_thumb, caption=caption, parse_mode='HTML')
                    download = True

                    try:
                        if '-nodownload' in context.args:
                            download = False
                    except IndexError:
                        download = True

                    if download:


                        video_file = "reddit/video.mp4"
                        audio_file = "reddit/audio.mp4"

                        try:
                            # Proviamo a guardare se c'è il file audio
                            link_audio = urllib.request.urlopen(url_audio)  #nosec
                        except urllib.error.HTTPError:  # Se non c'è passiamo direttamente il video come url, inutile scaricare e muxare
                            caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}\n\nNo audio (and reddit is dumb)."
                            await context.bot.edit_message_media(chat_id=update.message.chat.id, message_id=messaggio.message_id, media=InputMediaVideo(media=url, caption=caption, parse_mode='HTML'))
                            await reddit.close()
                            return

                        print(f"{get_now()} Unisco audio e video con FFmpeg per l'upload da locale")
                        link_video = urllib.request.urlopen(url)  #nosec

                        with open(video_file, "wb") as output:
                            output.write(link_video.read())

                        with open(audio_file, "wb") as output:
                            output.write(link_audio.read())

                        video_file_finale = "reddit/video_con_audio.mp4"

                        ff = ffmpy.FFmpeg(
                            # inputs={video_file: None, audio_file: None},
                            inputs={url: None, url_audio: None},
                            outputs={video_file_finale: '-y -c:v copy -c:a aac -loglevel quiet'})
                        ff.run()
                        time_elapsed = time.perf_counter() - start_time
                        caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}\n\nFinito in: {str(time_elapsed)[:4]}s\nScusate il ritardo, colpa di reddit.\n"
                        # update.message.reply_video(open(video_file_finale, "rb"), caption=caption, parse_mode='HTML')
                        await context.bot.edit_message_media(chat_id=update.message.chat.id, message_id=messaggio.message_id, media=InputMediaVideo(media=open(video_file_finale, "rb"), caption=caption, parse_mode='HTML'))
                        # bot.edit_message_caption(chat_id=update.message.chat.id, message_id=messaggio.message_id, caption=caption, parse_mode='HTML')
                        await reddit.close()
                        return

                    else:
                        caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}\n\nNo <a href='{url_audio}'>audio</a> because reddit is dumb."
                        if not await file_in_limits(url):
                            await update.message.reply_html(f"Il file è troppo grande, ecco un <a href='{url}'>link</a>\n{caption}")
                        else:
                            await update.message.reply_video(video=url, caption=caption, parse_mode='HTML', width=width, height=height)
                        await reddit.close()
                else:

                    caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}"
                    if not await file_in_limits(url):
                        await update.message.reply_html(f"Il file è troppo grande, ecco un <a href='{url}'>link</a>\n{caption}")
                    else:
                        try:
                            await update.message.reply_photo(photo=url, caption=caption, parse_mode='HTML')
                        except BadRequest:
                            await update.message.reply_html(f"Il file è troppo grande, ecco un <a href='{url}'>link</a>\n{caption}")
                    await reddit.close()


    elif "imgur" in url:
        if submission.url.endswith(".gif") or submission.url.endswith(".gifv") or submission.url.endswith(".mp4"):

            url = url.replace(".gifv", ".mp4")
            url = url.replace(".gif", ".mp4")

            caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}"
            if not await file_in_limits(url):
                await update.message.reply_html(f"Il file è troppo grande, ecco un <a href='{url}'>link</a>\n{caption}")
            else:
                await update.message.reply_video(video=url, caption=caption, parse_mode='HTML')
            await reddit.close()
        else:
            # print("Imgur")
            # print(url)
            # print(permalink)
            # url += ".jpeg"
            caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}"
            if not await file_in_limits(url):
                await update.message.reply_html(f"Il file è troppo grande, ecco un <a href='{url}'>link</a>\n{caption}")
            else:
                await update.message.reply_photo(photo=url, caption=caption, parse_mode='HTML')
            await reddit.close()
            return

    elif "gfycat" in url:

        url = submission.media['oembed']['thumbnail_url'][:-20]
        url = f"{url}-mobile.mp4"
        caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}"
        if not await file_in_limits(url):
            await update.message.reply_html(f"Il file è troppo grande, ecco un <a href='{url}'>link</a>\n{caption}")
        else:
            await update.message.reply_video(video=url, caption=caption, parse_mode='HTML')
        await reddit.close()
        return

    elif "redgifs.com" in url:

        url = submission.preview['reddit_video_preview']['fallback_url']
        caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}"
        # print(url)
        if not await file_in_limits(url):
            await update.message.reply_html(f"Il file è troppo grande, ecco un <a href='{url}'>link</a>\n{caption}")
        else:
            await update.message.reply_video(video=url, caption=caption, parse_mode='HTML')
        await reddit.close()
        return

    elif "streamable.com" in url:

        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Pull all text from the BodyText div
        video = soup.find_all('video')
        temp = video[0].get("src")
        url = "https:" + temp
        caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}"
        if not await file_in_limits(url):
            await update.message.reply_html(f"Il file è troppo grande, ecco un <a href='{url}'>link</a>\n{caption}")
        else:
            await update.message.reply_video(video=url, caption=caption, parse_mode='HTML')
        await reddit.close()
        return

    else:
        if not submission.media:
            if url.startswith("https://www.reddit.com/gallery/"):

                gallery = []
                for image in submission.media_metadata:
                    # print(image)
                    mtype = submission.media_metadata[image]['m']
                    if mtype.startswith("image"):
                        if await file_in_limits(submission.media_metadata[image]['s']['u']):
                            gallery.append(submission.media_metadata[image]['s']['u'])

                message = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n<a href='{url}'>{title}</a>"
                reply_to = await update.message.reply_html(message, quote=False, disable_web_page_preview=True)
                await context.bot.send_media_group(reply_to_message_id=reply_to.message_id, chat_id=update.message.chat.id, media=[InputMediaPhoto(url) for url in gallery[:10]])
                await reddit.close()
                return
            else:

                message = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n<a href='{url}'>{title}</a>"
                await update.message.reply_html(message, disable_web_page_preview=True)
                await reddit.close()
                return

        else:
            # pprint.pprint(vars(submission))
            print(f"{get_now()} Tipo di contenuto di reddit sconosciuto.")

            message = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}\n\n{url}"
            await update.message.reply_html(message)

            mymessage = pprint.pformat(vars(submission))
            URL = "https://hastebin.com"
            response = requests.post(URL + "/documents", mymessage.encode('utf-8'))
            r = json.loads(response.text)
            pastebin_url = f"{URL}/raw/{r['key']}"

            await context.bot.send_message(chat_id=config.ID_BOTCENTRAL, text=f'<a href="{pastebin_url}">Ecco a te</a>\nHo trovato un contenuto che non so come parsare:\n{message}', parse_mode='HTML')
            await reddit.close()
            return

    await reddit.close()
    return