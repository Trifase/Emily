import datetime
import json
from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import CallbackContext, ContextTypes


async def save_messages_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def extract_day(timestamp):
        return timestamp.strftime("%Y-%m-%d")

    def extract_hour(timestamp):
        return timestamp.strftime("%H")

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



def get_significant_hour(timestamp=None, return_string=True):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    else:
        timestamp = datetime.datetime.fromtimestamp(timestamp)
    zeroed_timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
    if return_string:
        return zeroed_timestamp.strftime("%Y-%m-%d %H:%M")
    else:
        return zeroed_timestamp

def get_significant_day(timestamp=None, return_string=True):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    else:
        timestamp = datetime.datetime.fromtimestamp(timestamp)
    zeroed_timestamp = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

    if return_string:
        return zeroed_timestamp.strftime("%Y-%m-%d")
    else:
        return zeroed_timestamp


def get_daily_messages(json_filename, user_id=None):
    with open(json_filename, encoding='utf') as json_file:
        data = json.load(json_file)
    stats = {}
    messages = data['messages']
    for message in messages:
        if user_id is not None:
            if message.get('from_id') != f'user{user_id}':
                continue

        timestamp = message['date_unixtime']
        significant_day = get_significant_day(int(timestamp), return_string=False)
        if significant_day not in stats:
            stats[significant_day] = 0
        stats[significant_day] += 1
    return stats

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


stats = get_daily_messages('db/stats/stats_diochan2_raw.json')
name = 'diochan2'
dats = list(stats.keys())
dats = [x.strftime('%m-%d') for x in dats]
vals = list(stats.values())


plt.rcParams["figure.figsize"] = (20,6)
plt.bar(dats, vals)
plt.title('Messages by Day', fontsize=18, pad=10)
plt.xticks(rotation=45, ha='right')
plt.xticks(dats)
plt.ylabel('Number of messages')

plt.tight_layout()
plt.savefig(f'{name}.jpg')

