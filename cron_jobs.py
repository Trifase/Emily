import datetime
import random
from telegram.ext import CallbackContext, ContextTypes

from utils import printlog, get_display_name, get_now
import config
from rich import print
from rich.progress import track
import peewee

db = peewee.SqliteDatabase(config.DBPATH)

class Reminders(peewee.Model):
    reply_id = peewee.TextField()
    user_id = peewee.TextField()
    chat_id = peewee.TextField()
    date_now = peewee.TextField()
    date_to_remind = peewee.TextField()
    message = peewee.TextField()

    class Meta:
        database = db
        table_name = 'reminders'
        primary_key = False

class Compleanni(peewee.Model):
    user_id = peewee.TextField()
    chat_id = peewee.TextField()
    birthdate = peewee.TextField()

    class Meta:
        database = db
        table_name = 'compleanni'
        primary_key = False




# Runs every minute
async def check_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    datenow = str(datetime.datetime.today().strftime("%d/%m/%Y %H:%M"))
    for row in Reminders.select().where(Reminders.date_to_remind == datenow):
        if row:
            print(f'{get_now()} Trovato un reminder: "{row.message}" del {row.date_now}',)
            if not row.message:
                missiva = f'Bip Bop Bup! Mi avevi chiesto di blipparti!'
            else:
                missiva = f'Ciao, mi avevi chiesto di ricordarti questo: {row.message}'
            user = await context.bot.get_chat_member(chat_id=row.chat_id, user_id=row.user_id)
            await context.bot.send_message(row.chat_id, f"[{user.user.mention_html()}] {missiva}", reply_to_message_id=row.reply_id, allow_sending_without_reply=True)
            Reminders.delete().where(Reminders.reply_id == row.reply_id).execute()
            print(f'{get_now()} Reminder annunciato e cancellato.')

# Runs every day at 9:00 (Europe/Rome)
async def lotto_member_count(context: ContextTypes.DEFAULT_TYPE) -> None:
    # print("Controllo il lotto")
    newcount = await context.bot.get_chat_member_count(config.ID_LOTTO)
    # if 'lotto_history' not in context.bot_data:
    #     context.bot_data['lotto_history'] = []
        
    # context.bot_data['lotto_history'].append(f"{datetime.datetime.now().strftime('%Y-%m-%d_%H:%M')}_{newcount}")
    # print(f"Ci sono {newcount} anime adesso")
    oldcount = context.bot_data.get('lotto_count', 0)
    # print(f"C'erano {oldcount} anime prima")
    if newcount != oldcount:
        context.bot_data['lotto_count'] = newcount
        await context.bot.send_message(config.ID_LOTTO, f"Popolazione: {newcount} anime.")
        return
    else:
        return



# Runs every day at 2:00 (Europe/Rome)
# Doesn't run anymore, see do_global_backup
async def do_backup(context: ContextTypes.DEFAULT_TYPE):
    import shutil
    for filename in ['picklepersistence', 'sqlite.db', 'sets.json']:
        print(f"{get_now()} [AUTO] Eseguo il backup del file {filename}")
        oldfile = f"db/{filename}"
        newfile = f"db/backups/{datetime.datetime.today().strftime('%Y%m%d_%H%M%S')}-{filename}"
        shutil.copy(oldfile, newfile)
    print(f"{get_now()} [AUTO] Backup eseguito")

# Runs every day at 2:00 (Europe/Rome)
async def do_global_backup(context: ContextTypes.DEFAULT_TYPE):
    import os
    import zipfile
    import datetime

    now = datetime.datetime.today().strftime('%Y%m%d_%H%M%S')

    backup_dir = "backups"
    archive_name = f"{backup_dir}/{now}-backup.zip"

    IGNORED_DIRS = [
        f"./{backup_dir}", "./db/backups", "./__pycache__",
        "./ig", "./.git/", "./reddit", "./images/tarots",
        "./.vscode", "./banca"
        ]
    IGNORED_FILES = [f"{now}-backup.zip", "condominioweb.jsonl.zst", "logs.txt"]

    skipped = 0
    backupped = 0

    with zipfile.ZipFile(archive_name, 'w') as zip_ref:
        to_archive = []
        for folder_name, subfolders, filenames in os.walk('.'):
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
        await context.bot.send_document(chat_id=config.ID_TRIF, document=open(archive_name, 'rb'))
        print(f"{get_now()} [AUTO] Backup globale eseguito: {archive_name} - File archiviati: {backupped} - File Skippati: {skipped} - File inviato su TG")
    except Exception as e:
        print(f"{get_now()} [AUTO] Backup globale eseguito: {archive_name} - File archiviati: {backupped} - File Skippati: {skipped} - File NON inviato su TG\n{e}")

# Runs every day at 9:00 and 18:00 (Europe/Rome)
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
                if y:
                    anni = int(today_y) - int(y)
                    if anni > 100:
                        await context.bot.send_message(row.chat_id, f"Auguri {nickname}! Oggi compi {anni} anni! Li porti benissimo! Sarai mica un vampiro?")
                    else:
                        await context.bot.send_message(row.chat_id, f"Auguri {nickname}! Oggi compi {anni} anni!")
                else:
                    await context.bot.send_message(row.chat_id, f"Auguri {nickname}! Buon compleanno!")