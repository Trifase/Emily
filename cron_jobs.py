import datetime
import html
import os
import shutil
import time
import zipfile

import httpx
import humanize
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from mastodon import Mastodon
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import config
from database import Chatlog, Compleanni, Reminders
from pyrog import get_all_chatmembers
from space import StelleResult, make_solar_system
from utils import get_now


# Runs every day at 01:00 (Europe/Rome)
async def delete_yesterday_chatlog(context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"{get_now()} [AUTO] Cancello i messaggi di ieri dal db")
    oggi_dt = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    oggi_timestamp = int(datetime.datetime.timestamp(oggi_dt))
    Chatlog.delete().where(Chatlog.timestamp < oggi_timestamp).execute()

# Runs every day at 8:30 (Europe/Rome)
async def post_solarsystem_mastodon(context: ContextTypes.DEFAULT_TYPE) -> None:

    print(f"{get_now()} [AUTO] Posto il sistema solare giornaliero su mastodon")


    result: StelleResult = await make_solar_system()

    if result is None:
        print(f"{get_now()} [AUTO] Errore durante la generazione del sistema solare")
        return

    image_path = result.file.name
    system_name = result.system_name
    system_distance = result.system_distance
    planet_list = result.planet_list
    seed = result.seed
    fp = result.file

    #   Set up Mastodon
    mastodon = Mastodon(
        access_token = 'db/mastodon.token',
        api_base_url = 'https://botsin.space/'
    )

    message = f"🌌 Sistema solare del giorno: {system_name}\nDistanza: {system_distance}\nSeed: {seed}\nOrbite:\n{planet_list}"

    mast_media = mastodon.media_post(image_path)
    mast_response = mastodon.status_post(message, media_ids=mast_media)
    mastodon_url = mast_response.get('url')
    print(f"{get_now()} [AUTO] Fatto! {mastodon_url}")

    fp.close()
    return

# Runs every 30min
async def parse_diochan(context: ContextTypes.DEFAULT_TYPE) -> None:
    DESTINATION_CHATS = [-1001619525581]

    MINUTES = 30
    SINGLE_POST = False
    IMAGES = False
    BOARDS = ['b', 's', 'x', 'hd', 'aco', 'v', 'cul', 'yt', 'pol']

    async def get_last_threads_from_board(board):
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f'https://www.diochan.com/{board}/catalog.json')
            response.raise_for_status()
            return response.json()

    diochan = {}
    for board in BOARDS:
        diochan[board] = await get_last_threads_from_board(board)
    now = int(time.time())

    delta_timestamp = 60 * MINUTES
    not_before = now - delta_timestamp
    threads = []

    for board in BOARDS:
        for page in diochan[board]:
            for thread in page['threads']:
                if thread['time'] > not_before:
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
                    threads.append(t)


    bot = context.bot

    if not threads:
        return

    lista_threads = []
    for thread in threads:
        lista_threads.append(f"/{thread['board']}/{thread['thread']}")

    print(f"{get_now()} [AUTO] Trovati {len(threads)} nuovi thread su Diochan", " | ".join(lista_threads))

    if SINGLE_POST:
        message = ''
        for thread in threads:
            timestamp = datetime.datetime.fromtimestamp(thread['time']).strftime('%d/%m/%Y %H:%M')
            text = thread['text'].replace('<br/>','\n').replace('<span class="quote">&gt;','>').replace('<span class="spoiler">', '').replace('</span>','')
            if len(text) > 2000:
                text = text[:2000] + "..."
            link = f"<a href='{thread['thread_url']}'>/{thread['board']}/ | No.{thread['thread']}</a> | {timestamp}"
            if thread['is_video']:
                link += f"\n<a href='{thread['video_url']}'>[YouTube]</a>"
            text = html.unescape(text)
            text = text.replace('<br/>','\n').replace('<span class="quote">', '').replace('<span class="spoiler">', '').replace('</span>', '')
            message += f"{link}\n{text}\n\n"
        for chat_id in DESTINATION_CHATS:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

    else:
        for thread in threads:
            timestamp = datetime.datetime.fromtimestamp(thread['time']).strftime('%d/%m/%Y %H:%M')
            text = thread['text'].replace('<br/>','\n').replace('<span class="quote">&gt;','>').replace('<span class="spoiler">', '').replace('</span>','')
            if len(text) > 2000:
                text = text[:2000] + "..."
            link = f"<a href='{thread['thread_url']}'>/{thread['board']}/ | No.{thread['thread']}</a> | {timestamp}"

            if thread['is_video']:
                link += f"\n<a href='{thread['video_url']}'>[YouTube]</a>"

            text = html.unescape(text)
            text = text.replace('<br/>','\n').replace('<span class="quote">', '').replace('<span class="spoiler">', '').replace('</span>', '')
            message = f"{link}\n{text}"
            image_url = thread['image_url']

            for chat_id in DESTINATION_CHATS:
                if IMAGES:
                    try:
                        await bot.send_photo(chat_id=chat_id, photo=image_url, caption=message, parse_mode='HTML')

                    # We catch everything, because we don't want to stop the bot if something goes wrong. We send a basic text message.
                    except Exception as e:
                        print(e)
                        await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
                else:
                    await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

# Runs every 30min
async def parse_niuchan(context: ContextTypes.DEFAULT_TYPE) -> None:
    DESTINATION_CHATS = [-1001619525581]
    MINUTES = 30

    async def get_last_threads_from_niuchan():
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get('https://niuchan.org/overboard.json')
            response.raise_for_status()
            return response.json()

    niuchan = await get_last_threads_from_niuchan()
    now = int(time.time())

    delta_timestamp = 60 * MINUTES
    not_before = now - delta_timestamp

    for t in niuchan['threads']:

        if not t.get('nomarkup'):
            continue

        if (int(t['u'])//1000) <= not_before:
            continue

        post_time_string = datetime.datetime.fromtimestamp(int(t['u'])//1000).strftime('%d/%m/%Y %H:%M')
        head = f"[🐍 niuchan] <a href='https://niuchan.org/{t['board']}/thread/{t['postId']}.html'>/{t['board']}/ | No.{t['postId']}</a>| {post_time_string}"
        text = t['nomarkup'].replace('<br/>','\n').replace('<span class="quote">&gt;','>').replace('<span class="spoiler">', '').replace('</span>','')

        if len(text) > 2000:
            text = text[:2000] + "..."
        message = f"{head}\n{text}"

        for chat in DESTINATION_CHATS:
            await context.bot.send_message(chat, message, parse_mode='HTML')


# Never runs
async def autolurkers(context: ContextTypes.DEFAULT_TYPE) -> None:

    _localize = humanize.i18n.activate("it_IT")
    type(_localize)

    print(f"{get_now()} [AUTO] controllo i lurkers")
    groups_to_check = [config.ID_DIOCHAN2]

    for chat_id in groups_to_check:

        if "timestamps" not in context.bot_data:
            context.bot_data["timestamps"] = {}
        if chat_id not in context.bot_data["timestamps"]:
            context.bot_data["timestamps"][chat_id] = {}

        deltas = {}

        MAX_SECS = 1_209_600 # 2 weeks


        for user in context.bot_data["timestamps"][chat_id].keys():
            deltas[user] = int(time.time()) - context.bot_data["timestamps"][chat_id][user]

            listona = ["LURKERS_LIST"]
            messaggio_automatico = ""

            allmembers = await get_all_chatmembers(chat_id)
            for lurker in sorted(deltas.items(), key=lambda x: x[1], reverse=True):
                for u in allmembers:
                    if u.user.id == lurker[0]:
                        mylurker = u
                        break

                if lurker[1] > MAX_SECS:

                    if mylurker.status in ['left', 'kicked']:
                        context.bot_data["timestamps"][chat_id].pop(lurker[0])
                        continue
                    else:
                        messaggio_automatico += f'{mylurker.user.first_name} - {str(humanize.precisedelta(lurker[1], minimum_unit="days"))} fa\n'
                        listona.append(mylurker.user.id)


            keyboard = [
                [
                    InlineKeyboardButton("👎 Kick", callback_data=listona),
                    InlineKeyboardButton("👍 Passo", callback_data=["LURKERS_LIST", None])
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

        if messaggio_automatico:
            print(f"{get_now()} [AUTO] trovati lurkers da kickare nel gruppo {chat_id}")
            await context.bot.send_message(chat_id, messaggio_automatico, reply_markup=reply_markup)

# Runs every minute
async def check_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    datenow = str(datetime.datetime.today().strftime("%d/%m/%Y %H:%M"))
    for row in Reminders.select().where(Reminders.date_to_remind == datenow):
        if row:
            print(f'{get_now()} Trovato un reminder: "{row.message}" del {row.date_now}',)
            if not row.message:
                missiva = 'Bip Bop Bup! Mi avevi chiesto di blipparti!'
            else:
                missiva = f'Ciao, mi avevi chiesto di ricordarti questo: {row.message}'
            user = await context.bot.get_chat_member(chat_id=row.chat_id, user_id=row.user_id)
            await context.bot.send_message(row.chat_id, f"[{user.user.mention_html()}] {missiva}", reply_to_message_id=row.reply_id, allow_sending_without_reply=True)
            Reminders.delete().where(Reminders.reply_id == row.reply_id).execute()
            print(f'{get_now()} Reminder annunciato e cancellato.')

# Runs every day at 9:00 (Europe/Rome)
async def lotto_member_count(context: ContextTypes.DEFAULT_TYPE) -> None:
    newcount = await context.bot.get_chat_member_count(config.ID_LOTTO)
    oldcount = context.bot_data.get('lotto_count', 0)
    if newcount != oldcount:
        context.bot_data['lotto_count'] = newcount
        await context.bot.send_message(config.ID_LOTTO, f"Popolazione: {newcount} anime.")
        return
    else:
        return

# Runs every hour
async def plot_boiler_stats(context: ContextTypes.DEFAULT_TYPE) -> None:

    r_token = context.bot_data.get('netatmo_refresh_token', config.r_token)
    home_id = config.home_id
    room_id = config.room_id
    bridge_mac = config.bridge_mac
    therm_mac = config.therm_mac


    async def refresh_token(refresh_token):
        client_id = config.NETATMO_CLIENT_ID
        client_secret = config.NETATMO_CLIENT_SECRET

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret
        }

        async with httpx.AsyncClient() as session:
            r = await session.post("https://api.netatmo.com/oauth2/token", data=data)
        response = r.json()

        return response

    # async def get_home_data(access_token):
    #     headers = {
    #         'accept': 'application/json',
    #         'Authorization': f'Bearer {access_token}',
    #     }

    #     async with httpx.AsyncClient() as session:
    #         r = await session.get('https://api.netatmo.com/api/homesdata', headers=headers)
    #     response = r.json()

    #     return response

    async def get_home_status(access_token, home_id):
        headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        }

        params = {
            'home_id': home_id,
        }

        async with httpx.AsyncClient() as session:
            r = await session.get('https://api.netatmo.com/api/homestatus', params=params, headers=headers)
        response = r.json()

        return response

    async def get_room_history(access_token, home_id, room_id, date_end='last', graph_type='temperature', scale='1hour'):
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }

        params = {
            'home_id': home_id,
            'room_id': room_id,
            'scale': scale,
            'date_begin': int(datetime.datetime.now().timestamp())-(3600*50),
            'type': graph_type
        }

        async with httpx.AsyncClient() as session:
            r = await session.get('https://api.netatmo.com/api/getroommeasure', params=params, headers=headers)
        response = r.json()

        return response

    # this returns the number of seconds the boiler was on in the time scale
    async def get_boiler_history(access_token, bridge_mac, therm_mac, date_end='last', scale='1hour'):

        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }

        params = {
            'device_id': bridge_mac,
            'module_id': therm_mac,
            'scale': scale,
            'type': 'sum_boiler_on',
            'date_begin': int(datetime.datetime.now().timestamp())-(3600*50)
        }


        async with httpx.AsyncClient() as session:
            r = await session.get('https://api.netatmo.com/api/getmeasure', params=params, headers=headers)
        response = r.json()

        return response

    int(time.time() - 3600*48)

    tokens = await refresh_token(r_token)
    # print(tokens)
    access_token = tokens['access_token']
    context.bot_data['netatmo_refresh_token'] = tokens['refresh_token']

    home_status = await get_home_status(access_token, home_id)
    # print(home_status)

    current_temp = home_status['body']['home']['rooms'][0]['therm_measured_temperature']
    set_temp = home_status['body']['home']['rooms'][0]['therm_setpoint_temperature']
    is_boiler_active = home_status['body']['home']['modules'][-1]['boiler_status']


    temp_history = await get_room_history(access_token, home_id, room_id)
    set_temp_history = await get_room_history(access_token, home_id, room_id, graph_type='sp_temperature')
    boiler_history = await get_boiler_history(access_token, bridge_mac, therm_mac)


    temps = temp_history['body'][0]
    list_temps = [x[0] for x in temps['value']]
    # print(list_temps)

    set_temps = set_temp_history['body'][0]
    list_set_temps = [x[0] for x in set_temps['value']]
    # print(list_set_temps)

    boiler = boiler_history['body'][0]
    list_minutes = [x[0]//60 for x in boiler['value']]
    # list_minutes = [x[0]//60 for x in reversed(boiler['value'])]
    # print(list_minutes)

    initial_timestamp = temps.get('beg_time')
    step = temps.get('step_time')
    list_timestamps = [initial_timestamp+(step*n) for n in range(len(temps.get('value')))]

    # print(list_timestamps)
    list_timestamps = [datetime.datetime.fromtimestamp(x).strftime('%d-%m %H:00') for x in list_timestamps]


    N_HOURS = 48


    list_timestamps = list_timestamps[-N_HOURS:]
    list_minutes = list_minutes[-N_HOURS:]
    list_temps = list_temps[-N_HOURS:]
    list_set_temps = list_set_temps[-N_HOURS:]

    # print(list_timestamps)
    # print()
    # print(list_minutes)
    # print()
    # print(list_temps)
    # print()
    # print(list_set_temps)

    px = 1/plt.rcParams['figure.dpi']

    _, bars = plt.subplots(figsize=(1280*px, 500*px))

    bars.set_xlabel("Time of the day")
    bars.set_title(f"Temperature and boiler activity (last {N_HOURS}hrs)\nCurrent: {current_temp}°C - Desidered: {set_temp}°C · Boiler active: {is_boiler_active}")
    bars.yaxis.set_major_locator(ticker.LinearLocator(5))
    bars.yaxis.set_minor_locator(ticker.LinearLocator(13))
    bars.xaxis.set_major_locator(ticker.MultipleLocator(6))
    bars.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    bars.set_ylabel("Boiler activity, Minutes per hour", color='red')
    bars.set_ylim(0, 60)
    bars.grid(True)
    bars.bar(list_timestamps, list_minutes, color='red', zorder=1, label="Boiler activity")

    lines=bars.twinx()
    lines.set_ylim(13, 25)
    lines.set_ylabel("Temperature in °C",)
    lines.plot(list_timestamps, list_temps, zorder=10, label="Temperature")
    lines.plot(list_timestamps, list_set_temps, label="Desidered Temperature", zorder=2, color='grey', linestyle='dotted', linewidth=1)

    bars.legend(loc='upper left')
    lines.legend(loc='upper right')

    plt.savefig("images/boiler48h.jpg")

# Runs every day at 2:00 (Europe/Rome)
# Doesn't run anymore, see do_global_backup
async def do_backup(context: ContextTypes.DEFAULT_TYPE):

    for filename in ['picklepersistence', 'sqlite.db', 'sets.json']:
        print(f"{get_now()} [AUTO] Eseguo il backup del file {filename}")
        oldfile = f"db/{filename}"
        newfile = f"db/backups/{datetime.datetime.today().strftime('%Y%m%d_%H%M%S')}-{filename}"
        shutil.copy(oldfile, newfile)
    print(f"{get_now()} [AUTO] Backup eseguito")

# Runs every day at 2:00 (Europe/Rome)
async def do_global_backup(context: ContextTypes.DEFAULT_TYPE):


    now = datetime.datetime.today().strftime('%Y%m%d_%H%M%S')

    backup_dir = "backups"
    archive_name = f"{backup_dir}/emily-{now}-backup.zip"

    IGNORED_DIRS = [
        f"./{backup_dir}",
        "./db/backups",
        "./db/corpuses",
        "./__pycache__",
        "./ig",
        "./.git/",
        "./reddit",
        "./images",
        "./images/tarots",
        "./images/trifasi",
        "./templates",
        "./.vscode",
        "./banca",
        "./.mypy_cache",
        "./logs",
        ]
    IGNORED_FILES = [f"emily-{now}-backup.zip", "condominioweb.jsonl.zst", "logs.txt"]

    skipped = 0
    backupped = 0

    with zipfile.ZipFile(archive_name, 'w') as zip_ref:
        to_archive = []
        for folder_name, _, filenames in os.walk('.'):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                if file_path.startswith(tuple(IGNORED_DIRS)):
                    # print(f"Saltato {folder_name} {filename}")
                    skipped += 1
                elif filename in IGNORED_FILES:
                    # print(f"Saltato {folder_name} {filename}")
                    skipped += 1
                else:
                    # print(f"Archiviando {file_path}")
                    backupped += 1
                    to_archive.append(file_path)
        # for file in track(to_archive, description="Backup in corso"):
        for file in to_archive:
            zip_ref.write(file)
    zip_ref.close()
    try:
        await context.bot.send_document(chat_id=config.ID_BOTCENTRAL, document=open(archive_name, 'rb'))
        print(f"{get_now()} [AUTO] Backup globale eseguito: {archive_name} - File archiviati: {backupped} - File Skippati: {skipped} - File inviato su TG")
    except Exception as e:
        print(f"{get_now()} [AUTO] Backup globale eseguito: {archive_name} - File archiviati: {backupped} - File Skippati: {skipped} - File NON inviato su TG\n{e}")

# Runs every day at 0:00, 12:00 and 20:00 (Europe/Rome)
async def check_compleanni(context: ContextTypes.DEFAULT_TYPE):
    print(f"{get_now()} [AUTO] controllo i compleanni di oggi")

    today_d = datetime.datetime.now().strftime("%d")
    today_m = datetime.datetime.now().strftime("%m")
    today_y = datetime.datetime.now().strftime("%Y")

    for row in Compleanni.select():
        if row:
            d = row.birthdate[:2]
            m = row.birthdate[3:5]
            y = row.birthdate[6:10]
            if d == today_d and m == today_m:
                try:
                    member = await context.bot.get_chat_member(row.chat_id, row.user_id)
                    nickname = member.user.mention_html()
                except Exception as e:
                    Compleanni.delete().where((Compleanni.user_id == row.user_id) & (Compleanni.chat_id == row.chat_id)).execute()
                    print(f"{e}\nCompleanno cancellato (user: {row.user_id}, chat: {row.chat_id})")
                    return
                if y:
                    anni = int(today_y) - int(y)
                    if anni > 100:
                        await context.bot.send_message(row.chat_id, f"Auguri {nickname}! Oggi compi {anni} anni! Li porti benissimo! Sarai mica un vampiro?")
                    else:
                        await context.bot.send_message(row.chat_id, f"Auguri {nickname}! Oggi compi {anni} anni!")
                else:
                    await context.bot.send_message(row.chat_id, f"Auguri {nickname}! Buon compleanno!")