import datetime
import peewee

from pytimeparse import parse
from telegram import Update, Bot
from telegram.ext import CallbackContext, ContextTypes
from rich import print
from dateutil.parser import parse as parse_date

import config

from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do

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


# Reminder
async def reminder_helper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    await update.message.reply_markdown_v2(
        f'Uso: \n`/remindme 3d15h25m messaggio`\n`/remindme 5m butta la pasta`\nUsa `/reminderlist` per la lista dei tuoi reminder e \n`/remindelete <ID>` per eliminare un reminder',
        quote=True)
    return


# Gets Job from APScheduler, send a message and delete entry from SQlite
async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    # datenow = str(datetime.datetime.today().strftime("%d/%m/%Y %H:%M"))
    # for row in Reminders.select().where(Reminders.date_to_remind == datenow):
        # if row:
    row = context.job.data
    message = row.get('message')
    date_now = row.get('date_now').strftime("%d/%m/%Y %H:%M")
    print(f'{get_now()} Trovato un reminder: "{message}" del {date_now}')

    if not message:
        missiva = f'Bip Bop Bup! Mi avevi chiesto di blipparti!'
    else:
        missiva = f'Ciao, mi avevi chiesto di ricordarti questo: {message}'

    user = await context.bot.get_chat_member(chat_id=row['chat_id'], user_id=row['user_id'])

    await context.bot.send_message(row['chat_id'], f"[{user.user.mention_html()}] {missiva}", reply_to_message_id=row['reply_id'], allow_sending_without_reply=True)
    Reminders.delete().where(Reminders.reply_id == row['reply_id'] and Reminders.chat_id == row['chat_id']).execute()
    print(f'{get_now()} Reminder annunciato e cancellato.')


async def remindme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    global reply_id
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    reply_id = update.message.message_id
    text = update.message.text
    text = text[10:]  # togliamo "/remindme "
    if not context.args:
        await update.message.reply_markdown_v2(
            f'Devi inserire un lasso di tempo\.\nTempo relativo:\n`/remindme 3d15h25m messaggio`\n`/remindme 5m butta la pasta`\nTempo assoluto:\n`/remindme 23:59 vai a dormire`\n`/remindme 25/12/2024 Natale`\n`/remindme 31/12/2026 23:56 Capodanno!`\n\nUsa `/reminderlist` per la lista dei tuoi reminder e \n`/remindelete <ID>` per eliminare un reminder',
            quote=True)
        return
    if ":" in text or "/" in text:  # ora assoluta
        if text.count("/") == 1:
            await update.message.reply_html("Se indichi una data, deve essere completa di anno, ad esempio:\n<code>/remindme 11/09/2001 08:46 chiudere le imposte</code>")
            return
        # print(text[:17])
        targetdate = str(parse_date(text[:17], fuzzy=True, dayfirst=True).strftime("%d/%m/%Y %H:%M"))
        if parse_date(text[:17], fuzzy=True, dayfirst=True) < datetime.datetime.now():
            await update.message.reply_text("Lascia andare il passato e pensa al futuro.")
            return
        if (targetdate.endswith("00:00")) and ("00:00" not in text):
            message = text[len(text.split()[0]) + 1:]
        else:
            message = text[len(text.split()[0]) + len(text.split()[1]) + 2:]
    else:  # ora non precisa
        try:
            secondi = parse(text.split()[0])  # parsiamo delay
        except IndexError:
            await update.message.reply_markdown_v2(
                f'Tempo relativo:\n`/remindme 3d15h25m messaggio`\n`/remindme 5m butta la pasta`\nTempo assoluto:\n`/remindme 23:59 vai a dormire`\n`/remindme 25/12/2024 Natale`\n`/remindme 31/12/2026 23:56 Capodanno!`\n\nUsa `/reminderlist` per la lista dei tuoi reminder e \n`/remindelete <ID>` per eliminare un reminder',
                quote=True)  # /remindme 20/04/2021 15:15 messaggio`\n`/remindme 13:18 messaggio`\n
            return
        if not secondi:  # non parsa correttamente
            await update.message.reply_markdown_v2(
                f'Tempo relativo:\n`/remindme 3d15h25m messaggio`\n`/remindme 5m butta la pasta`\nTempo assoluto:\n`/remindme 23:59 vai a dormire`\n`/remindme 25/12/2024 Natale`\n`/remindme 31/12/2026 23:56 Capodanno!`\n\nUsa `/reminderlist` per la lista dei tuoi reminder e \n`/remindelete <ID>` per eliminare un reminder',
                quote=True)  # /remindme 20/04/2021 15:15 messaggio`\n`/remindme 13:18 messaggio`\n
            return
        else:
            targetdate = str((datetime.datetime.today() + datetime.timedelta(seconds=secondi)).strftime("%d/%m/%Y %H:%M"))
        message = text[len(text.split()[0]) + 1:]

    datenow = str(datetime.datetime.today().strftime("%d/%m/%Y %H:%M"))

    if not message:
        await update.message.reply_markdown_v2(f'Tranquillo, ti avviso io il `{targetdate}`', quote=True)
    else:
        await update.message.reply_markdown_v2(f'Il `{targetdate}` ti ricorder?? questo: `{message}`', quote=True)

    Reminders.create(reply_id=reply_id, user_id=user_id, chat_id=chat_id, date_now=datenow, date_to_remind=targetdate, message=message)

    r = {}
    r['message'] = message
    r['reply_id'] = reply_id
    r['user_id'] = user_id
    r['chat_id'] = chat_id
    r['date_now'] = datetime.datetime.strptime(datenow, "%d/%m/%Y %H:%M")
    r['date_to_remind'] = datetime.datetime.strptime(targetdate, "%d/%m/%Y %H:%M")

    context.job_queue.run_once(send_reminder, r['date_to_remind'], chat_id=chat_id, name=f"{chat_id}_{reply_id}", data=r)

    await printlog(update, "vuole che ricordi qualcosa il", f"{targetdate} messaggio: \[{message}]")


async def reminders_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    counter = 0
    reminders = ""
    await printlog(update, "chiede la lista dei reminders")

    for row in Reminders.select().where((Reminders.user_id == update.message.from_user.id) & (Reminders.chat_id == update.message.chat.id)):
        if row:
            counter += 1
            reminders += f'`[{row.reply_id}] - {row.date_to_remind} - "{row.message}"`\n'

    if counter:
        await context.bot.send_message(update.message.chat.id, reminders, parse_mode='MarkdownV2')
    else:
        await update.message.reply_markdown_v2(f'Non trovo un cazzo onestamente', quote=True)

async def remindelete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return


    found = False
    reply_id = " ".join(context.args)  # prende l'ID dal comando
    if not reply_id:
        await update.message.reply_html("Non hai specificato un ID")
        return

    await printlog(update, "vuole cancellare il reminder", reply_id)


    for row in Reminders.select().where(
            (Reminders.user_id == update.message.from_user.id) &
            (Reminders.chat_id == update.message.chat.id) &
            (Reminders.reply_id == reply_id)):
        if row:

            deletequery = Reminders.delete().where(
                (Reminders.user_id == update.message.from_user.id)
                & (Reminders.chat_id == update.message.chat.id)
                & (Reminders.reply_id == reply_id))
            deletequery.execute()

            name = f"{Reminders.chat_id}_{reply_id}"

            current_jobs = context.job_queue.get_jobs_by_name(name)
            for job in current_jobs:
                job.schedule_removal()

            await update.message.reply_html(f'Fatto', quote=True)
        else:
            await update.message.reply_html(f'Non trovo un cazzo onestamente', quote=True)



# # A LITT'L BIT OF CLEANIN'
# now = datetime.datetime.today()
# c = 0
# for row in Reminders.select():
#     # print(f"{row.reply_id} ?? {row.user_id} ?? {row.chat_id} ?? {row.date_now} ?? {row.date_to_remind} ?? {row.message}")
#     target_datetime = datetime.datetime.strptime(row.date_to_remind, "%d/%m/%Y %H:%M")
#     if now > target_datetime:
#         Reminders.delete().where((Reminders.reply_id == row.reply_id) & (Reminders.chat_id == row.chat_id)).execute()
#         c += 1
# print(f"Cancellati {c} reminder")

