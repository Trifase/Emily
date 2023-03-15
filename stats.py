import datetime
import locale
import pytz
import json
from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import CallbackContext, ContextTypes
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
locale.setlocale(locale.LC_ALL, 'it_IT.utf8')
from utils import no_can_do, printlog
import os


def extract_day(timestamp):
    return timestamp.strftime("%Y-%m-%d")

def extract_hour(timestamp):
    return timestamp.strftime("%H")

def last_30_days():
    start = datetime.datetime.today()
    days_30 = []
    for day in range(1, 31): 
        d = start - datetime.timedelta(days=day)
        days_30.append(d.strftime("%Y-%m-%d"))
    days_30.reverse()
    return days_30

def list_24_hours():
    hours = []
    for hour in range(0, 24):
        hours.append(str(hour).zfill(2))
    return hours

def list_week_days():
    week_days = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
    return week_days


def json_to_stats(json_filename):
    with open(json_filename, encoding='utf') as json_file:
        data = json.load(json_file)

    stats = {}
    messages = data['messages']
    for message in messages:
        timestamp = datetime.datetime.fromtimestamp(int(message['date_unixtime']), tz=pytz.timezone('Europe/Rome'))
        
        day = extract_day(timestamp)
        hour = extract_hour(timestamp)

        if day not in stats:
            stats[day] = {}
        
        if 'total' not in stats[day]:
            stats[day]['total'] = 0
        
        if hour not in stats[day]:
            stats[day][hour] = 0
        
        stats[day][hour] += 1
        stats[day]['total'] += 1
    return stats

def make_triplot(stats, name):
    messages_days = last_30_days()
    for x in messages_days:
        if x not in stats:
            stats[x] = {'total': 0}

    messages_tot = [stats[x].get('total', 0) for x in last_30_days()]
    messages_days = [x[5:]for x in messages_days]
    messages_colors = ['forestgreen' if (x > max(messages_tot) * 0.9) else 'firebrick' if (x < min(messages_tot) * 1.1) else 'steelblue' for x in messages_tot]

    hours = list(stats['average_hours'].keys())
    hours_tot = list(stats['average_hours'].values())
    hours_colors = ['forestgreen' if (x > max(hours_tot) * 0.8) else 'steelblue' for x in hours_tot]

    weekdays = list(stats['average_weekdays'].keys())
    weekdays_tot = list(stats['average_weekdays'].values())
    weekdays_colors = ['forestgreen' if x == max(weekdays_tot) else 'firebrick' if x == min(weekdays_tot) else 'steelblue' for x in weekdays_tot]

    plt.rcParams["figure.figsize"] = (12.8, 8)
    fig = plt.figure(tight_layout=True)
    gs = gridspec.GridSpec(2, 3)
    ax = fig.add_subplot(gs[0, :])
    ax.spines.right.set_visible(False)
    ax.spines.top.set_visible(False)
    ax.spines.left.set_visible(False)
    ax.grid(axis='y', color='lightgray', linestyle='-', linewidth=0.5, zorder=1)
    ax.bar(messages_days, messages_tot, color=messages_colors, width=0.6, zorder=2)
    ax.set_title('Messaggi giornalieri', fontsize=18, pad=10)
    for label in ax.get_xticklabels():
        label.set_ha("right")
        label.set_rotation(45)
    ax.tick_params(axis='y', left=False)

    ax = fig.add_subplot(gs[1, 0:2])
    ax.spines.right.set_visible(False)
    ax.spines.top.set_visible(False)
    ax.spines.left.set_visible(False)
    ax.grid(axis='y', color='lightgray', linestyle='-', linewidth=0.5, zorder=1)
    ax.set_title("Ore di attività", fontsize=18, pad=10)
    ax.bar(hours, hours_tot, width=0.6, color=hours_colors, zorder=2)
    ax.tick_params(axis='x', bottom=False)
    ax.tick_params(axis='y', left=False)

    ax = fig.add_subplot(gs[1, 2])
    ax.spines.right.set_visible(False)
    ax.spines.top.set_visible(False)
    ax.spines.bottom.set_visible(False)
    ax.grid(axis='x', color='lightgray', linestyle='-', linewidth=0.5, zorder=1)
    ax.set_title("Giorni di attività", fontsize=18, pad=10)
    ax.barh(weekdays, weekdays_tot, height=0.3, color=weekdays_colors, zorder=2)
    ax.tick_params(axis='y', left=False)
    ax.tick_params(axis='x', bottom=False)
    ax.invert_yaxis() 

    plt.savefig(f'images/charts/{name}.png')
    return f'images/charts/{name}.png'

def try_this_at_home():
    stats = json_to_stats('db/stats/stats_diochan2_raw.json')
    name = "diochan2"
    list_days = last_30_days()
    list_hours = list_24_hours()

    stats['average_hours'] = {'00': 0, '01': 0, '02': 0, '03': 0, '04': 0, '05': 0, '06': 0, '07': 0, '08': 0, '09': 0, '10': 0, '11': 0, '12': 0, '13': 0, '14': 0, '15': 0, '16': 0, '17': 0, '18': 0, '19': 0, '20': 0, '21': 0, '22': 0, '23': 0}

    stats['average_weekdays'] = {'Lunedì': 0, 'Martedì': 0, 'Mercoledì': 0, 'Giovedì': 0, 'Venerdì': 0, 'Sabato': 0, 'Domenica': 0}

    for day in list_days:
        if day in stats:
            weekday = datetime.datetime.strptime(day, "%Y-%m-%d").strftime("%A").capitalize()
            stats['average_weekdays'][weekday] += stats[day].get('total', 0)
            for hour in list_hours:
                stats['average_hours'][hour] += stats[day].get(hour, 0)

    filename = make_triplot(stats, name)



async def save_messages_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'stats' not in context.chat_data:
        context.chat_data['stats'] = {}

    day = extract_day(update.message.date)
    hour = extract_hour(update.message.date)

    if day not in context.chat_data['stats']:
        context.chat_data['stats'][day] = {}
    
    if 'total' not in context.chat_data['stats'][day]:
        context.chat_data['stats'][day]['total'] = 0
    
    if hour not in context.chat_data['stats'][day]:
        context.chat_data['stats'][day][hour] = 0
    
    context.chat_data['stats'][day][hour] += 1
    context.chat_data['stats'][day]['total'] += 1


async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    
    stats = context.chat_data.get('stats')
    if not stats:
        await update.message.reply_text('Non ho ancora statistiche da mostrarti')
        return
    
    name = str(update.effective_chat.id)

    list_days = last_30_days()
    list_hours = list_24_hours()

    stats['average_hours'] = {'00': 0, '01': 0, '02': 0, '03': 0, '04': 0, '05': 0, '06': 0, '07': 0, '08': 0, '09': 0, '10': 0, '11': 0, '12': 0, '13': 0, '14': 0, '15': 0, '16': 0, '17': 0, '18': 0, '19': 0, '20': 0, '21': 0, '22': 0, '23': 0}

    stats['average_weekdays'] = {'Lunedì': 0, 'Martedì': 0, 'Mercoledì': 0, 'Giovedì': 0, 'Venerdì': 0, 'Sabato': 0, 'Domenica': 0}

    for day in list_days:
        if day in stats:
            weekday = datetime.datetime.strptime(day, "%Y-%m-%d").strftime("%A").capitalize()
            stats['average_weekdays'][weekday] += stats[day].get('total', 0)
            for hour in list_hours:
                stats['average_hours'][hour] += stats[day].get(hour, 0)

    filename = make_triplot(stats, name)
    await update.message.reply_photo(open(filename, 'rb'))


async def populate_chat_data_from_jsons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    for filename in os.listdir('db/stats'):
        if filename.endswith('.json'):
            with open(f'db/stats/{filename}', encoding='utf') as json_file:
                data = json.load(json_file)
            chat_id = int(f"-100{data['id']}")
            stats = json_to_stats(f'db/stats/{filename}')
            if not context.application.chat_data[chat_id].get('stats'):
                context.application.chat_data[chat_id]['stats'] = {}
            print(f"{filename} {chat_id} {len(stats)}")
            context.application.chat_data[chat_id]['stats'] = stats
            await update.message.reply_text(f'Ho popolato il chat_data con le statistiche di {filename}, ID: {chat_id}')
            statistiche = context.application.chat_data[chat_id]
            print(statistiche['stats'])


# try_this_at_home()