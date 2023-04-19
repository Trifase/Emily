import requests

from rich import print
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.error import BadRequest

import config
from utils import printlog, no_can_do


# Maps

async def streetview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede streetview BETA')
    await printlog(update, "chiede streetview")

    if not context.args:
        await update.message.reply_text("Inserisci un posto")
        return
    heading = ""
    if context.args[0].startswith("-h"):
        heading = context.args[0][2:]
        context.args[0] = ""

    address = " ".join(context.args)
    geo_query = {
        "address": address,
        "language": "it",
        "region": "it",
        "key": config.GMAP_API_KEY
    }
    geo_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    location = requests.get(geo_url, geo_query).json()

    try:
        location_name = location['results'][0]['formatted_address']
        import string
        for char in string.punctuation:
            location_name = location_name.replace(char, '')
        loc_lat = location['results'][0]['geometry']['location']['lat']
        loc_lon = location['results'][0]['geometry']['location']['lng']
    except IndexError:
        await update.message.reply_text("Non trovo un cazzo")
        return
    print(f"{location_name[:20]};{loc_lat};{loc_lon};315")
    # Inline Keyboard
    keyboard = [
        [
            InlineKeyboardButton("↖️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};315"),
            InlineKeyboardButton("⬆️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};0"),
            InlineKeyboardButton("↗️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};45"),
        ],
        [
            InlineKeyboardButton("⬅️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};270"),
            InlineKeyboardButton("➡️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};90"),
        ],
        [
            InlineKeyboardButton("↙️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};225"),
            InlineKeyboardButton("⬇️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};180"),
            InlineKeyboardButton("↘️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};135"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Google maps
    map_query = {
        "location": f"{loc_lat},{loc_lon}",
        "size": "640x640",
        "heading": heading,
        "fov": 100,
        "pitch": 0,
        "key": config.GMAP_API_KEY
    }

    map_url = 'https://maps.googleapis.com/maps/api/streetview'
    r = requests.get(map_url, map_query)
    open('images/map.jpg', 'wb').write(r.content)
    await update.message.reply_photo(open('images/map.jpg', 'rb'), quote=False, caption=location_name, reply_markup=reply_markup)

async def maps_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id in context.bot_data['global_bans']:
        return
    """Parses the CallbackQuery and updates the message text."""
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query = update.callback_query
    await query.answer()

    argomenti = query.data
    commands = argomenti.split("_")[1].split(";")

    location_name = commands[0]
    loc_lat = commands[1]
    loc_lon = commands[2]
    heading = commands[3]

    # Inline Keyboard
    keyboard = [
        [
            InlineKeyboardButton("↖️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};315"),
            InlineKeyboardButton("⬆️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};0"),
            InlineKeyboardButton("↗️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};45"),
        ],
        [
            InlineKeyboardButton("⬅️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};270"),
            InlineKeyboardButton("➡️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};90"),
        ],
        [
            InlineKeyboardButton("↙️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};225"),
            InlineKeyboardButton("⬇️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};180"),
            InlineKeyboardButton("↘️", callback_data=f"m_{location_name[:20]};{loc_lat};{loc_lon};135"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Google maps
    map_query = {
        "location": f"{loc_lat},{loc_lon}",
        "size": "640x640",
        "heading": heading,
        "fov": 100,
        "pitch": 0,
        "key": config.GMAP_API_KEY
    }

    map_url = 'http://maps.googleapis.com/maps/api/streetview'
    r = requests.get(map_url, map_query)
    open('images/new_map.jpg', 'wb').write(r.content)

    try:
        await query.edit_message_media(media=InputMediaPhoto(open('images/new_map.jpg', 'rb'), caption=location_name), reply_markup=reply_markup)    
    except BadRequest:
        pass

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede una mappa')
    await printlog(update, "chiede una location")

    if not context.args:
        await update.message.reply_text("Inserisci una città")
        return

    address = " ".join(context.args)
    geo_query = {
        "address": address,
        "language": "it",
        "region": "it",
        "key": config.GMAP_API_KEY
    }
    geo_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    location = requests.get(geo_url, geo_query).json()

    try:
        location_name = location['results'][0]['formatted_address']
        loc_lat = location['results'][0]['geometry']['location']['lat']
        loc_lon = location['results'][0]['geometry']['location']['lng']
    except IndexError:
        await update.message.reply_text("Non trovo un cazzo")
        return
    # Google maps
    map_query = {
        "center": f"{loc_lat},{loc_lon}",
        "zoom": 6,
        "size": "1200x1200",
        "scale": 2,
        "maptype": "hybrid",
        "markers": f"color:red|{loc_lat},{loc_lon}",
        "key": config.GMAP_API_KEY
    }

    map_url = 'https://maps.googleapis.com/maps/api/staticmap'
    r = requests.get(map_url, map_query)
    open('images/map.jpg', 'wb').write(r.content)
    await update.message.reply_photo(open('images/map.jpg', 'rb'), quote=False, caption=location_name)
    await context.bot.send_location(update.message.chat.id, loc_lat, loc_lon)
