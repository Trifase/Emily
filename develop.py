from dateparser.search import search_dates
import datetime


t = [
    "4h ricordami di",
    "10h ricordmai di",
    "4hrs ricordami di",
    "4 hrs ricordami di",
    "4 hours ricordami di",
    "4o ricordami di",
    "4 o ricordami di",
    "4ore ricordami di",
    "4 ore ricordami di",
    "5m ricordami di",
    "5 minuti ricordami di ",
    "5 min ricordami di",
    "5min ricordami di",
    "5mins ricordami di",
    "5 mins ricordami di",
    "5 minutes ricordami di",
    "10m ricordami di",
    "4h5m ricordami di",
    "domani ricordami di",
    "domani alle 10 ricordami di",
    "domani alle 10:00 ricordami di",
    "domani alle 10:00:00 ricordami di",
    "una settimana ricordami di",
    "il 5 maggio ricordami di",
    "il 5 maggio alle 10 ricordami di",
    "fra due mesi ricordami di"

]
max_len = max([len(x) for x in t])
for text in t:
    date_found = search_dates(text, languages=["it", "en"], settings={'PREFER_DATES_FROM': 'future', 'DEFAULT_LANGUAGES': ['it', 'en'] })

    if not date_found:
        print(f"{text.ljust(max_len)} <|> non ho capito.")
        continue

    # computa la data target
    targetdate = date_found[0][1].strftime("%d/%m/%Y %H:%M")
    # la parte di stringa analizzata
    trigger_text = date_found[0][0]
    # il messaggio da ricordare
    message = text.replace(trigger_text, '').strip()

    if date_found[0][1] < datetime.datetime.now():
        print(f"{text} <|> è nel passato ({targetdate}).")
        continue

    print(f"{text.ljust(max_len)}  | {targetdate}\t| {message}")
