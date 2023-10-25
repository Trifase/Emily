import datetime

from dateparser.search import search_dates
from telegram import Update
from telegram.ext import ContextTypes

from database import Reminders
from utils import get_now, no_can_do, printlog


# Reminder
async def reminder_helper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    await update.message.reply_markdown_v2(
        "Uso: \n`/remindme 3d15h25m messaggio`\n`/remindme 5m butta la pasta`\nUsa `/reminderlist` per la lista dei tuoi reminder e \n`/remindelete <ID>` per eliminare un reminder",
        quote=True,
    )
    return


# Gets Job from APScheduler, send a message and delete entry from SQlite
async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    row = context.job.data
    message = row.get("message")
    date_now = row.get("date_now").strftime("%d/%m/%Y %H:%M")
    print(f'{get_now()} Trovato un reminder: "{message}" del {date_now}')

    if not message:
        missiva = "Bip Bop Bup! Mi avevi chiesto di blipparti!"
    else:
        missiva = f"Ciao, mi avevi chiesto di ricordarti questo: {message}"

    user = await context.bot.get_chat_member(chat_id=row["chat_id"], user_id=row["user_id"])
    await context.bot.send_message(
        row["chat_id"],
        f"[{user.user.mention_html()}] {missiva}",
        reply_to_message_id=row["reply_id"],
        allow_sending_without_reply=True,
    )
    Reminders.delete().where((Reminders.reply_id == row["reply_id"]) & (Reminders.chat_id == row["chat_id"])).execute()


async def remindme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    # global reply_id
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    reply_id = update.message.message_id
    text = update.message.text
    text = text[10:]  # togliamo "/remindme "

    if not context.args:
        await update.message.reply_markdown_v2(
            "Devi inserire un lasso di tempo\.\nTempo relativo:\n`/remindme 3 giorni 15 ore messaggio`\n`/remindme 10m butta la pasta`\nTempo assoluto:\n`/remindme 23:59 vai a dormire`\n`/remindme 25/12/2024 Natale`\n`/remindme 31/12/2026 23:56 Capodanno!`\n\nUsa `/reminderlist` per la lista dei tuoi reminder e \n`/remindelete <ID>` per eliminare un reminder",
            quote=True,
        )
        return

    date_found = search_dates(text, languages=["it"], settings={"PREFER_DATES_FROM": "future"})

    if not date_found:
        await update.message.reply_html("Mi dispiace, non sono riuscita a capire la data e l'orario, scusa.")
        return

    if date_found[0][1] < datetime.datetime.now():
        await update.message.reply_text(
            f"Non posso ricordarti qualcosa nel passato.\nLa data che ho capito: <code>{date_found[0][1].strftime('%d/%m/%Y %H:%M')}</code>"
        )
        return

    targetdate = date_found[0][1].strftime("%d/%m/%Y %H:%M")

    if targetdate.endswith("00:00") and "00:00" not in text:
        targetdate = targetdate.replace("00:00", "8:00")

    trigger_text = date_found[0][0]
    message = text.replace(trigger_text, "").strip()

    datenow = str(datetime.datetime.today().strftime("%d/%m/%Y %H:%M"))

    if not message:
        await update.message.reply_markdown_v2(f"Tranquillo, ti avviso io il `{targetdate}`", quote=True)
    else:
        await update.message.reply_markdown_v2(f"Il `{targetdate}` ti ricorderò questo: `{message}`", quote=True)

    Reminders.create(
        reply_id=reply_id,
        user_id=user_id,
        chat_id=chat_id,
        date_now=datenow,
        date_to_remind=targetdate,
        message=message,
    )

    r = {}
    r["message"] = message
    r["reply_id"] = reply_id
    r["user_id"] = user_id
    r["chat_id"] = chat_id
    r["date_now"] = datetime.datetime.strptime(datenow, "%d/%m/%Y %H:%M")
    r["date_to_remind"] = datetime.datetime.strptime(targetdate, "%d/%m/%Y %H:%M")

    context.job_queue.run_once(
        send_reminder, r["date_to_remind"], chat_id=chat_id, name=f"{chat_id}_{reply_id}", data=r
    )

    await printlog(update, "vuole che ricordi qualcosa il", f"{targetdate} messaggio: \[{message}]")


async def reminders_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    counter = 0
    reminders = ""
    await printlog(update, "chiede la lista dei reminders")

    for row in Reminders.select().where(
        (Reminders.user_id == update.message.from_user.id) & (Reminders.chat_id == update.message.chat.id)
    ):
        if row:
            counter += 1
            reminders += f'`[{row.reply_id}] - {row.date_to_remind} - "{row.message}"`\n'

    if counter:
        await context.bot.send_message(update.message.chat.id, reminders, parse_mode="MarkdownV2")
    else:
        await update.message.reply_markdown_v2("Non trovo un cazzo onestamente", quote=True)


async def remindelete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    reply_id = " ".join(context.args)  # prende l'ID dal comando
    if not reply_id:
        await update.message.reply_html("Non hai specificato un ID")
        return

    await printlog(update, "vuole cancellare il reminder", reply_id)

    for row in Reminders.select().where(
        (Reminders.user_id == update.message.from_user.id)
        & (Reminders.chat_id == update.message.chat.id)
        & (Reminders.reply_id == reply_id)
    ):
        if row:
            deletequery = Reminders.delete().where(
                (Reminders.user_id == update.message.from_user.id)
                & (Reminders.chat_id == update.message.chat.id)
                & (Reminders.reply_id == reply_id)
            )
            deletequery.execute()

            name = f"{Reminders.chat_id}_{reply_id}"

            current_jobs = context.job_queue.get_jobs_by_name(name)
            for job in current_jobs:
                job.schedule_removal()

            await update.message.reply_html("Fatto", quote=True)
        else:
            await update.message.reply_html("Non trovo un cazzo onestamente", quote=True)


# # A LITT'L BIT OF CLEANIN'
# now = datetime.datetime.today()
# c = 0
# for row in Reminders.select():
#     # print(f"{row.reply_id} · {row.user_id} · {row.chat_id} · {row.date_now} · {row.date_to_remind} · {row.message}")
#     target_datetime = datetime.datetime.strptime(row.date_to_remind, "%d/%m/%Y %H:%M")
#     if now > target_datetime:
#         Reminders.delete().where((Reminders.reply_id == row.reply_id) & (Reminders.chat_id == row.chat_id)).execute()
#         c += 1
# print(f"Cancellati {c} reminder")
