import asyncio
import random
from html import unescape

import requests
from rich import print
from telegram import Update
from telegram.constants import PollType
from telegram.ext import ContextTypes

import config
from utils import get_display_name, get_now, no_can_do, printlog


async def make_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "trivia_in_corso" not in context.chat_data:
        context.chat_data["trivia_in_corso"] = False
    if context.chat_data["trivia_in_corso"]:
        return
    if await no_can_do(update, context):
        return

    context.chat_data["trivia_in_corso"] = True
    r = requests.get('https://opentdb.com/api.php?amount=1&type=multiple')
    opentdb = r.json()
    poll_data = opentdb['results'][0]
    domanda = unescape(poll_data['question'])
    risposta_corretta = unescape(poll_data['correct_answer'])
    risposte_html: list= poll_data['incorrect_answers']
    risposte = [unescape(risposta) for risposta in risposte_html]
    risposte.append(risposta_corretta)
    difficuly_time = {
        'easy': 15,
        'medium': 30,
        'hard': 60
    }
    diff = poll_data['difficulty']
    explanation = unescape(f"{poll_data['category']} - {diff}")
    random.shuffle(risposte)
    risp_giusta_index = risposte.index(risposta_corretta)
    
    sent_poll = await context.bot.send_poll(
        chat_id=update.message.chat_id,
        question=domanda,
        options=risposte,
        is_anonymous=False,
        type=PollType.QUIZ,
        explanation = explanation,
        correct_option_id=risp_giusta_index,
        open_period = difficuly_time[poll_data['difficulty']],
    )
    this_poll = [poll_data['difficulty'], risp_giusta_index]

    await printlog(update, "crea un quiz", f"{sent_poll.poll.id} ({poll_data['difficulty']})")

    if 'trivia' not in context.user_data:
        context.bot_data['trivia'] = {}

    context.bot_data['trivia'][sent_poll.poll.id] = this_poll

    await asyncio.sleep(difficuly_time[poll_data['difficulty']])

    if update.message.chat.id == config.ID_LOTTO:
        context.chat_data["trivia_in_corso"] = False
        await asyncio.sleep(15)
        await sent_poll.delete()
    else:
        await update.message.reply_text("Trivia finito.", quote=False)
        context.chat_data["trivia_in_corso"] = False

    return

async def ricevi_risposta_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    poll_id = update.poll_answer.poll_id
    risposta = update.poll_answer.option_ids[0]
    points = {
        'easy': 1,
        'medium': 2,
        'hard': 3
    }

    if poll_id not in context.bot_data['trivia']:
        return
    
    difficulty = context.bot_data['trivia'][poll_id][0]

    if risposta == context.bot_data['trivia'][poll_id][1]:
        if 'trivia_points_new' not in context.user_data:
            context.user_data['trivia_points_new'] = 0

        context.user_data['trivia_points_new'] += points[difficulty]
        print(f'{get_now()} {await get_display_name(update.effective_user)} risponde a {poll_id} ({difficulty}) correttamente! Ora ha {context.user_data["_points_new"]} punti.')

    else:
        if 'trivia_wrongs' not in context.user_data:
            context.user_data['trivia_wrongs'] = 0

        context.user_data['trivia_wrongs'] += 1
        print(f'{get_now()} {await get_display_name(update.effective_user)} risponde a {poll_id} ({difficulty}) ma sbaglia! Ha sbagliato {context.user_data["trivia_wrongs"]} volte.')

async def punteggio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    await printlog(update, "chiede il punteggio nei trivia")

    message = ""

    if 'trivia_points_new' not in context.user_data:
        message += "Hai 0 punti.\n"
    else:
        message += f"Hai {context.user_data['trivia_points_new']} punti.\n"
    if 'trivia_wrongs' not in context.user_data:
        message += "Hai risposto male a 0 quiz.\n"
    else:
        message += f"Hai risposto male a {context.user_data['trivia_wrongs']} quiz."
    await update.message.reply_text(message)

async def classifica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    await printlog(update, "chiede la classifica dei trivia")

    classifica = []

    for user_id, value in context.application.user_data.items():
        if 'trivia_points_new' in value:
            if 'trivia_wrongs' not in value:
                trivia_wrongs = 0
            else:
                trivia_wrongs = value['trivia_wrongs']

            classifica.append((user_id, value['trivia_points_new'], trivia_wrongs))

    classifica.sort(key=lambda x: x[1], reverse=True)
    risposta = ""

    for i, (user_id, points, wrongs) in enumerate(classifica[:10]):
        try:
            user = await context.bot.get_chat(user_id)
            risposta += f"{i+1} · <b>[ {points} ]</b> · {user.full_name} <i>({wrongs})</i>\n"
        except Exception:
            continue
        
    await update.message.reply_html(risposta)
