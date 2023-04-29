from dateparser.search import search_dates
import datetime


t = [
    "4h cala la pasta     ",
    "4 hours cala la pasta",
    "4h10m cala la pasta  ",
    "4o cala la pasta     ",
    "4 o cala la pasta    ",
    "4ore cala la pasta   ",
    "4 ore cala la pasta  ",
    "20:30 cala la pasta  ",
    "240m fai questa cosa ",
    "3d15h25m messaggio   ",
    "5m butta la pasta    "
]

for text in t:
    date_found = search_dates(text, languages=["it", "en"], settings={'PREFER_DATES_FROM': 'future'})

    if not date_found:
        print(f"{text}: non ho capito.")
        continue

    targetdate = date_found[0][1].strftime("%d/%m/%Y %H:%M")
    if date_found[0][1] < datetime.datetime.now():
        print(f"{text}: è nel passato ({targetdate}).")
        continue
    print(f"{text}: {targetdate}")
