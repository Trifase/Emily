import cairo
import uuid
import pytz
import math
import random
import miio
import pprint
import requests
import tabulate
import aiohttp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import CallbackContext, ContextTypes
from rich import print
from yeelight import Bulb
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone

import config

from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do, ForgeCommand
from cron_jobs import plot_boiler_stats


def get_bulb(name: str):
    ip_pranzo = "192.168.1.206"
    token_pranzo = "e9466aedeab8b3eecd97ac6f337257fe"

    ip_cucina = "192.168.1.207"
    token_cucina = "33188b32b80cca8eeead7036b4da32da"

    ip_salotto = "192.168.1.150"
    token_salotto = "8b81464003a7a0d4126ea8e6cb8d28e3"

    ip_penisola = "192.168.1.50"

    salotto = miio.Yeelight(ip_salotto, token_salotto)
    pranzo = miio.Yeelight(ip_pranzo, token_pranzo)
    cucina = miio.Yeelight(ip_cucina, token_cucina)
    penisola = Bulb(ip_penisola)

    bulbs = {
        "salotto": {
            "label": "Luce salotto",
            "object": salotto
            },
        "pranzo": {
            "label": "Luce pranzo",
            "object": pranzo
            },
        "cucina": {
            "label": "Luce cucina",
            "object": cucina
            },
        "penisola": {
            "label": "Luce penisola",
            "object": penisola
            }
    }

    if name.lower() not in bulbs.keys():
        return None
    else:
        return bulbs[name.lower()]

def get_status(bulbname):
    if isinstance(bulbname, Bulb):  # Yeelight
        if bulbname.get_properties()['power'] == "on":
            return True
        return False
    elif isinstance(bulbname, miio.Yeelight):  # xiaomi
        if bulbname.get_properties(["power"])[0] == "on":
            return True
        return False
    else:
        raise TypeError

def toggle(bulbname):
    if isinstance(bulbname, Bulb):  # Yeelight
        bulbname.toggle()
    elif isinstance(bulbname, miio.Yeelight):  # xiaomi
        bulbname.toggle()
    else:
        raise TypeError

def get_light_label(bulbname):
    bulbs = ["salotto", "pranzo", "cucina", "penisola"]
    if bulbname not in bulbs:
        return None


    bulb = get_bulb(bulbname)

    if get_status(bulb['object']):
        return f"🟢 {bulb['label']}"
    else:
        return f"🔴 {bulb['label']}"



async def luci_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return
    if update.effective_user.id not in config.ADMINS:
        return

    await printlog(update, "chiede lo status delle luci")

    bulbs = ["salotto", "pranzo", "cucina", "penisola"]

    callbacks = [ForgeCommand(original_update=update, new_text=f"/toggle {x}", new_args=[x], callable=toggle_light) for x in bulbs]

    luci_keyb = [
        [
            InlineKeyboardButton(f"{get_light_label(bulbs[0])}", callback_data=callbacks[0]),
            InlineKeyboardButton(f"{get_light_label(bulbs[1])}", callback_data=callbacks[1]),
        ],
        [
            InlineKeyboardButton(f"{get_light_label(bulbs[2])}", callback_data=callbacks[2]),
            InlineKeyboardButton(f"{get_light_label(bulbs[3])}", callback_data=callbacks[3]),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(luci_keyb)



    await update.message.reply_html(f"Luci:", reply_markup=reply_markup, quote=False)

async def toggle_light(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        if update.effective_user.id not in config.ADMINS:
            return
    except Exception as e:
        if update.from_user.id not in config.ADMINS:
            return

    bulbs = ["salotto", "pranzo", "cucina", "penisola"]

    if not context.args or context.args[0] not in bulbs:
        return

    await printlog(update, "toggla una luce", context.args[0])

    toggle(get_bulb(context.args[0])['object'])
    if update.message.reply_markup:

        bulbs = ["salotto", "pranzo", "cucina", "penisola"]

        callbacks = [ForgeCommand(original_update=update, new_text=f"/toggle {x}", new_args=[x], callable=toggle_light) for x in bulbs]

        luci_keyb = [
            [
                InlineKeyboardButton(f"{get_light_label(bulbs[0])}", callback_data=callbacks[0]),
                InlineKeyboardButton(f"{get_light_label(bulbs[1])}", callback_data=callbacks[1]),
            ],
            [
                InlineKeyboardButton(f"{get_light_label(bulbs[2])}", callback_data=callbacks[2]),
                InlineKeyboardButton(f"{get_light_label(bulbs[3])}", callback_data=callbacks[3]),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(luci_keyb)


        await update.message.edit_reply_markup(reply_markup=reply_markup)

    return

async def consumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMINS:
            return

    await printlog(update, "controlla il consumo")

    async with aiohttp.ClientSession() as session:
        async with session.get("http://192.168.1.245/emeter/0") as response:
            data = await response.json()

            await update.message.reply_html(f"Consumo istantaneo: {data['power']} W")


async def purificatore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMINS:
            return
    await printlog(update, "chiede lo status del purificatore d'aria")
    import miio
    air = miio.AirPurifierMiot("192.168.1.84", "e8e5a8bb036e21662c4708b61a829c04") # 54:48:E6:55:B3:72
    s = air.status()
    message = ""
    message += f"Purificatore d'aria Xiaomi Air Purifier 3H: {'Acceso' if s.is_on else 'Spento'}\n"
    message += f"Temperatura: {s.temperature}°C - Umidità: {s.humidity}% - AQI: {s.aqi}\n"
    message += f"Ore d'uso: {s.filter_hours_used}h - Aria purificati: {s.purify_volume} m³ - Filtro rimanente: {s.filter_life_remaining}%\n"
    await update.message.reply_html(message)

async def riscaldamento_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMINS:
        return
    if '-new' in context.args:
        await plot_boiler_stats(context)
        await printlog(update, "genera un nuovo grafico della caldaia")
    await update.message.reply_photo(open('images/boiler48h.jpg', 'rb'))


