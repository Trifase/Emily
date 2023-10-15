import datetime

import requests
from telegram import Update
from telegram.ext import ContextTypes

import config
from utils import no_can_do, printlog


async def ora(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede l\'ora')
    await printlog(update, "chiede l'ora")
    if not context.args:
        await update.message.reply_text("Inserisci una città")
        return
    API_KEY = config.OWM_API_KEY
    if len(context.args) == 1:
        citta = context.args[0]
    elif len(context.args) > 1:
        citta = " ".join(context.args)
    else:
        await update.message.reply_text("Devi inserire una città.")
        return
    # citta += ",,it"
    geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
    query = {
        "q": citta,
        "appid": API_KEY
    }
    geocoding = requests.get(geocoding_url, query)
    geodata = geocoding.json()

    if not geodata:
        await update.message.reply_text("Nessuna città trovata.")
        return

    lat = geodata[0]['lat']
    lon = geodata[0]['lon']
    country = geodata[0]['country']
    name = geodata[0]['name']
    print(f"[Open Weather Map] Cerco: {name}, {country} [{lat}, {lon}]")

    weather_url = "https://api.openweathermap.org/data/2.5/onecall"
    weather_query = {
        "lon": lon,
        "lat": lat,
        "units": "metric",
        "lang": "it",
        "exclude": "minutely,hourly",
        "appid": API_KEY
    }
    weather = requests.get(weather_url, weather_query)
    data = weather.json()

    try:
        meteo = data['current']
    except KeyError:
        # data['error']
        await update.message.reply_text("Errore.")
        return

    ora = f"Sono le {datetime.datetime.utcfromtimestamp(meteo['dt'] + data['timezone_offset']).strftime('%H:%M')} del {datetime.datetime.utcfromtimestamp(meteo['dt']+ data['timezone_offset']).strftime('%d/%m')}"

    await update.message.reply_text(ora)


async def prometeo_oggi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    citta = ""
    if not context.args:
        if 'default_meteo_city' in context.user_data:
            citta = context.user_data['default_meteo_city']
        else:
            await update.message.reply_html("Inserisci una città.\nSe vuoi impostare una città di default puoi usare <code>-setdefault [città]</code>, ad esempio: <code>/prometeo -setdefault Napoli</code>")
            return
    else:
        if context.args[0] == "-setdefault":
            default_city = ' '.join(context.args[1:])
            context.user_data['default_meteo_city'] = default_city
            await update.message.reply_text(f"Salvata: {default_city}")
            return

    API_KEY = config.OWM_API_KEY
    if not citta:
        if len(context.args) == 1:
            citta = context.args[0]
        elif len(context.args) > 1:
            citta = " ".join(context.args)
        else:
            await update.message.reply_text("Devi inserire una città.")
            return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede il meteo di oggi: {citta}')
    await printlog(update, "chiede prometeo di oggi", citta)
    # citta += ",,it"
    geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
    query = {
        "q": citta,
        "appid": API_KEY
    }
    geocoding = requests.get(geocoding_url, query)
    geodata = geocoding.json()

    if not geodata:
        await update.message.reply_text("Nessuna città trovata.")
        return

    lat = geodata[0]['lat']
    lon = geodata[0]['lon']
    country = geodata[0]['country']
    name = geodata[0]['name']
    # print(f"[Open Weather Map] Cerco: {name}, {country} [{lat}, {lon}]")

    weather_url = "https://api.openweathermap.org/data/2.5/onecall"
    weather_query = {
        "lon": lon,
        "lat": lat,
        "units": "metric",
        "lang": "it",
        "exclude": "minutely,hourly",
        "appid": API_KEY
    }
    weather = requests.get(weather_url, weather_query)
    data = weather.json()
    try:
        meteo = data['current']
    except KeyError:
        await update.message.reply_text("Errore.")
        return

    air_url = "http://api.openweathermap.org/data/2.5/air_pollution"
    air_query = {
        "lon": lon,
        "lat": lat,
        "appid": API_KEY
    }
    airdata = requests.get(air_url, air_query)
    air = airdata.json()

    H = meteo['humidity']
    T = meteo['temp']

    THOM = T - 0.55 * (1 - (0.01 * H)) * (T - 14.5)
    if THOM <= 21:
        disagio = f"😊 [{round(THOM)}] benessere"
    elif THOM <= 24:
        disagio = f"😐 [{round(THOM)}] leggero disagio"
    elif THOM <= 27:
        disagio = f"🥺 [{round(THOM)}] crescente disagio"
    elif THOM <= 29:
        disagio = f"😵 [{round(THOM)}] disagio"
    elif THOM <= 32:
        disagio = f"🥵 [{round(THOM)}] forte disagio"
    elif THOM > 32:
        disagio = f"☠️ [{round(THOM)}] emergenza medica"
    else:
        disagio = "sconosciuto"

    aqi = air['list'][0]['main']['aqi']
    if aqi == 1:
        aria = f"🟢 [{aqi}] buona"
    elif aqi == 2:
        aria = f"🔵 [{aqi}] moderata"
    elif aqi == 3:
        aria = f"🟡 [{aqi}] leggermente malsana"
    elif aqi == 4:
        aria = f"🟠 [{aqi}] malsana"
    elif aqi == 5:
        aria = f"🔴 [{aqi}] molto malsana"
    elif aqi == 6:
        aria = f"☠️ [{aqi}] pericolosa"
    else:
        aria = "sconosciuta"

    emojis = {
        "01": "☀️",  # sole
        "02": "⛅",  # sole nuvole
        "03": "🌥️",  # nuvole
        "04": "☁️",  # nuvolacce
        "09": "🌧️",  # nuvolacce e pioggia
        "10": "🌦️",  # nuvole pioggia e sole
        "11": "🌩️",  # nuvolacce e fulmini
        "13": "🌨️",  # neve
        "50": "🌫️"  # fog
    }
    uv = meteo['uvi']
    if uv < 3:
        uvi = f"🟩 [{uv}] basso"
    elif uv < 6:
        uvi = f"🟨 [{uv}] medio"
    elif uv < 7:
        uvi = f"🟧 [{uv}] alto"
    elif uv < 11:
        uvi = f"🟥 [{uv}] molto alto"
    elif uv >= 11:
        uvi = f"☠️ [{uv}] estremamente alto"
    else:
        uvi = "sconosciuto"

    meteo_oggi = ""
    meteo_oggi += f"<b>{name}, {country}</b> {'🌞' if meteo['sunrise'] < meteo['dt'] < meteo['sunset'] else '🌜'} {datetime.datetime.utcfromtimestamp(meteo['dt']+data['timezone_offset']).strftime('%H:%M')} del {datetime.datetime.utcfromtimestamp(meteo['dt']+data['timezone_offset']).strftime('%d/%m')}\n"
    meteo_oggi += f"{'🌙' if meteo['weather'][0]['icon'] == '01n' else emojis[meteo['weather'][0]['icon'][:2]]} {str(meteo['weather'][0]['description']).capitalize()}, percepiti {meteo['feels_like']}°C\n\n"
    meteo_oggi += f"Temperatura: {meteo['temp']}°C - Umidità: {meteo['humidity']}%\n"
    meteo_oggi += f"Disagio climatico: {disagio}\n"
    meteo_oggi += f"Qualità dell'aria: {aria}\n"
    meteo_oggi += f"Indice UV: {uvi}"

    await update.message.reply_html(meteo_oggi, disable_web_page_preview=True)


async def meteo_oggi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    citta = ""
    if not context.args:
        if 'default_meteo_city' in context.user_data:
            citta = context.user_data['default_meteo_city']
        else:
            await update.message.reply_html("Inserisci una città.\nSe vuoi impostare una città di default puoi usare <code>-setdefault [città]</code>, ad esempio: <code>/meteo -setdefault Napoli</code>")
            return
    else:
        if context.args[0] == "-setdefault":
            default_city = ' '.join(context.args[1:])
            context.user_data['default_meteo_city'] = default_city
            await update.message.reply_text(f"Salvata: {default_city}")
            return

    API_KEY = config.OWM_API_KEY
    if not citta:
        if len(context.args) == 1:
            citta = context.args[0]
        elif len(context.args) > 1:
            citta = " ".join(context.args)
        else:
            await update.message.reply_text("Devi inserire una città.")
            return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede il meteo semplice di oggi: {citta}')
    await printlog(update, "chiede meteo di oggi", citta)
    geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
    query = {
        "q": citta,
        "appid": API_KEY
    }
    geocoding = requests.get(geocoding_url, query)
    geodata = geocoding.json()

    if not geodata:
        await update.message.reply_text("Nessuna città trovata.")
        return

    lat = geodata[0]['lat']
    lon = geodata[0]['lon']
    country = geodata[0]['country']
    name = geodata[0]['name']
    # print(f"[Open Weather Map] Cerco: {name}, {country} [{lat}, {lon}]")

    weather_url = "https://api.openweathermap.org/data/2.5/onecall"
    weather_query = {
        "lon": lon,
        "lat": lat,
        "units": "metric",
        "lang": "it",
        "exclude": "minutely,hourly",
        "appid": API_KEY
    }
    weather = requests.get(weather_url, weather_query)
    data = weather.json()

    try:
        meteo = data['current']
    except KeyError:
        await update.message.reply_text("Errore.")
        return

    emojis = {
        "01": "☀️",  # sole
        "02": "⛅",  # sole nuvole
        "03": "🌥️",  # nuvole
        "04": "☁️",  # nuvolacce
        "09": "🌧️",  # nuvolacce e pioggia
        "10": "🌦️",  # nuvole pioggia e sole
        "11": "🌩️",  # nuvolacce e fulmini
        "13": "🌨️",  # neve
        "50": "🌫️"  # fog
    }
    meteo_oggi = ""
    meteo_oggi += f"<b>{name}, {country}</b> {'🌞' if meteo['sunrise'] < meteo['dt'] < meteo['sunset'] else '🌜'} {datetime.datetime.utcfromtimestamp(meteo['dt']+data['timezone_offset']).strftime('%H:%M')} del {datetime.datetime.utcfromtimestamp(meteo['dt']+data['timezone_offset']).strftime('%d/%m')}\n"
    meteo_oggi += f"{'🌙' if meteo['weather'][0]['icon'] == '01n' else emojis[meteo['weather'][0]['icon'][:2]]} {str(meteo['weather'][0]['description']).capitalize()}, percepiti {meteo['feels_like']}°C\n"
    meteo_oggi += f"Temperatura: {meteo['temp']}°C - Umidità: {meteo['humidity']}%\n"

    await update.message.reply_html(meteo_oggi, disable_web_page_preview=True)


async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede il forecast metereologico')

    if not context.args:
        await update.message.reply_text("Inserisci una città")
        return
    API_KEY = config.OWM_API_KEY
    citta = " ".join(context.args)

    citta += ",,it"
    geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
    query = {
        "q": citta,
        "appid": API_KEY
    }
    geocoding = requests.get(geocoding_url, query)
    geodata = geocoding.json()

    if not geodata:
        await update.message.reply_text("Nessuna città trovata.")
        return
    await printlog(update, "chiede le previsioni metereologiche", citta)
    lat = geodata[0]['lat']
    lon = geodata[0]['lon']
    country = geodata[0]['country']
    name = geodata[0]['name']

    print(f"[Open Weather Map] Cerco: {name}, {country} [{lat}, {lon}]")

    weather_url = "https://api.openweathermap.org/data/2.5/onecall"
    weather_query = {
        "lon": lon,
        "lat": lat,
        "units": "metric",
        "lang": "it",
        "exclude": "minutely,hourly",
        "appid": API_KEY
    }
    weather = requests.get(weather_url, weather_query)
    data = weather.json()
    giorni = [0, 1, 2, 3]
    emojis = {
        "01d": "☀️",  # sole
        "02d": "⛅",  # sole nuvole
        "03d": "🌥️",  # nuvole
        "04d": "☁️",  # nuvolacce
        "09d": "🌧️",  # nuvolacce e pioggia
        "10d": "🌦️",  # nuvole pioggia e sole
        "11d": "🌩️",  # nuvolacce e fulmini
        "13d": "🌨️",  # neve
        "50d": "🌫️"  # fog
    }
    meteo_oggi = ""
    meteo_oggi += f"Città: {name}, {country}.\n"
    for day in giorni:
        try:
            meteo = data['daily'][day]
        except KeyError:
            data['error']
            await update.message.reply_text("Errore.")
            return
        temp_min = round(meteo['temp']['min'])
        temp_max = round(meteo['temp']['max'])
        icon = meteo['weather'][0]['icon']
        aspetto = f"{emojis[icon]} {meteo['weather'][0]['description']}"
        dt = datetime.datetime.utcfromtimestamp(meteo['dt'] + data['timezone_offset']).strftime('%d/%m')
        meteo_oggi += f"{dt} - {temp_max}/{temp_min}°C - {aspetto}\n"
    await update.message.reply_text(meteo_oggi)
