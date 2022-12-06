import datetime
import config

from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do

from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import CallbackContext, ContextTypes
from rich import print



async def maesta_primo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def feminize(word):
        if word.endswith('o'):
            return word[:-1] + 'a'
        elif word.endswith('e'):
            return word[:-1] + 'a'
        else:
            return word

    if await no_can_do(update, context):
        return
    
    if update.message.chat_id != config.ID_LOTTO:
        return

    if len(update.message.text.split(" ")) != 1:
        return

    word = update.message.text.split(" ")[0].lower()

    titoli = [
        "primo",
        "prima",
        "fastidio",
        "drama",
        "napl",
        "obeso",
        "obesa",
        "terrone",
        "terrona",
        "lgbt",
        "depresso",
        "depressa",
        "sexy",
        "brutto",
        "brutta",
        "sesso",
        "minchia",
        "kebabbaro",
        "kebabbara",
        "sole",
        "ritardo",
        "rosicone",
        "rosicona",
        "coglione",
        "cogliona",
        "merda",
        "bello",
        "bella",
        "godo",
        "scopare"
    ]

    if word not in titoli:
        return

    if word not in ["sesso", "sexy", "lgbt", "napl", "minchia", "sole", "fastidio", "drama", "ritardo", "merda", "godo", "scopare"]: # unisex
        word = feminize(word)

    if "titoli" not in context.chat_data:
        context.chat_data["titoli"] = {}
    if "titoli_holders" not in context.chat_data:
        context.chat_data["titoli_holders"] = {}

    today = datetime.datetime.today().strftime('%Y-%m-%d')

    if today not in context.chat_data["titoli"]:
        context.chat_data["titoli"][today] = {}
    if today not in context.chat_data["titoli_holders"]:
        context.chat_data["titoli_holders"][today] = {}

    if word in context.chat_data["titoli"][today]:
        user = await context.bot.get_chat_member(update.message.chat.id, update.message.from_user.id)
        if context.chat_data['titoli'][today][word] == user.user.full_name:
            await update.message.reply_html(f"Ho un deja-vu, mi sembrava che Sua Maestà {word.capitalize()} fossi già tu!", quote=False)
        else:
            await update.message.reply_html(f"Mi dispiace, ma per oggi Sua Maestà {word.capitalize()} è {context.chat_data['titoli'][today][word]}", quote=False)
        return
    else:
        user = await context.bot.get_chat_member(update.message.chat.id, update.message.from_user.id)
        title_holder = user.user.full_name
        if title_holder in context.chat_data["titoli_holders"][today]:
            title = context.chat_data['titoli_holders'][today][title_holder]
            await update.message.reply_html(f"Sei già Sua Maestà {title.capitalize()}.", quote=False)
            return
        else:
            # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} vuole essere sua maestà {word}')
            await printlog(update, "è sua maesta", word)
            context.chat_data["titoli_holders"][today][title_holder] = word
            context.chat_data["titoli"][today][word] = title_holder
            await update.message.reply_html(f"👑 Per oggi sei <b>Sua Maestà {word.capitalize()}!</b> 👑", quote=False)
            return



async def stat_maesta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from collections import defaultdict, Counter

    if await no_can_do(update, context):
        return
    if update.message.chat_id != config.ID_LOTTO:
        return

    most_title = defaultdict(int)
    most_user = defaultdict(int)

    for day in context.chat_data["titoli"].keys():
        for title in context.chat_data["titoli"][day].keys():
            most_title[title] += 1

    for day in context.chat_data["titoli_holders"].keys():
        for holder in context.chat_data["titoli_holders"][day].keys():
            most_user[holder] += 1

    message = ''
    message += "Classifiche:\n"

    u = Counter(most_user)
    t = Counter(most_title)

    for titolo in t.most_common(3):
        message += f"Sua Maestà {titolo[0].capitalize()}: <code>{titolo[1]}</code>\n"

    message += "\n"

    for utente in u.most_common(3):
        message += f"{utente[0]}: <code>{utente[1]}</code> titoli ricevuti\n"

    await update.message.reply_html(message)

async def elenco_maesta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    
    if update.message.chat_id != config.ID_LOTTO:
        return

    await printlog(update, "chiede l'elenco maestà")
    if "titoli" in context.chat_data:
        today = datetime.datetime.today().strftime('%Y-%m-%d')

        if today in context.chat_data["titoli"]:
            message = ""
            for titolo, utente in context.chat_data['titoli'][today].items():
                message += f"👑 <b>Sua Maestà {titolo.capitalize()}</b>: {utente}\n"
            await update.message.reply_html(message, quote=False)
            return
        else:
            await update.message.reply_text("Nessuna Sua Maestà per oggi.", quote=False)
            return
    else:
        await update.message.reply_text("Nessuna Sua Maestà per oggi.", quote=False)
        return


async def conta_morti(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.chat_member.chat.id not in [config.ID_LOTTO]:
        return
    # import pprint
    # pprint.pprint(update.to_dict())
    try:
        chat_id = update.chat_member.chat.id
    except Exception as e:
        return
    if chat_id not in [config.ID_LOTTO]:
        return

    if update.chat_member.new_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
        print(f"È uscito {update.chat_member.new_chat_member.user.first_name}.")

