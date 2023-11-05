import datetime
import json
import locale
import platform
import warnings

import instaloader
import pytz
from telegram import Update
from telegram import __version__ as TG_VER
from telegram.constants import ParseMode
from telegram.ext import AIORateLimiter, Application, ApplicationBuilder, Defaults, PicklePersistence

import config
from cron_jobs import (
    check_compleanni,
    delete_yesterday_chatlog,
    do_global_backup,
    lotto_member_count,
    parse_diochan,
    # parse_niuchan,
    post_solarsystem_mastodon,
)
from database import Chatlog, Compleanni, Quote, Reminders, TensorMessage
from error_handler import error_handler
from reminders import send_reminder
from handlers import generate_handlers_dict
from utils import count_k_v, get_now, get_reminders_from_db

warnings.filterwarnings("ignore")


def main():
    defaults = Defaults(
        parse_mode=ParseMode.HTML, tzinfo=pytz.timezone("Europe/Rome"), block=False, allow_sending_without_reply=True
    )
    print(f"{get_now()} Costruisco l'applicazione...")

    builder = ApplicationBuilder()
    builder.token(config.BOT_TOKEN)
    builder.persistence(PicklePersistence(filepath="db/picklepersistence"))
    builder.arbitrary_callback_data(True)
    builder.rate_limiter(AIORateLimiter())
    builder.defaults(defaults)
    builder.read_timeout(30.0)
    builder.connect_timeout(30.0)
    builder.write_timeout(30.0)
    builder.pool_timeout(5.0)
    builder.post_init(post_init)
    builder.post_shutdown(post_shutdown)

    builder.http_version("1.1")
    builder.get_updates_http_version("1.1")

    app = builder.build()

    print(f"{get_now()} Aggiungo i job...")

    j = app.job_queue

    j.run_repeating(parse_diochan, interval=1800, data=None, job_kwargs={"misfire_grace_time": 25})
    # j.run_repeating(parse_niuchan, interval=1800, data=None, job_kwargs={'misfire_grace_time': 25})

    j.run_daily(lotto_member_count, datetime.time(hour=9, minute=0, tzinfo=pytz.timezone("Europe/Rome")), data=None)
    j.run_daily(
        post_solarsystem_mastodon, datetime.time(hour=8, minute=30, tzinfo=pytz.timezone("Europe/Rome")), data=None
    )
    j.run_daily(check_compleanni, datetime.time(hour=0, minute=0, tzinfo=pytz.timezone("Europe/Rome")), data=None)
    j.run_daily(check_compleanni, datetime.time(hour=12, minute=00, tzinfo=pytz.timezone("Europe/Rome")), data=None)
    j.run_daily(check_compleanni, datetime.time(hour=20, minute=00, tzinfo=pytz.timezone("Europe/Rome")), data=None)
    j.run_daily(do_global_backup, datetime.time(hour=2, minute=00, tzinfo=pytz.timezone("Europe/Rome")), data=None)
    j.run_daily(
        delete_yesterday_chatlog, datetime.time(hour=1, minute=00, tzinfo=pytz.timezone("Europe/Rome")), data=None
    )
    # j.run_daily(autolurkers, datetime.time(hour=9, minute=0, tzinfo=pytz.timezone('Europe/Rome')), data=None)
    # j.run_repeating(plot_boiler_stats, interval=2600.0, data=None, job_kwargs={'misfire_grace_time': 25})

    # Error handler
    app.add_error_handler(error_handler)

    # Handlers
    print(f"{get_now()} Genero gli handlers...")
    handlers = generate_handlers_dict()

    app.add_handlers(handlers)
    print(f"{get_now()} {len(handlers)} handlers aggiunti.")

    print(f"{get_now()} Inizializzazione completata.\n")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


async def post_init(app: Application) -> None:
    # creo le tabelle se non ci sono
    print(f"{get_now()} Controllo e creo le tabelle necessarie...")

    TensorMessage.create_table()
    Quote.create_table()
    Reminders.create_table()
    Compleanni.create_table()
    Chatlog.create_table()

    # Recupero i set e li storo in memoria
    if "current_sets" not in app.bot_data:
        app.bot_data["current_sets"] = {}

    with open("db/sets.json") as sets_db:
        sets = json.load(sets_db)
        app.bot_data["current_sets"] = sets

    _, v = count_k_v(sets)
    print(f"{get_now()} Sets caricati. {v} keywords totali.")

    # Recupero i reminders e programmo i job
    r = get_reminders_from_db()
    added = 0

    for reminder in r["reminders"]:
        app.job_queue.run_once(
            send_reminder,
            reminder["date_to_remind"],
            chat_id=reminder["chat_id"],
            name=f"{reminder['chat_id']}_{reminder['reply_id']}",
            data=reminder,
        )
        added += 1

    print(f"{get_now()} Trovati {r['processed']} reminders. {added} aggiunti e {r['deleted']} eliminati.")

    # Avvio il webserver per le richieste della banca
    # wapp = web.Application()
    # wapp.add_routes([web.get('/logs', webserver_logs)])
    # runner = web.AppRunner(wapp)
    # await runner.setup()
    # site = web.TCPSite(runner, '0.0.0.0', 8888)
    # await site.start()
    # print(f'{get_now()} Server web inizializzato!')

    # Inizializzo la sessione di Instaloader per Instagram
    L = instaloader.Instaloader(
        dirname_pattern="ig/{target}",
        quiet=True,
        fatal_status_codes=[429],
        save_metadata=False,
        max_connection_attempts=1,
    )
    USER = "emilia_superbot"
    L.load_session_from_file(USER, "db/session-emilia_superbot")

    # Prendo il gruppo per mandare il messaggio di riavvio
    if "last_restart" not in app.bot_data:
        app.bot_data["last_restart"] = config.ID_TESTING

    last_chat_id = app.bot_data["last_restart"]
    await app.bot.send_message(chat_id=last_chat_id, text="Bot riavviato correttamente!")

    print(f"{get_now()} Tutto pronto!\n")
    print(f"{get_now()} In esecuzione!\n")
    return


async def post_shutdown(app: Application) -> None:
    # Pulisco le sessioni di aiohttp rimaste aperte
    # import gc
    # import aiohttp
    # clientsessions = [obj for obj in gc.get_objects() if isinstance(obj, aiohttp.client.ClientSession)]
    # for c in clientsessions:
    #     await c.close()
    return


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "it_IT.utf8")
    print()
    print(f"{get_now()} Avvio - versione: {config.VERSION}\n--------------------------------------------")
    print(f"{get_now()} Using python-telegram-bot v{TG_VER} on Python {platform.python_version()}")

    main()
