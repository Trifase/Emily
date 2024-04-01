import datetime

# import datetime
import json
import locale

import httpx
from bs4 import BeautifulSoup
from dateparser.search import search_dates

# from pprint import pprint
from rich import print
from telegram import Update
from telegram.ext import ContextTypes
from uniplot import plot

import config
from utils import get_now, no_can_do, printlog

locale.setlocale(locale.LC_ALL, "it_IT.utf8")


def get_links(year=2023, month=6) -> list:
    """Get all the daily links for a specific month

    Args:
        year (int, optional): year. Defaults to 2023.
        month (int, optional): month. Defaults to 6.

    Returns:
        list: a list of links
    """
    # base url = https://www.comune.palmadimontechiaro.ag.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/3683?YY=2023&MM=6
    url = f"https://www.comune.palmadimontechiaro.ag.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/3683?YY={year}&MM={month}"
    r = httpx.get(url)
    soup = BeautifulSoup(r.text, features="lxml")
    links = soup.find("div", class_="ElencoCanale")
    links = links.find_all("li")
    links = [link.find("a").get("href") for link in links]
    # pprint(links)
    return links


def analyze_day(url: str, debug=False) -> tuple:
    """Scape a single day link and returns a tuple containing the day in ISO format and a list of quartieri

    Args:
        url (str): the url for the daily page
        debug (bool, optional): print debug informations. Defaults to False.

    Returns:
        tuple: a tuple containing the day in ISO format and a list of quartieri
    """
    r = httpx.get(url)
    soup = BeautifulSoup(r.text, features="lxml")
    breadcrumb = soup.find("div", class_="BreadCrumb")
    data = breadcrumb.find("span").text
    # data = ' '.join(data.split()[-3:])
    text_data = data.replace("Turni erogazione acqua del ", "").strip()
    try:
        data = datetime.datetime.strptime(text_data, "%d %B %Y").date()
    except ValueError:
        date_found = search_dates(
            text_data,
            languages=["it", "en"],
            settings={"PREFER_DATES_FROM": "past", "DEFAULT_LANGUAGES": ["it", "en"]},
        )

        if date_found:
            data = date_found[0][1].date()
    # print(data)
    table = soup.find("table", id="blobTable-2")
    if table:
        celle = table.find_all("td", headers="th_c_2_0")
    else:
        table = soup.find("table", id="blobTable-3")
        celle = table.find_all("td", headers="th_c_3_0")
    celle = [cella.text for cella in celle]

    # erogazione = any(to_search.casefold() in cella.casefold() for cella in celle)
    # if erogazione:
    # pprint(f"{data}: {erogazione}")
    if debug:
        lista_quartieri = []
        for quartiere in celle:
            if len(quartiere) < 3:
                continue
            quartiere = quartiere.strip().split(":")[0].strip()
            quartiere = quartiere.strip().split("(")[0].strip()
            if quartiere not in lista_quartieri:
                lista_quartieri.append(quartiere)

        print(f"[{data}]\t· {', '.join(lista_quartieri)}")
    return (data, celle)


def get_erogazioni(json_file="db/erogazioni.json", quartiere="Garda") -> list:
    """Analyze the json and return a list of days where the quartiere is erogato

    Args:
        json_file (str, optional): json file to analyze. Defaults to "data.json".
        quartiere (str, optional): quartiere to search for. Defaults to "Garda".

    Returns:
        list: a list of strings (dates in ISO format)
    """

    with open(json_file, "r") as f:
        data = json.load(f)
    lista_erogazioni = [key for key in data if erogato_in_quartiere(data[key]["quartieri"], to_search=quartiere)]
    return lista_erogazioni


def erogato_in_quartiere(lista_quartieri, to_search="Garda") -> bool:
    return any(to_search.casefold() in cella.casefold() for cella in lista_quartieri)


def fancy_stats(erogazioni: list, print_plot=True, limit_erogazioni=150, rolling_avg=5, only_data=True):
    if limit_erogazioni > len(erogazioni):
        limit_erogazioni = len(erogazioni)

    erogazioni = erogazioni[-limit_erogazioni:]
    data = {"n_erogazioni": limit_erogazioni}

    last_erogazione = datetime.datetime.strptime(erogazioni[0], "%Y-%m-%d").date()
    data["first_erogazione"] = erogazioni[0]
    data["last_erogazione"] = erogazioni[-1]
    media_erogazione = 0
    n_erogazioni = 0
    last_media = 0
    last_media_roll = 0

    roll_avg = []
    avg = []
    max_erog = {"day": last_erogazione, "delta": 0}

    media_erogazione_roll_avg = [0 for _ in range(rolling_avg)]
    i = 0

    for day in erogazioni:
        i += 1
        this_erogazione = datetime.datetime.strptime(day, "%Y-%m-%d").date()
        delta = this_erogazione - last_erogazione
        n_erogazioni += 1
        media_erogazione += delta.days

        media_erogazione_roll_avg.append(delta.days)
        media_erogazione_roll_avg.pop(0)

        media = media_erogazione / n_erogazioni
        media_roll: float = sum(media_erogazione_roll_avg) / rolling_avg
        roll_avg.append(media_roll)
        avg.append(media)

        if delta.days > max_erog["delta"]:
            max_erog["day"] = day
            max_erog["delta"] = delta.days

        simbolo = "↓" if last_media > media else "↑"
        simbolo_roll = "↓" if last_media_roll > media_roll else "↑"

        last_media = media
        last_media_roll = media_roll
        last_erogazione = this_erogazione

        if not only_data:
            print(
                f"{i}\t{day} | Ultima erogazione: {delta.days} giorni prima\t| {simbolo} Media: {round(media, 2)} giorni\t| {simbolo_roll} Media mobile ({rolling_avg}): {round(media_roll, 2)} giorni"
            )

    data["delta_ultima_erogazione"] = delta.days
    data["max_erogazione_date"] = max_erog["day"]
    data["max_erogazione_delta"] = max_erog["delta"]
    data["rolling_avg_last"] = last_media_roll  # type: ignore
    data["avg_last"] = last_media  # type: ignore

    # print()
    # print(roll_avg)
    if print_plot and not only_data:
        plot(
            roll_avg[5:],
            erogazioni[5:],
            title=f"Media mobile ({rolling_avg} erogazioni) - ultime {limit_erogazioni} erogazioni",
            width=150,
            lines=True,
        )

        # print()
        plot(
            avg[5:],
            erogazioni[5:],
            title=f"Media erogazioni - ultime {limit_erogazioni} erogazioni",
            width=150,
            lines=True,
        )

    if only_data:
        return data


async def acqua_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return

    if update.message.from_user.id not in config.ADMINS:
        return
    
    quartiere = "Garda"
    rolling_avg = 5

    await printlog(update, "chiede informazioni sui turni dell'acqua", quartiere)

    erogazioni = get_erogazioni(json_file=config.DB_ACQUA, quartiere=quartiere)
    stats = fancy_stats(erogazioni, print_plot=False, limit_erogazioni=1000, rolling_avg=rolling_avg)

    message = ""
    message += f"Totale erogazioni analizzate: <code>{stats['n_erogazioni']}</code>, dal <code>{stats['first_erogazione']}</code>.\n"
    message += f"Ultima erogazione <code>{stats['delta_ultima_erogazione']}</code> giorni fa, il <code>{stats['last_erogazione']}</code>.\n"
    message += f"Massima distanza tra due erogazioni: <code>{stats['max_erogazione_delta']}</code> giorni il <code>{stats['max_erogazione_date']}</code>.\n"
    message += f"Media mobile (<code>{rolling_avg}</code> erogazioni) all'ultima erogazione: <code>{round(stats['rolling_avg_last'], 2)}</code> giorni.\n"
    message += f"Media assoluta di tutte le erogazioni: <code>{round(stats['avg_last'], 2)}</code> giorni."

    await update.message.reply_html(message)


async def manual_update_acqua_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return
    if update.message.from_user.id not in config.ADMINS:
        return
    return await update_acqua_db(context)


# Runs every morning at 3:00 (Europe/Rome)
async def update_acqua_db(context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"{get_now()} [AUTO] Aggiorno turni acqua dal sito del comune")
    today = datetime.datetime.today()
    year = today.year
    month = today.month

    db = json.load(open(config.DB_ACQUA, "r"))
    links = get_links(year=year, month=month)

    for link in links:
        data, celle = analyze_day(link, debug=False)
        if data.strftime("%Y-%m-%d") in db:
            continue
        else:
            db[data.strftime("%Y-%m-%d")] = {"quartieri": celle}

    # Sorta il db per data, lo salva di nuovo sul json
    db = dict(sorted(db.items()))
    j = json.dumps(db)
    with open(config.DB_ACQUA, "w") as f:
        f.write(j)

    print(f"{get_now()} [AUTO] Turni acqua aggiornati.")
