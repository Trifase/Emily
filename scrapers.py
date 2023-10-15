import datetime
import json
import logging
import pprint
import random
import re
import shutil
import tempfile
import time
import traceback
import urllib
import urllib.request
from urllib import parse
from uuid import uuid4

import asyncpraw
import ffmpy
import httpx
import instaloader
import pymediainfo
import pytz
import requests
import tweepy
import wikipedia as wkp
import yt_dlp
from bs4 import BeautifulSoup
from instaloader import BadResponseException, Profile, StoryItem
from requests_html import AsyncHTMLSession
from rich import print as cprint
from telegram import (
    InlineQueryResultArticle,
    InlineQueryResultVideo,
    InputMediaPhoto,
    InputMediaVideo,
    InputTextMessageContent,
    Update,
)
from telegram.error import BadRequest
from telegram.ext import ContextTypes

import config
from utils import alert, get_display_name, get_now, no_can_do, printlog

local_tz = pytz.timezone('Europe/Rome')
logger = logging.getLogger()

def utc_to_local(utc_dt):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)

async def get_facebook_video_info(url) -> dict:
    video_data = {}

    asession = AsyncHTMLSession()
    try:
        response = await asession.get(url)
        await response.html.arender()

        sd_url_pattern = '\"playable_url\":\"(.+?)\"'
        hd_url_pattern = '\"playable_url_quality_hd\":\"(.+?)\"'
        title_pattern = '\"text\":\"(.+?)\"'

        hd_url = None
        sd_url = None
        title = None


        try:
            hd_url = re.search(hd_url_pattern, response.html.html).group(1).replace('\/', '/').replace('\\u0025', '%')
        except Exception:
            pass

        try:
            sd_url = re.search(sd_url_pattern, response.html.html).group(1).replace('\/', '/').replace('\\u0025', '%')
        except Exception:
            pass

        try:
            title = re.search(title_pattern, response.html.html).group(1)
        except Exception:
            pass

        # print(hd_url)
        # print(sd_url)
        # print(title)

        video_data['title'] = title
        video_data['sd_url'] = sd_url
        video_data['hd_url'] = hd_url
    except Exception as e:
        # print(sd_url, hd_url, title)
        print(e)
    return video_data

async def file_in_limits(url, debug=False) -> bool:
    info = requests.head(url)
    if ('mp4' in info.headers["Content-Type"]):
        if (int(info.headers["Content-Length"]) <= 20000000):

            if debug:

                print(url)
                print("E' nei limiti")
                pprint.pprint(info.headers)
            return True

    if ('image' in info.headers["Content-Type"]):
        if (int(info.headers["Content-Length"]) <= 5000000):
            if debug:
                print(url)
                pprint.pprint(info.headers)
                print("E' nei limiti")
            return True

    if debug:
        print(url)
        pprint.pprint(info.headers)
        print("Non è nei limiti")
    return False


async def get_tiktok_username_id(url):
    """
    Get the username and the video id from a tiktok url
    """

    purl = parse.urlparse(url)

    if purl.netloc == "vm.tiktok.com":
        tiktok_id = purl.path.split("/")[1]
        link = f"https://vm.tiktok.com/{tiktok_id}"
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'}
        response = requests.get(link, headers=headers)
        info_list = requests.utils.unquote(response.url).split("?")[0].split("/")
        username = info_list[3]
        tt_id = info_list[5]
    elif purl.netloc == 'www.tiktok.com':
        username = purl.path.split("/")[1]
        tt_id = purl.path.split("/")[3]
        link = url
    else:
        raise RuntimeError
    return (username, tt_id, link)

async def get_tiktok_video_infos_aweme(username: str, video_ID: str, debug: bool=False) -> dict:
    """
    Get Infos from the tiktok api and return a dict of relevant informations
    """

    infos = {}
    tiktok_api_headers = {
            'User-Agent': 'com.ss.android.ugc.trill/494+Mozilla/5.0+(Linux;+Android+12;+2112123G+Build/SKQ1.211006.001;+wv)+AppleWebKit/537.36+(KHTML,+like+Gecko)+Version/4.0+Chrome/107.0.5304.105+Mobile+Safari/537.36'
        }

    api_url = f'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={video_ID}'

    async with httpx.AsyncClient() as session:
        r = await session.get(api_url, headers=tiktok_api_headers, timeout=10)
    response = r.json()

    if debug:
        with open("debug.json", "w") as outfile:
            outfile.write(json.dumps(response, indent=4))
    data = response["aweme_list"][0]

    video_url = data["video"]["play_addr"]["url_list"][0]
    caption = f"<a href='https://www.tiktok.com/{username}/video/{video_ID}'>{username}</a>\n"
    caption += ' '.join([x for x in data["desc"].split() if not x.startswith('#')])
    thumbnail_jpg = data["video"]["cover"]["url_list"][0]
    title = f"Tiktok Video from {username}"
    height = data["video"]["height"]
    width = data["video"]["width"]
    slideshow = []
    if data.get('image_post_info'):
        for image in data['image_post_info']['images'][:10]:
            slideshow.append(image['display_image']['url_list'][-1])

    infos["username"] = username
    infos["video_id"] = video_ID
    infos["video_url"] = video_url
    infos["title"] = title
    infos["caption"] = caption
    infos["thumbnail_url"] = thumbnail_jpg
    infos["height"] = height
    infos["width"] = width
    infos["slideshow"] = slideshow
    return infos

async def tiktok_inline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query

    if query == "":
        return
    if not query.startswith("https://"):
        return

    if 'tiktok' not in query.split('.'):
        return


    username, tt_id, link = await get_tiktok_username_id(query)

    cprint(f'{get_now()} {await get_display_name(update.effective_user)} inline chiede un tiktok: {link}')

    try:
        video_info = await get_tiktok_video_infos_aweme(username, tt_id)
        if not video_info:
            results = [
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="Video not found! ",
                    input_message_content=InputTextMessageContent(link),
                    description="Can't find the video, sorry",
                    thumbnail_url="https://i.imgur.com/P9IhjS6.jpg",
                    thumbnail_height=80,
                    thumbnail_width=80
                    )]
            await update.inline_query.answer(results)
            return

        if not video_info["height"] and not video_info["width"]:
            results = [
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="Video is slideshow! Sorry!",
                    input_message_content=InputTextMessageContent(link),
                    description="Telegram doesn't support slideshows with music",
                    thumbnail_url="https://i.imgur.com/P9IhjS6.jpg",
                    thumbnail_height=80,
                    thumbnail_width=80
                    )]
            await update.inline_query.answer(results)
            return
        info = requests.head(video_info["video_url"])
        if int(info.headers["Content-Length"]) >= 20000000:
            message_content = InputTextMessageContent(f"Video is too big! Here's the link: <a href=\"{video_info['video_url']}\">[link]</a>")
            results = [
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="Video too big! ",
                    input_message_content=message_content,
                    description="The video exceeds 20MB",
                    thumbnail_url="https://i.imgur.com/P9IhjS6.jpg",
                    thumbnail_height=80,
                    thumbnail_width=80
                    )]
            await update.inline_query.answer(results)
            return
        else:
            caption = video_info['caption']
            caption = ' '.join([x for x in caption.split() if not x.startswith('#')])
            results = [
                    InlineQueryResultVideo(
                        id=str(uuid4()),
                        video_url=video_info['video_url'],
                        mime_type="video/mp4",
                        thumbnail_url=video_info['thumbnail_url'],
                        # thumbnail_url="https://imgur.com/BIWJZPG.jpg",
                        title=video_info['title'],
                        caption=caption,
                        parse_mode="HTML"
                    )]
            await update.inline_query.answer(results)
            return
    except Exception as e:
        print(e)
        return

async def tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    link = f"https://vm.tiktok.com/{context.match.group(1)}"

    username, tiktok_id, link = await get_tiktok_username_id(link)

    await printlog(update, "chiede un tiktok", link)

    video_info = await get_tiktok_video_infos_aweme(username, tiktok_id)

    if not video_info:
        await update.message.reply_text("Non riesco, forse tiktok è rotto, o forse sono programmata male.")
        return

    if video_info["slideshow"]:
        await update.effective_chat.send_chat_action(action='upload_photo')
        await update.message.reply_media_group(media=[InputMediaPhoto(image) for image in video_info['slideshow']])
        return

    info = requests.head(video_info["video_url"])

    if int(info.headers["Content-Length"]) >= 50000000:
        deleteme = await update.message.reply_html(f"Il video è più di 50MB\nNon posso caricarlo, ecco il <a href=\'{video_info['video_url']}\'>link</a>")
        return
    elif int(info.headers["Content-Length"]) >= 20000000:
        deleteme = await update.message.reply_text("Il video è più di 20MB\nTocca caricarlo a mano, un attimo.")
        try:
            with urllib.request.urlopen(video_info["video_url"]) as response:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    shutil.copyfileobj(response, tmp_file)
            await update.message.reply_video(video=open(tmp_file.name, "rb"), caption=video_info["caption"], height=video_info["height"], width=video_info["width"], parse_mode='HTML')
            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=deleteme.message_id)
        except Exception as e:
            await update.message.reply_text(f"Errore: {e}")
    else:
        try:
            await update.message.reply_video(video=video_info["video_url"], caption=video_info["caption"], height=video_info["height"], width=video_info["width"], parse_mode='HTML')
        except BadRequest as e:
            await update.message.reply_html(f"{e}\nA telegram questo video non piace, ecco il <a href=\"{video_info['video_url']}\">[link]</a>.")

async def tiktok_long(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    url = f"https://www.tiktok.com/{context.match.group(1)}/video/{context.match.group(2)}"

    username, tt_id, link = await get_tiktok_username_id(url)

    await printlog(update, "chiede un tiktok", link)

    video_info = await get_tiktok_video_infos_aweme(username, tt_id)

    if not video_info:
        await update.message.reply_text("Non riesco, forse tiktok è rotto, o forse sono programmata male.")
        return

    info = requests.head(video_info["video_url"])

    if int(info.headers["Content-Length"]) >= 50000000:
        deleteme = await update.message.reply_html(f"Il video è più di 50MB\nNon posso caricarlo, ecco il <a href=\'{video_info['video_url']}\'>link</a>")
        return
    elif int(info.headers["Content-Length"]) >= 20000000:
        deleteme = await update.message.reply_text("Il video è più di 20MB\nTocca caricarlo a mano, un attimo.")
        try:
            with urllib.request.urlopen(video_info["video_url"]) as response:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    shutil.copyfileobj(response, tmp_file)
            await update.message.reply_video(video=open(tmp_file.name, "rb"), caption=video_info["caption"], height=video_info["height"], width=video_info["width"], parse_mode='HTML')
            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=deleteme.message_id)
        except Exception as e:
            await update.message.reply_text(f"Errore: {e}")
    else:
        await update.message.reply_video(video=video_info["video_url"], caption=video_info["caption"], parse_mode='HTML')


async def new_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # (\b\S+(:?instagram\.com|instagr\.am)\S+\b)
    if await no_can_do(update, context):
        return

    url = context.match.group(1)
    url_path = parse.urlsplit(url).path[1:].split('/')
    user_agent = "Mozilla/5.0 (X11; Linux aarch64; rv:91.0) Gecko/20100101 Firefox/91.0"

    L = instaloader.Instaloader(dirname_pattern="ig/{target}", quiet=True, fatal_status_codes=[429], save_metadata=False, max_connection_attempts=1, user_agent=user_agent, iphone_support=False)
    USER = "emilia_superbot"
    L.load_session_from_file(USER, "db/session-emilia_superbot")

    await update.effective_chat.send_chat_action(action='typing')

    match url_path[0]:
        case 'reel' | 'p' | 'tv':
            shortcode = url_path[1]

            await printlog(update, f"chiede un contenuto ({url_path[0]}) da instagram", f"https://www.instagram.com/{url_path[0]}/{shortcode}/")

            try:
                post = instaloader.Post.from_shortcode(L.context, shortcode)
            except Exception as e:
                await update.message.reply_html(f"Qualcosa è andato storto:\n{e}")
                print(traceback.format_exc())
                return

            await update.effective_chat.send_chat_action(action='upload_photo')

            if post.typename == "GraphSidecar":
                medialist = []
                username = post.owner_username
                caption = f"https://www.instagram.com/{username}\n{post.caption[:200] if post.caption else ''}"
                caption = caption.replace("<", "&lt;").replace(">", "&gt;")
                for p in post.get_sidecar_nodes():
                    if p.is_video:
                        if await file_in_limits(p.video_url):
                            mi = pymediainfo.MediaInfo.parse(p.video_url, parse_speed=0)
                            if not mi.audio_tracks:
                                pass
                            else:
                                medialist.append(InputMediaVideo(media=p.video_url))
                        else:
                            continue

                    else:
                        if await file_in_limits(p.display_url):
                            medialist.append(InputMediaPhoto(media=p.display_url))
                        else:
                            continue

                await context.bot.send_media_group(reply_to_message_id=update.message.message_id, chat_id=update.message.chat.id, media=medialist)

            elif post.typename == "GraphImage":
                url = post.url
                username = post.owner_username
                caption = f"https://www.instagram.com/{username}\n{post.caption[:200] if post.caption else ''}"
                caption = caption.replace("<", "&lt;").replace(">", "&gt;")
                if await file_in_limits(url):
                    await update.message.reply_photo(photo=url, caption=caption, parse_mode='HTML')
                else:
                    await update.message.reply_html(f"Il file è troppo grosso per caricarlo, quindi ecco <a href='{url}'>il link</a>.", disable_web_page_preview=True)

            elif post.typename == "GraphVideo":
                url = post.video_url
                username = post.owner_username

                if await file_in_limits(url):
                    caption = f"https://www.instagram.com/{username}\n{post.caption[:200] if post.caption else ''}"
                    caption = caption.replace("<", "&lt;").replace(">", "&gt;")
                    await update.message.reply_video(video=url, caption=caption, parse_mode='HTML')
                else:
                    await update.message.reply_html(f"Il file è troppo grosso per caricarlo, quindi ecco <a href='{url}'>il link</a>.", disable_web_page_preview=True)

        case 'stories':
            username = url_path[1]
            target_story_id = url_path[2]
            await printlog(update, "chiede una storia da instagram", f"https://www.instagram.com/stories/{username}/{target_story_id}/")

            try:
                item = StoryItem.from_mediaid(L.context, int(target_story_id))
            except BadResponseException:
                await update.message.reply_text("Profilo privato o storia non esistente, o vedi tu.")
                return

            if item.is_video:
                if not item.video_url:
                    await update.message.reply_html("Instagram è stronzo e non mi fa scaricare la storia, scusa.", disable_web_page_preview=True)
                    return
                if await file_in_limits(item.video_url):
                    mi = pymediainfo.MediaInfo.parse(item.video_url, parse_speed=0)
                    if not mi.audio_tracks:
                        await update.effective_chat.send_chat_action(action='upload_photo')
                        await update.message.reply_animation(animation=item.video_url)
                    else:
                        await update.effective_chat.send_chat_action(action='upload_video')
                        await update.message.reply_video(video=item.video_url)
                else:
                    await update.message.reply_html(f"Il file è troppo grosso per essere caricato, quindi ecco <a href='{item.video_url}'>il link</a>.", disable_web_page_preview=True)
                    return

            else:
                if await file_in_limits(item.url):
                    await update.effective_chat.send_chat_action(action='upload_photo')
                    await update.message.reply_photo(photo=item.url)
                else:
                    await update.message.reply_html(f"Il file è troppo grosso per essere caricato, quindi ecco <a href='{item.url}'>il link</a>.", disable_web_page_preview=True)
                    return

        case _:
            username = url_path[0]

            await printlog(update, "chiede un profilo da instagram", f"https://www.instagram.com/{username}")

            try:
                profile = Profile.from_username(L.context, username)
            except Exception as e:
                await update.message.reply_html(f"Qualcosa è andato storto:\n{e}")
                print(traceback.format_exc())
                return

            if profile.is_private:
                messaggio = "Il profilo è privato.\n"
                messaggio += f"https://www.instagram.com/{username}\n{profile.biography}"
                await update.message.reply_photo(photo=profile.profile_pic_url, caption=messaggio)
                return

            await update.effective_chat.send_chat_action(action='upload_photo')

            i = 0
            MAX_MEDIA = 9
            medialist = []

            listapost = profile.get_posts()

            for post in listapost:

                if i >= MAX_MEDIA:

                    if not medialist:
                        await update.message.reply_text("Non trovo niente.")
                        return

                    caption = f"https://www.instagram.com/{username}\n{profile.biography}"
                    caption = caption.replace("<", "&lt;").replace(">", "&gt;")
                    await context.bot.send_media_group(reply_to_message_id=update.message.message_id, chat_id=update.message.chat.id, media=medialist)
                    return

                if post.typename == "GraphSidecar":
                    for p in post.get_sidecar_nodes():
                        if i >= MAX_MEDIA:
                            break

                        if p.is_video:
                            if await file_in_limits(p.video_url):
                                mi = pymediainfo.MediaInfo.parse(p.video_url, parse_speed=0)
                                if not mi.audio_tracks:
                                    pass
                                else:
                                    medialist.append(InputMediaVideo(media=p.video_url))
                                    i += 1
                            else:
                                continue

                        else:
                            if await file_in_limits(p.display_url):
                                medialist.append(InputMediaPhoto(media=p.display_url))
                                i += 1
                            else:
                                continue

                elif post.typename == "GraphImage":

                    url = post.url
                    username = post.owner_username
                    caption = f"https://www.instagram.com/{username}\n{post.caption[:200] if post.caption else ''}"
                    caption = caption.replace("<", "&lt;").replace(">", "&gt;")

                    if not await file_in_limits(post.url):
                            continue
                    medialist.append(InputMediaPhoto(media=post.url, caption=caption, parse_mode='HTML'))
                    i += 1

                elif post.typename == "GraphVideo":


                    url = post.video_url
                    username = post.owner_username

                    if await file_in_limits(url):
                        mi = pymediainfo.MediaInfo.parse(url, parse_speed=0)
                        if not mi.audio_tracks:
                            pass
                        else:
                            caption = f"https://www.instagram.com/{username}\n{post.caption[:200] if post.caption else ''}"
                            caption = caption.replace("<", "&lt;").replace(">", "&gt;")
                            medialist.append(InputMediaVideo(media=url, caption=caption, parse_mode='HTML'))
                            i += 1
                    else:
                        continue

                else:
                    print("Boh")
                    return

            if not medialist:
                await update.message.reply_text("Non trovo niente.")
                return

            await context.bot.send_media_group(reply_to_message_id=update.message.message_id, chat_id=update.message.chat.id, media=medialist)
            return

async def instagram_stories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    L = instaloader.Instaloader(dirname_pattern="ig/{target}", quiet=True, fatal_status_codes=[429], save_metadata=False, max_connection_attempts=1)
    USER = "emilia_superbot"
    L.load_session_from_file(USER, "db/session-emilia_superbot")

    if not context.args or (len(context.args) != 1):
        await update.message.reply_html("Uso: <code>/stories @profile</code>")
        return
    username = context.args[0].replace("@", "")

    messaggio = await update.message.reply_text(f"Scarico le storie di: @{username}")
    await printlog(update, "scarica le storie instagram di", f"@{username}")
    try:
        profile = Profile.from_username(L.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        await update.message.reply_text("Il profilo non esiste.")
        return
    except instaloader.exceptions.QueryReturnedBadRequestException as e:
        await update.message.reply_text("Probabilmente sono bannata da instagram")
        await alert(update, context, f"ha cercato le storie di @{username}", f"{e}")
        return
    except Exception as e:
        await update.message.reply_html(f"Qualcosa è andato storto:\n{e}")
        await alert(update, context, f"ha cercato le storie di @{username}", f"{e}")
        print(traceback.format_exc())
        return

    if not profile.has_viewable_story:
        await update.message.reply_text(f"@{username} non ha nessuna storia visibile.")
        return

    medialist = []
    stories_list = []
    MAX_MEDIA = 10
    i = 0

    for story in L.get_stories([profile.userid]):
        for item in story.get_items():
            stories_list.append(item)
    for item in reversed(stories_list):
        # print(i)
        if i >= MAX_MEDIA:
            # print("STOP!")
            break


        if item.is_video:
            url = item.video_url
            if await file_in_limits(url, debug=False):
                username = item.owner_username
                if not item._asdict().get('has_audio', None):
                    await update.message.reply_video(video=url, caption=f"@{username}")
                    i += 1
                else:
                    medialist.append(InputMediaVideo(media=url, caption=f"@{username}"))
                    i += 1

        else:
            url = item.url
            if await file_in_limits(url, debug=False):
                    username = item.owner_username
                    medialist.append(InputMediaPhoto(media=url, caption=f"@{username}"))
                    i += 1

    if not i:
        await update.message.reply_text(f"@{username} non ha nessuna storia visibile.")
        return



    await context.bot.send_media_group(update.effective_chat.id, media=medialist)
    await messaggio.delete()


async def ninofrassica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    if await no_can_do(update, context):
        return

    L = instaloader.Instaloader(dirname_pattern="ig/{target}", quiet=True, fatal_status_codes=[429], save_metadata=False, max_connection_attempts=1)
    USER = "emilia_superbot"
    L.load_session_from_file(USER, "db/session-emilia_superbot")
    username = "ninofrassicaoff"

    profile = Profile.from_username(L.context, username)
    listapost = profile.get_posts()

    # TODAY = datetime.date.today()
    # print(TODAY)
    n = 0
    LIMIT = 30
    try:
        user_date = context.args[0].split("/")
        search_date = datetime.datetime(int(user_date[2]), int(user_date[1]), int(user_date[0])).date()
    except IndexError:
        search_date = datetime.date.today()

    if datetime.date.today() - search_date > datetime.timedelta(days=30):
        await update.message.reply_html("Puoi cercare fino a 30 gg fa.")
        return

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede i post nino frassica del {search_date}, che mito')
    await printlog(update, "chiede un post di nino frassica del", search_date)
    mymessage = ""
    for post in listapost:
        # print("Trovato post: ", end="")
        medialist = []
        if post.date.date() > search_date:
            if n == LIMIT:
                print(f"Limite massimo di post raggiunto ({LIMIT})")
                if not mymessage:
                    await update.message.reply_html("Non trovo niente.")
                return
            # print("non è di oggi")

            n += 1
            continue
        elif post.date.date() < search_date:
            print("Data superata. Nessun post trovato.")
            # update.message.reply_html("Non trovo niente per quella data.")
            return
        else:
            if n == LIMIT:
                print(f"Limite massimo di post raggiunto ({LIMIT})")
                if not mymessage:
                    await update.message.reply_html("Non trovo niente.")
                return
            n += 1
            # print("è di oggi")

            caption = f"https://www.instagram.com/{username}\n{post.caption if post.caption else ''}"
            # mymessage = update.message.reply_html(caption, quote="False")
            if post.typename == "GraphSidecar":
                # print(f"Trovato Album")
                i = 0
                for p in post.get_sidecar_nodes():
                    if p.is_video:
                        medialist.append(InputMediaVideo(media=p.video_url, caption=caption if i == 0 else '', parse_mode="HTML"))
                        # print(f"--Video")
                        i += 1

                    else:
                        medialist.append(InputMediaPhoto(media=p.display_url, caption=caption if i == 0 else '', parse_mode="HTML"))
                        # print(f"--Foto")
                        i += 1

            elif post.typename == "GraphImage":
                url = post.url
                username = post.owner_username
                medialist.append(InputMediaPhoto(media=post.url, caption=caption, parse_mode='HTML'))
                print(" Foto")
            elif post.typename == "GraphVideo":
                url = post.video_url
                username = post.owner_username
                print(" Video")
                medialist.append(InputMediaVideo(media=url, caption=caption, parse_mode='HTML'))
            else:
                print("Boh")

           
            await context.bot.send_media_group(reply_to_message_id=update.message.message_id, chat_id=update.message.chat.id, media=medialist)

    await update.message.reply_html("Non trovo niente.")
    return

async def wikipedia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return



    wkp.set_lang("it")
    try:
        searchquery = update.effective_message.text.split(maxsplit=1)[1]
    except IndexError:
        await update.message.reply_text("Non hai specificato cosa cercare")
        return


    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} cerca su wikipedia: {searchquery}')
    await printlog(update, "cerca su wikipedia", searchquery)
    try:
        page = wikipedia.search(searchquery)[0]
        summary = f"<a href='http://it.wikipedia.org/wiki/{page}'><b>{page}</b></a>\n"
        summary += f"{wikipedia.summary(page, sentences=1)}"

        await update.message.reply_html(summary, disable_web_page_preview=True)
        return
    except IndexError:
        await update.message.reply_html("Non trovo un cazzo amicə.")
    except wikipedia.exceptions.DisambiguationError as e:
        # print(e.__dict__)
        alternativa = "\n".join([i for i in e.options])
        await update.message.reply_html(f"Amicə sei statə troppo vagə. Sii più precisə. Prova uno di questi:\n{alternativa}")

async def youtube_alts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} posta un link a youtube: {context.match.group(2)}')
    await printlog(update, "posta un link a youtube", context.match.group(2))
    await update.message.reply_html(f"<a href='https://www.youtube.com/watch?v={context.match.group(2)}'>[YouTube]</a>", quote=False, disable_web_page_preview=True)

async def facebook_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    link = context.match.group(0)

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'mp4'
    }

    await printlog(update, "posta un video di facebook", link)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url=link, download=False)
    caption = f"{info['title']}\n{info['description']}"
    formats = []

    for f in info['formats']:
        if f['ext'] == 'mp4':
            formats.append(f)


    file_url = formats[-1]['url']

    if not await file_in_limits(file_url):
        file_url = formats[-2]['url']

    if await file_in_limits(file_url):
        # print(f"sto per inviare questo:\n{file_url}")
        await update.message.reply_video(video=file_url, caption=caption[:1000], parse_mode='HTML')

    else:
        await update.message.reply_html(f"Il file è troppo grosso per caricarlo, quindi ecco <a href='{file_url}'>il link</a>.", disable_web_page_preview=True)

async def scrape_tweet_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if (update.message.sender_chat.id == config.ID_BT_CHAN): # or (update.message.chat.id == config.ID_TESTING):
            return
        else:
            pass
    except AttributeError:
        if await no_can_do(update, context):
            return

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} posta un tweet: {context.match.group(1)}')
    await printlog(update, "posta un tweet", context.match.group(1))

    CONSUMER_KEY = config.TW_API
    CONSUMER_SECRET = config.TW_API_SECRET
    ACCESS_KEY = config.TW_ACCESS_TOKEN
    ACCESS_SECRET = config.TW_ACCESS_TOKEN_SECRET

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)
    tw_id = [context.match.group(1)]


    my_tweet = api.lookup_statuses(tw_id, tweet_mode='extended')
    try:
        t = my_tweet[0]
    except IndexError:
        await update.message.reply_html("Tweet non trovato.")
        return

    # print(my_tweet[0]._json)

    try:
        text = t.full_text
        text = text.split('\n\nhttps://t.co/')[0]
        text += "\n"
    except AttributeError:
        text = ""

    name = t.user.screen_name
    url = f"https://twitter.com/{name}/status/{t.id}"

    try:
        text_url = t.entities.urls[0]['expanded_url']
        text_url += "\n"
    except (AttributeError, IndexError):
        text_url = ""
    nitter_instances = [
        "nitter.net",
        "nitter.it",
        "nitter.nl",
        "nitter.cz"
    ]
    nitter_url = url.replace("twitter.com",random.choice(nitter_instances))
    caption = f"<a href='{url}'>@{name}</a>\n{text if text else ''}{text_url if text_url else ''}\n<a href='{nitter_url}'>[Nitter]</a>"
    try:
        medialist = t.extended_entities.get('media', [])
    except AttributeError:
        medialist = []

    medias = []
    if medialist:
        i = 0
        media_no = []
        for media in medialist:
            if media.get('type') == 'photo':
                media_url = media.get('media_url')
                # print(media_url)
                # print(await file_in_limits(media_url))
                if await file_in_limits(media_url):
                    medias.append(InputMediaPhoto(media=media_url, caption=caption if i == 0 else '', parse_mode='HTML'))
                    i += 1
                else:
                    media_no.append(media_url)
            elif media.get('type') == 'video':
                n = 0
                if not media.get('video_info').get('variants')[n].get('bitrate'): # a volte twitter come qualità più alta mette una playlist m3u8, in quel caso skippiamo
                    n += 1
                media_url = media.get('video_info').get('variants')[n].get('url')

                # print(media_url)
                # print(await file_in_limits(media_url))

                # qua c'è una pezza: a volte i link hanno tipo ?tag=12 dopo .mp4 e questoa a telegram non piace: glielo togliamo e speriamo che non si rompa niente.
                media_url = media_url.split('.mp4')[0]
                media_url = f"{media_url}.mp4"

                if await file_in_limits(media_url):
                    medias.append(InputMediaVideo(media=media_url, caption=caption if i == 0 else '', parse_mode='HTML'))
                    i += 1
                else:
                    media_no.append(media_url)

        if medias:
            # print(medias)
            await context.bot.send_media_group(reply_to_message_id=update.message.message_id, chat_id=update.message.chat.id, media=medias)
        else:
           
            # print("C'erano dei media ma erano tutti oltre il limite:")
            # print(media_no)
            message = "C'erano dei media ma erano tutti oltre il limite per caricarli automaticamente:\n"
            for media in enumerate(media_no, start=1):
                message += f"<a href='{media[1]}'>[{media[0]}]</a> "
            await update.message.reply_html(message)
            # print(medialist)
    else:
        await update.message.reply_html(caption, disable_web_page_preview=True)

async def parse_reddit_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
   
    if update.effective_user.id == 160339370:
        await update.message.reply_html("Basta Zanna.")
        return

    start_time = time.perf_counter()

    reddit = asyncpraw.Reddit(
        client_id=config.REDDIT_ID,
        client_secret=config.REDDIT_SECRET,
        user_agent="Emily Bot"
        )


    url = context.match.group(0)
    submission = await reddit.submission(url=url, fetch=True)


    if hasattr(submission, "crosspost_parent"):  # controllo se è un crosspost
        submission = await reddit.submission(id=submission.crosspost_parent.split("_")[1])

    permalink = f"https://reddit.com{submission.permalink}"
    title = submission.title
    sub = f"r/{submission.subreddit}"
    upvotes = submission.score
    url = submission.url
    gallery = []

    await printlog(update, "posta un link a reddit", permalink)
    # print(url)

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
                    # import pprint
                    # pprint.pprint(submission)
                    url = submission.media['reddit_video']['fallback_url']
                    url = url.replace("?source=fallback", "")
                    url_audio = url.replace("1080", "audio")
                    url_audio = url_audio.replace("720", "audio")
                    url_audio = url_audio.replace("360", "audio")
                    url_audio = url_audio.replace("240", "audio")
                    url_audio = url_audio.replace("audio", "AUDIO_128")
                    width = submission.media['reddit_video']['width']
                    height = submission.media['reddit_video']['height']

                    # pprint.pprint(submission.media)
                    # print(f"url: {url}")
                    # print(f"url_audio: {url_audio}")
                    # pprint.pprint(vars(submission))
                    try:
                        link_thumb = submission.preview['images'][0]['source']['url']
                    except AttributeError:
                        link_thumb = "https://i.imgur.com/znuE4Fn.jpg"

                    caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}\n\nIl video arriva in un attimo"
                    messaggio = await update.message.reply_photo(photo=link_thumb, caption=caption, parse_mode='HTML')
                    download = True

                    try:
                        if '-nodownload' in update.message.text.split(' '):
                            download = False
                    except IndexError:
                        download = True

                    if download:


                        video_file = "reddit/video.mp4"
                        audio_file = "reddit/audio.mp4"

                        try:
                            link_audio = urllib.request.urlopen(url_audio)  # Proviamo a guardare se c'è il file audio
                        except urllib.error.HTTPError:  # Se non c'è passiamo direttamente il video come url, inutile scaricare e muxare
                            caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}\n\nNo audio (and reddit is dumb)."
                            await context.bot.edit_message_media(chat_id=update.message.chat.id, message_id=messaggio.message_id, media=InputMediaVideo(media=url, caption=caption, parse_mode='HTML'))
                            await reddit.close()
                            return

                        print(f"{get_now()} Unisco audio e video con FFmpeg per l'upload da locale")
                        link_video = urllib.request.urlopen(url)

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
                        # caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}\n\nFinito in: {str(time_elapsed)[:4]}s\nScusate il ritardo, colpa di reddit.\n"
                        caption = f"<a href='{permalink}'>{sub}</a> | {upvotes} upvotes\n{title}\n<i>Finito in: {str(time_elapsed)[:4]}s</i>"
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

async def twitch_clips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    client_id = config.TWITCH_CLIENT_ID
    client_secret = config.TWITCH_CLIENT_SECRET

    clip_id = context.match.group(1)

    bearer_token = httpx.post(f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials").json()['access_token']
    if bearer_token.lower().startswith('bearer'):
        bearer_token = bearer_token[6:0]

    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Client-Id': client_id
    }

    params = {
        'id': clip_id,
    }

    API_URL = 'https://api.twitch.tv/helix/clips'
    response = httpx.get(API_URL, params=params, headers=headers).json()

    if not response.get('data'):
        await update.message.reply_html("Non trovo niente")
        return
   
    await printlog(update, "posta una clip di twitch", context.match.group(0))

    thumbnail_url = response['data'][0]['thumbnail_url']
    mp4_base_url = thumbnail_url.split("-preview",1)[0]
    mp4_url_1080 = f"{mp4_base_url}.mp4"
    mp4_url_720 = f"{mp4_base_url}-720.mp4"
    mp4_url_480 = f"{mp4_base_url}-480.mp4"
    mp4_url_360 = f"{mp4_base_url}-360.mp4"
    try:
        await update.message.reply_video(mp4_url_1080)
    except BadRequest:
        try:
            await update.message.reply_video(mp4_url_720)
        except BadRequest:
            try:
                await update.message.reply_video(mp4_url_480)
            except BadRequest:
                try:
                    await update.message.reply_video(mp4_url_360)
                except BadRequest:
                    await update.message.reply_html(f"Boh, non riesco a mandarlo, ecco il link: [<a href='{mp4_url_1080}'>LINK</a>]")

