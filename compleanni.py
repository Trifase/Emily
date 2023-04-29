import datetime
import re

import peewee
from rich import print
from telegram.error import BadRequest
from telegram import Update
from telegram.ext import ContextTypes

import config
from utils import get_now, no_can_do, printlog

db = peewee.SqliteDatabase(config.DBPATH)

class Compleanni(peewee.Model):
    user_id = peewee.TextField()
    chat_id = peewee.TextField()
    birthdate = peewee.TextField()

    class Meta:
        database = db
        table_name = 'compleanni'
        primary_key = False

# Compleanni
async def compleanni_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    def parse_date(text):

        # Ritorna la data dopo averla controllata, inserendo il secolo se manca e c'è l'anno, leading zeroes se mancano in giorno e mese, o raisa ValueError se è invalida.

        has_year = True
        g = re.match(r"(0?[1-9]|[12][0-9]|3[01])[\/\-](0?[1-9]|1[012])[\/\-]?(\d{4}|\d{2})?$", text)

        if not g:
            raise ValueError("Data Invalida")

        else:
            if not g[3]:
                has_year = False
                y = ""
            elif len(g[3]) == 2:
                y = "19" + g[3] if int(g[3]) > 29 else "20" + g[3]
            else:
                y = g[3]
            d = g[1] if len(g[1]) == 2 else "0" + g[1] 
            m = g[2] if len(g[2]) == 2 else "0" + g[2]
            # print(f'g: {d}, d: {d}, y:  {y}')

            if not has_year:
                birthdate = d + "/" + m
                return birthdate
            else:
                birthdate = d + "/" + m + "/" + y
                return birthdate

    # if update.effective_chat.id != config.ID_TESTING:  # EXCEPT TESTING
    #     return

    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    text = update.message.text[12:]  # togliamo "/compleanno "

    # text deve contenere la data, in formato gg/mm o gg/mm/aa o gg/mm/aaaa. Se l'anno è presente, il bot quando farà gli auguri annuncerà l'età - altrimenti no.
    # Si accettano anche gg-mm o gg-mm-aa o gg-mm-aaaa. Se giorno e mese non hanno il leading zero, viene aggiunti. Se l'anno è di due cifre, diventerà di quattro.
    # vedi la funzione parse_date.

    if not text:
        await update.message.reply_markdown_v2('Devi inserire una data in formato `dd/mm` oppure `dd/mm/yyyy`\.')
        print(f"{get_now()} ERRORE: data non inserita")
        return

    try:
        birthdate = parse_date(text)
    except ValueError:
        await update.message.reply_text('Devi inserire una data valida.')
        print(f"{get_now()} ERRORE: data invalida")
        return



    check = 0
    for row in Compleanni.select().where((Compleanni.user_id == user_id) & (Compleanni.chat_id == chat_id)).limit(1):
        if row:
            check = 1

    if check:
        Compleanni.update(user_id=user_id, chat_id=chat_id, birthdate=birthdate).where((Compleanni.user_id == user_id) & (Compleanni.chat_id == chat_id)).execute()
        # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} modifica il suo compleanno')
        await printlog(update, "modifica il proprio compleanno")
        check = 0
    else:
        # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} aggiunge il suo compleanno')
        await printlog(update, "aggiunge il proprio compleanno", birthdate)
        Compleanni.create(user_id=user_id, chat_id=chat_id, birthdate=birthdate)


    await update.message.reply_text('Compleanno aggiunto!')

async def compleanni_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    counter = 0
    compleanni = ""
    compleannilist = []

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede la lista dei compleanni')
    await printlog(update, "chiede la lista dei compleanni")
    # print(update.message.chat.id)
    for row in Compleanni.select().where(Compleanni.chat_id == update.message.chat.id):
        if row:
            try:
                member = await context.bot.get_chat_member(update.message.chat.id, row.user_id)

                nickname = member.user.mention_html()
                data = row.birthdate
                if len(data) > 5:
                    date = datetime.datetime.strptime(data, '%d/%m/%Y').date()
                else:
                    date = datetime.datetime.strptime(data, '%d/%m').date()
                compleannilist.append([nickname, date])
                counter += 1
            except BadRequest:
                print(row.user_id, "non è più nel gruppo")
                continue
    if counter == 0:
        await update.message.reply_html('Non trovo un cazzo, onestamente', quote=True)
    else:
    #     # print(compleannilist)
        compleannilist.sort(key=lambda x: (x[1].month, x[1].day))
    #     # print(compleannilist)
        for comp in compleannilist:
            nickname = comp[0]
            data = comp[1].strftime("%d/%m")
            compleanni = compleanni + f'{nickname} · {data}\n'
        await context.bot.send_message(update.message.chat.id, compleanni)

async def compleanno_del(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    found = False

    chat_id = update.message.chat.id
    user_id = update.message.from_user.id


    for row in Compleanni.select().where((Compleanni.user_id == user_id) & (Compleanni.chat_id == chat_id)):
        if row:
            found = True

    if found:
        Compleanni.delete().where((Compleanni.user_id == user_id) & (Compleanni.chat_id == chat_id)).execute()
        await update.message.reply_text('Come vuoi.', quote=True)
        # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} ha cancellato il suo compleanno')
        await printlog(update, "cancella il proprio compleanno")
        
    else:
        await update.message.reply_markdown_v2('Non trovo un cazzo onestamente', quote=True)

async def compleanni_manual_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  
    if await no_can_do(update, context):
        return

    if update.message.from_user.id not in config.ADMINS:
        return

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} controlla i compleanni di oggi')
    await printlog(update, "controlla i compleanni di oggi")
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
