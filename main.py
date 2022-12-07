import warnings
warnings.filterwarnings("ignore")
import locale
import pytz
import peewee
import re
import time
import datetime
import json
import instaloader
import platform

from rich import print
from aiohttp import web

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import __version__ as TG_VER
from telegram.constants import ParseMode
from telegram.ext import Application, ApplicationBuilder, CommandHandler, PicklePersistence, MessageHandler, filters, CallbackQueryHandler, Defaults, CallbackContext, ContextTypes, PollAnswerHandler, InlineQueryHandler, ChatMemberHandler, AIORateLimiter, PreCheckoutQueryHandler

import config

from utils import printlog, get_now, no_can_do, is_member_in_group

from admin import (cancella, commandlist, count_lines, echo, esci, executecode,
    getchat, ip, lista_chat, listen_to, restart, _eval, set_group_picture,
    set_title, tg_info, wakeup, banlist, add_ban, del_ban, trigger_backup, parla,
    track_chats, show_chats, send_custom_media, check_temp, flush_arbitrary_callback_data)
from asphalto import azzurro, lurkers
from banca import bot_get_saldo, bot_get_transazioni
from best_timeline import scrape_tweet_bt, silenzia, deleta_if_channel, aoc_leaderboard
from compleanni import compleanni_add, compleanni_list, compleanni_manual_check, compleanno_del
from cron_jobs import check_reminders, check_compleanni, lotto_member_count, do_global_backup, plot_boiler_stats
from diochan import save_tensor, random_tensor, search_quote, add_quote, diochan, mon, ascendi
from donazioni import donazioni, precheckout_callback, successful_payment_callback
from games import sassocartaforbici
from gpt3 import ai
from lotto import maesta_primo, elenco_maesta, stat_maesta
from macros import ispirami, change_my_mind
from maps import streetview, location, maps_buttons
from meteo import meteo_oggi, ora, prometeo_oggi, forecast
from movies import doveguardo, imdb, doveguardo_buttons
from misc import (bioritmo, fascio, fatfingers, scacchi, square, traduci, spongebob, voice, alexa, get_user_info,
    set_auto_reaction, send_auto_reaction, bomb_react, start, polls_callbackqueryhandlers, condominioweb, is_safe,
    greet_BT_user, random_trifase)
from pyrog import reaction_karma
from quiz import classifica, make_poll, ricevi_risposta_quiz, punteggio
from reddit import reddit
from reminders import remindelete, reminder_helper, reminders_list, remindme, send_reminder
from scrapers import (tiktok, tiktok_long, new_instagram, instagram_stories,
    youtube_alts, ninofrassica, wikipedia, tiktok_inline, facebook_video, scrape_tweet_media,
    parse_reddit_link, twitch_clips)
from sets import addset, deleteset, jukebox, listaset
from smarthome import luci_status, toggle_light, get_light_label, consumo, purificatore, riscaldamento_stats
from space import solarsystem, launches
from tarots import tarot, oroscopo, tarotschema
from testing import test, getfile
from torrent import lista_torrent
from twitter import lista_tweets, tweet
from utils import is_user, is_inline_button

def main():

    defaults = Defaults(
        parse_mode=ParseMode.HTML,
        tzinfo=pytz.timezone('Europe/Rome'),
        block=False,
        allow_sending_without_reply=True
        )

    builder = ApplicationBuilder()
    builder.token(config.BOT_TOKEN)
    builder.persistence(PicklePersistence(filepath='db/picklepersistence'))
    builder.arbitrary_callback_data(True)
    builder.rate_limiter(AIORateLimiter())
    builder.defaults(defaults)
    builder.read_timeout(30.0)
    builder.connect_timeout(30.0)
    builder.write_timeout(30.0)
    builder.pool_timeout(5.0)
    builder.post_init(post_init)
    builder.post_shutdown(post_shutdown)

    app = builder.build()

    # cron_jobs.py
    j = app.job_queue

    # j.run_repeating(check_reminders, interval=30.0, data=None, job_kwargs={'misfire_grace_time': 25})
    j.run_repeating(plot_boiler_stats, interval=2600.0, data=None, job_kwargs={'misfire_grace_time': 25})

    # j.run_repeating(lotto_member_count, interval=300.0, data=None, job_kwargs={'misfire_grace_time': 25})

    j.run_daily(lotto_member_count, datetime.time(hour=9, minute=0, tzinfo=pytz.timezone('Europe/Rome')), data=None)

    j.run_daily(check_compleanni, datetime.time(hour=0, minute=0, tzinfo=pytz.timezone('Europe/Rome')), data=None)
    j.run_daily(check_compleanni, datetime.time(hour=12, minute=00, tzinfo=pytz.timezone('Europe/Rome')), data=None)
    j.run_daily(check_compleanni, datetime.time(hour=20, minute=00, tzinfo=pytz.timezone('Europe/Rome')), data=None)

    j.run_daily(do_global_backup, datetime.time(hour=2, minute=00, tzinfo=pytz.timezone('Europe/Rome')), data=None)

    # main.py
    app.add_handler(CallbackQueryHandler(admin_buttons, pattern=r'^cmd:'))
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, parse_everything), 21)


    # Error handler
    # app.add_error_handler(error_handler)

    # admin.py
    # app.add_handler(CommandHandler('backup', do_manual_backup, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['checktemp', 'check_temp', 'temp', 'temperatura'], check_temp, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('flush_arbitrary_callback_data', flush_arbitrary_callback_data))
    app.add_handler(CommandHandler(['parla', 'say'], parla, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('restart', restart, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('print', _eval, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['commandlist','lista_comandi', 'commands'], commandlist, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['del','cancella', 'delete'], cancella, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('sloc', count_lines, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('exec', executecode, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['ripeti','say', 'echo'], echo, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('info', tg_info, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['getchat', 'get_chat'], getchat, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['chatlist', 'listachat', 'lista_chat'], lista_chat, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['listen_to', 'listen'], listen_to, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('esci', esci, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['ip', 'myip'], ip, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('wakeup', wakeup, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['listaban', 'ban_list', 'banlist'], banlist, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['addban', 'ban', 'add_ban'], add_ban, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['delban', 'del_ban'], del_ban, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['set_title', 'settitle', 'title'], set_title, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['set_propic', 'setpicture', 'propic'], set_group_picture, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('backup', trigger_backup, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler("show_chats", show_chats), 48)
    app.add_handler(CommandHandler(['send_media', 'send_custom_media', 'send'], send_custom_media, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))

    app.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER), 44)

    # asphalto.py
    app.add_handler(CommandHandler(['azzurro', 'azz'], azzurro, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('lurkers', lurkers, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))

    # banca.py
    app.add_handler(CommandHandler(['saldo', 'carige_saldo'], bot_get_saldo, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['movimenti', 'transazioni', 'carige_movimenti'], bot_get_transazioni, filters=~filters.UpdateType.EDITED))

    # best_timeline.py
    app.add_handler(MessageHandler(
        ~filters.UpdateType.EDITED & 
        filters.Regex(re.compile(r"(?:(?:http|https):\/\/)?(?:www.|mobile.)?(?:twitter.com)\/(?:\w+)\/status\/(\w+)", re.IGNORECASE)), scrape_tweet_bt
        ), group=929)
    app.add_handler(CommandHandler(['silenzia', 'silenzio', 'taci', 'shhh'], silenzia, filters=~filters.UpdateType.EDITED))
    app.add_handler(MessageHandler(filters.SenderChat.CHANNEL, deleta_if_channel), -99)
    app.add_handler(CommandHandler(['aoc', 'leaderboard'], aoc_leaderboard, filters=~filters.UpdateType.EDITED))

    # compleanni.py
    app.add_handler(CommandHandler(['compleanno', 'addcompleanno'], compleanni_add, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['compleanni', 'listacompleanni'], compleanni_list, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['cancellacompleanno', 'delcompleanno'], compleanno_del, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('compleanni_check', compleanni_manual_check, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))

    # diochan.py
    app.add_handler(CommandHandler('quote', search_quote, filters=~filters.UpdateType.EDITED & filters.Chat(config.ID_DIOCHAN)))
    app.add_handler(CommandHandler('addquote', add_quote, filters=~filters.UpdateType.EDITED & filters.Chat(config.ID_DIOCHAN)))
    app.add_handler(CommandHandler('ascendi', ascendi, filters=~filters.UpdateType.EDITED & filters.Chat(config.ID_DIOCHAN)))
    app.add_handler(CommandHandler('diochan', diochan, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['tensor', 'tensorbot'], random_tensor, filters=~filters.UpdateType.EDITED))
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & filters.TEXT & filters.User(username="@Tensor1987"), save_tensor), 19)
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r'\bmon\b', re.IGNORECASE)), mon), 25)

    # donazioni.py
    app.add_handler(CommandHandler("donazione", donazioni))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    # games.py
    app.add_handler(CommandHandler(['sassocartaforbici', 'scf', 'morracinese', 'morra'], sassocartaforbici))

    # gpt3.py
    app.add_handler(CommandHandler("ai", ai))
    # app.add_handler(CommandHandler("tarocchi", ai_tarocchi))

    # lotto.py
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT & filters.Chat(config.ID_LOTTO), maesta_primo), 15)
    app.add_handler(CommandHandler("maesta", elenco_maesta))
    app.add_handler(CommandHandler(["stats_maesta", 'maesta_stats', 'maestats', 'maestat'], stat_maesta))
    # app.add_handler(ChatMemberHandler(conta_morti, ChatMemberHandler.ANY_CHAT_MEMBER), 18)
    

    # macros.py
    app.add_handler(CommandHandler('ispirami', ispirami, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['changemymind', 'change'], change_my_mind, filters=~filters.UpdateType.EDITED))

    # maps.py
    app.add_handler(CommandHandler(['loc', 'localize', 'location', 'dove'], location, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['sw', 'street', 'streetview'], streetview, filters=~filters.UpdateType.EDITED))
    app.add_handler(CallbackQueryHandler(maps_buttons, pattern=r'^m_'))

    # meteo.py
    app.add_handler(CommandHandler('ora', ora, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('prometeo', prometeo_oggi, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('meteo', meteo_oggi, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['forecast', 'previsioni'], forecast, filters=~filters.UpdateType.EDITED))

    # misc.py
    # app.add_handler(CommandHandler('chiedi_opinione', chiedi_opinione))
    app.add_handler(CommandHandler(['trifase', 'randomtrif', 'randomtrifase'], random_trifase, filters=~filters.UpdateType.EDITED))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_BT_user))
    app.add_handler(CallbackQueryHandler(polls_callbackqueryhandlers, pattern=is_inline_button), -999)
    # Disabled because tensorflow doesn't support python 3.11 yet
    # app.add_handler(CommandHandler('is_safe', is_safe, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('condominioweb', condominioweb, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['start'], start, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler(['bioritmo', 'bio', 'biorhythm'], bioritmo, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('traduci', traduci, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('get_user_info', get_user_info, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('spongebob', spongebob, filters=~filters.UpdateType.EDITED))
    # app.add_handler(CommandHandler('help', call_help, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('square', square, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('fascio', fascio, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['lichess', 'lichness'], scacchi, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('voice', voice, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['fatfinger', 'fatfingers'], fatfingers, filters=~filters.UpdateType.EDITED))
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r"[Aa]lexa (?:[Pp]lay|[Rr]iproduci) (.+)", re.IGNORECASE)), alexa))
    app.add_handler(CommandHandler('autoreaction', set_auto_reaction, filters=~filters.UpdateType.EDITED))
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL, send_auto_reaction), 291)
    app.add_handler(CommandHandler('bombreact', bomb_react, filters=~filters.UpdateType.EDITED))

    # movies.py
    app.add_handler(CommandHandler(['doveguardo', 'dove_guardo'], doveguardo, filters=~filters.UpdateType.EDITED))
    app.add_handler(CallbackQueryHandler(doveguardo_buttons, pattern=r'^dvg_'))
    app.add_handler(CommandHandler(['imdb', 'torrent'], imdb, filters=~filters.UpdateType.EDITED))

    # pyrog.py
    app.add_handler(CommandHandler(['karma', 'reactionlist', 'reactkarma'], reaction_karma, filters=~filters.UpdateType.EDITED))

    # quiz.py
    app.add_handler(CommandHandler('trivia', make_poll, filters=~filters.UpdateType.EDITED))
    app.add_handler(PollAnswerHandler(ricevi_risposta_quiz))
    app.add_handler(CommandHandler('punteggio', punteggio, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('classifica', classifica, filters=~filters.UpdateType.EDITED))

    # reddit.py
    app.add_handler(CommandHandler(['redd', 'reddit'], reddit, filters=~filters.UpdateType.EDITED))

    # reminders.py
    app.add_handler(CommandHandler(['reminder', 'remindhelp'], reminder_helper, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['remindme', 'remind'], remindme, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['reminderlist', 'remindlist', 'listareminder', 'reminder_list'], reminders_list, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['reminder_delete', 'remindelete', 'deletereminder'], remindelete, filters=~filters.UpdateType.EDITED))

    # scrapers.py
    app.add_handler(CommandHandler(["wikipedia", "wiki"], wikipedia, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('ninofrassica', ninofrassica, filters=~filters.UpdateType.EDITED))
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r"(\b\S+(:?instagram\.com|instagr\.am)\S+\b)",  re.IGNORECASE)), new_instagram))
    app.add_handler(CommandHandler(["stories", "storie"], instagram_stories, filters=~filters.UpdateType.EDITED))
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r"(?:https?://vm.tiktok.com\/(\w+))", re.IGNORECASE)), tiktok))
    app.add_handler(MessageHandler(
        ~filters.UpdateType.EDITED & 
        filters.Regex(re.compile(r"(?:(?:http|https):\/\/)?(?:www.)?(?:tiktok.com)\/(@[a-zA-Z0-9_.]+)\/video\/(\w+)", re.IGNORECASE)), tiktok_long
        ))
    app.add_handler(MessageHandler(
        ~filters.UpdateType.EDITED & 
        filters.Regex(re.compile(r"(?:(?:http|https):\/\/)?(?:www.|mobile.)?(?:twitter.com)\/(?:\w+)\/status\/(\w+)", re.IGNORECASE)), scrape_tweet_media
        ), group=920)
    app.add_handler(MessageHandler(
        ~filters.UpdateType.EDITED & 
        filters.Regex(re.compile(r"(?:(?:http:\/\/)?|(?:https:\/\/)?)?(?:yewtu.be|utew.be)\/(?:watch\?v=)?([a-zA-Z0-9_-]{6,11})", re.IGNORECASE)), youtube_alts
        ))
    app.add_handler(InlineQueryHandler(tiktok_inline))
    app.add_handler(MessageHandler(
        ~filters.UpdateType.EDITED & 
        filters.Regex(re.compile(r"(?:(?:http|https):\/\/)?(?:www\.|fb\.watch)\/([^\/]{10})", re.IGNORECASE)), facebook_video
        ))
    app.add_handler(MessageHandler(
        ~filters.UpdateType.EDITED & 
        filters.Regex(re.compile(r"(?:(?:http|https):\/\/)?(?:www.|fb.|m.)?(?:watch|facebook.com)\/watch(?:\/)?\?v=[0-9]+", re.IGNORECASE)), facebook_video
        ))
    app.add_handler(MessageHandler(
        ~filters.UpdateType.EDITED & 
        filters.Regex(re.compile(r"(?:(?:http|https):\/\/)?(?:www.|fb.|m.)?(?:watch|facebook.com)(?:\/[\w.]+)(?:\/videos|\/watch)\/([\w.]+)", re.IGNORECASE)), facebook_video
        ))
    app.add_handler(MessageHandler(
        ~filters.UpdateType.EDITED & 
        filters.Regex(re.compile(r"^http(?:s)?://(?:www\.)?(?:[\w-]+?\.)?reddit\.com(/r/|/user/)?(?(1)([\w:]{2,21}))(/comments/)?(?(3)(\w{5,6})(?:/[\w%\\\\-]+)?)?(?(4)/(\w{7}))?/?(\?)?(?(6)(\S+))?(\#)?(?(8)(\S+))?$", re.IGNORECASE)), parse_reddit_link
        ))
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r"(?:https:\/\/)?clips\.twitch\.tv\/(\S+)", re.IGNORECASE)), twitch_clips))

    # 
    # sets.py
    app.add_handler(CommandHandler(['set', 'addset'], addset, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['listaset', 'setlist'], listaset, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['deleteset', 'delset'], deleteset, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['jukebox', 'audio'], jukebox, filters=~filters.UpdateType.EDITED))

    # smarthome.py
    app.add_handler(CommandHandler(['status_luci', 'statusluci', 'luci', 'luci_status'], luci_status, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['toggle', 'luce', 'toggla'], toggle_light, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['consumo'], consumo, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['purificatore', 'purifier'], purificatore, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['riscaldamento', 'boiler', 'caldaia'], riscaldamento_stats, filters=~filters.UpdateType.EDITED))
    


    # space.py
    app.add_handler(CommandHandler(['stars', 'solarsystem', 'stelle'], solarsystem, filters=~filters.UpdateType.EDITED, block=True))
    app.add_handler(CommandHandler(['lanci', 'launches'], launches, filters=~filters.UpdateType.EDITED, block=True))


    # tarots.py
    app.add_handler(CommandHandler(['tarot', 'tarots', 'tarocchi'], tarot, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['oroscopo', 'horoscope', 'oro'], oroscopo, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['tarotschema', 'reversetarots', 'schema'], tarotschema, filters=~filters.UpdateType.EDITED))
    

    # testing.py
    app.add_handler(CommandHandler('test', test, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('getfile', getfile, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    
    # torrent.py
    app.add_handler(CommandHandler(['torrents', 'torrentlist', 'listatorrent', 'lista_torrent'], lista_torrent, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))

    # twitter.py
    app.add_handler(CommandHandler(['tw', 'tweet'], tweet, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['tweetlists', 'listatweet', 'tweets', 'twlist'], lista_tweets, filters=~filters.UpdateType.EDITED))

    # app.add_handler(MessageHandler(
    #     ~filters.UpdateType.EDITED & 
    #     filters.Regex(
    #         re.compile(
    #             r"(?:(?:http|https):\/\/)?(?:www.)?(?:instagram.com|instagr.am|instagr.com)\/(?:p|reel)\/([^\/]{11})",
    #             re.IGNORECASE
    #             )
    #         ),
    #         instagram_post
    #     ))
    # app.add_handler(MessageHandler(
    #     ~filters.UpdateType.EDITED & 
    #     filters.Regex(re.compile(r"(?:(?:http|https):\/\/)?(?:www.)?(?:instagram.com|instagr.am|instagr.com)\/(stories|s)\/([\w.]+)(\/([\w.]+))?", re.IGNORECASE)), instagram_story
    #     ))
    # app.add_handler(MessageHandler(
    #     ~filters.UpdateType.EDITED & 
    #     filters.Regex(re.compile(r"(?:(?:http|https):\/\/)?(?:www.)?(?:\binstagram.com|instagr.am|instagr.com)\/(?!stories\/)(?!p\/)(?!tv\/)(?!s\/)(?!reel\/)([^\/\n?]+)", re.IGNORECASE)), instagram_profile
    #     ))
    # app.add_handler(MessageHandler(
    #     ~filters.UpdateType.EDITED & 
    #     filters.Regex(re.compile(r"(?:(?:http|https):\/\/)?(?:www.)?(?:instagram.com|instagr.am|instagr.com)\/tv\/([^\/]*)", re.IGNORECASE)), instagram_tv
    #     ))


    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

# All Messages
async def parse_everything(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    chat_id = int(update.effective_chat.id)

    SPY = True


    # Auto exit on banned groups
    if chat_id in config.BANNED_GROUPS:
        await context.bot.leave_chat(chat_id)

    if 'lista_chat' not in context.bot_data:
        context.bot_data['lista_chat'] = []
    if "listen_to" not in context.bot_data:
        context.bot_data['listen_to'] = []

    # Se è nella lista spiati, inoltra il messaggio su emily spia
    if chat_id in context.bot_data['listen_to']:
        my_chat = await context.bot.get_chat(chat_id)
        msg_from = "👤 chat privata"
        if my_chat.title:
            msg_from = f"💬 {my_chat.title}"
        text = f"[SPIO] Messaggio su {msg_from}:\nID: <code>{my_chat.id}</code>\n{update.effective_user.mention_html()}: {update.effective_message.text}"
        # Inline Keyboard
        keyboard = [
            [
                InlineKeyboardButton(f"{'Spia' if chat_id not in context.bot_data['listen_to'] else 'Non spiare'}", callback_data=f"cmd:listen_to:{chat_id}"),
                InlineKeyboardButton("Banna", callback_data=f"cmd:ban:{chat_id}"),
                InlineKeyboardButton("Info", callback_data=f"cmd:getchat:{chat_id}"),
                InlineKeyboardButton("Del chatlist", callback_data=f"cmd:listachat:-delete {chat_id}"),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=config.ID_SPIA, text=text, reply_markup=reply_markup)

    # if 'lista_chat' not in context.bot_data:
    #     context.bot_data['lista_chat'] = {}


    if chat_id not in context.bot_data['lista_chat']:
        context.bot_data['lista_chat'].append(chat_id)
        is_presente = await is_member_in_group(config.ID_TRIF, chat_id, context)
        if chat_id < 0 and chat_id not in context.bot_data['listen_to'] and SPY:

            
            if not is_presente:
                context.bot_data['listen_to'].append(chat_id)
                # await context.bot.send_message(chat_id=config.ID_SPIA, text=f"Spio: {chat_id}")
            else:
                # await context.bot.send_message(chat_id=config.ID_SPIA, text=f"Non spio {chat_id} - gruppo in comune.")
                pass
                
        elif chat_id not in context.bot_data['listen_to'] and SPY:
            context.bot_data['listen_to'].append(chat_id)
            # await context.bot.send_message(chat_id=config.ID_SPIA, text=f"Spio: {chat_id}")

        if not await is_user(update):
            
            message = ""
            mychat = await context.bot.get_chat(chat_id)
            utenti = await context.bot.get_chat_member_count(chat_id)
            if chat_id in context.bot_data['listen_to']:
                message += "Nuova chat di gruppo rilevata! (Spio)\n\n"
            else:
                message += "Nuova chat di gruppo rilevata! (Non spio)\n\n"
            message += f"<b>Nome: {mychat.title}</b>\n"
            message += f"ID: <code>{mychat.id}</code>\n"
            message += f"Tipo: {mychat.type}\n"
            message += f"Utenti: {utenti}\n"
            message += f"Invite Link: {mychat.invite_link}\n"
            message += f"Descrizione:\n{mychat.description}\n\n"
            # try:
            #     presente = await context.bot.get_chat_member(int(chat_id), config.ID_TRIF)
            #     message += f"Sei presente in questa chat\n"
            # except Exception as e:
            #     message += f"Non sei presente in questa chat\n"

            message += f"Messaggio: {update.effective_user.mention_html()}: {update.effective_message.text}"

        else:
            message = ""
            utente = await context.bot.get_chat(chat_id)
            if chat_id in context.bot_data['listen_to']:
                message += "Nuova chat utente rilevata! (Spio)\n\n"
            else:
                message += "Nuova chat utente rilevata! (Non spio)\n\n"
            message += f"Nome: {utente.first_name} {utente.last_name}\n"
            message += f"Nickname: @{utente.username}\n"
            message += f"ID: <code>{utente.id}</code>\n"
            message += f"Bio: {utente.bio}\n\n"
            message += f"Messaggio: {update.effective_user.mention_html()}: {update.effective_message.text}"

        # Inline Keyboard
        keyboard = [
            [
                InlineKeyboardButton(f"{'Spia' if chat_id not in context.bot_data['listen_to'] else 'Non spiare'}", callback_data=f"cmd:listen_to:{chat_id}"),
                InlineKeyboardButton("Banna", callback_data=f"cmd:ban:{chat_id}"),
                InlineKeyboardButton("Info", callback_data=f"cmd:getchat:{chat_id}"),
                InlineKeyboardButton("Del chatlist", callback_data=f"cmd:listachat:-delete {chat_id}"),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(config.ID_SPIA, message, reply_markup=reply_markup)

    # Timestamp per asphalto
    if chat_id == config.ID_ASPHALTO:
        if 'timestamps' not in context.bot_data:
            context.bot_data['timestamps'] = {}
        if chat_id not in context.bot_data['timestamps']:
            context.bot_data['timestamps'][chat_id] = {}

        if update.effective_user:
            user_id = int(update.effective_user.id)
            context.bot_data['timestamps'][chat_id][user_id] = int(time.time())

    # Da qui in poi, i messaggi privati vengono ignorati.
    if update.message.chat.type == "private":
        return

    # Sets
    with open('db/sets.json') as sets_db:
        sets = json.load(sets_db)

    chat_id = str(update.message.chat.id)
    messaggio = update.effective_message.text

    if chat_id not in sets:
        sets[chat_id] = {}
    chatdict = sets[chat_id]
    if messaggio.lower().endswith('@emilia_superbot'):
        messaggio = messaggio[:-16]

    if messaggio.lower() in chatdict:
        # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} triggera {messaggio}')
        await printlog(update, "triggera", messaggio)
        set_text: str = chatdict[messaggio.lower()]
        is_reply = False
        if update.message.reply_to_message:
            is_reply = True
            reply_id = update.message.reply_to_message.message_id
        if set_text.startswith('media:'):  # 'media:media_type:media_id'
            media_type = set_text.split(':')[1]
            media_id = set_text.split(':')[2]
            try:
                if media_type == "photo":
                    if is_reply:
                        await context.bot.send_photo(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_photo(chat_id, media_id)
                elif media_type == "video":
                    if is_reply:
                        await context.bot.send_video(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_video(chat_id, media_id)
                elif media_type == "sticker":
                    if is_reply:
                        await context.bot.send_sticker(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_sticker(chat_id, media_id)
                elif media_type == "audio":
                    if is_reply:
                        await context.bot.send_audio(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_audio(chat_id, media_id)
                elif media_type == "voice":
                    if is_reply:
                        await context.bot.send_voice(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_voice(chat_id, media_id)
                elif media_type == "document":
                    if is_reply:
                        await context.bot.send_document(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_document(chat_id, media_id)
                elif media_type == "animation":
                    if is_reply:
                        await context.bot.send_animation(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_animation(chat_id, media_id)
                elif media_type == "video_note":
                    if is_reply:
                        await context.bot.send_video_note(chat_id, media_id, reply_to_message_id=reply_id)
                    else:
                        await context.bot.send_video_note(chat_id, media_id)
                else:
                    await update.message.reply_text("Tipo di media non riconosciuto")
                return
            except Exception as e:
                await update.message.reply_html(f'<b>Errore:</b> {e}')
                return
        else:
            if is_reply:
                await update.message.reply_text(f'{chatdict[messaggio.lower()]}', quote=False, disable_web_page_preview=True, reply_to_message_id=reply_id)
            else:
                await update.message.reply_text(f'{chatdict[messaggio.lower()]}', quote=False, disable_web_page_preview=True)
            return

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    query = update.callback_query
    await query.answer()

    # Example of update.callback_query.data it receives:
    # cmd:ban:123456789

    # splitting the string into command and args
    command = query.data.split(":")[1]
    args = query.data.split(":")[2]

    # forging a fake message.text
    query.message.text = f"/{command} {args}"

    # creating an empty context.args
    if not context.args:
        context.args = []

    # forging a fake context.args
    for arg in args.split(" "):
        context.args.append(arg)

    # calling actual functions with the forged callback_query and forged context
    # add_ban is the same function that would be called by /add_ban <user_id>
    if command == 'ban':
        await add_ban(update.callback_query, context)
    elif command == 'getchat':
        await getchat(update.callback_query, context)
    elif command == 'listen_to':
        await listen_to(update.callback_query, context)
    elif command == 'listachat':
        await lista_chat(update.callback_query, context)
        
    elif command == 'toggle':
        if query.from_user.id not in config.ADMINS:
            await query.answer(f"Non puoi.")
            return

        await toggle_light(update.callback_query, context)
        bulbs = ["salotto", "pranzo", "cucina", "penisola"]

        luci_keyb = [
            [
                InlineKeyboardButton(f"{get_light_label(bulbs[0])}", callback_data=f"cmd:toggle:{bulbs[0]}"),
                InlineKeyboardButton(f"{get_light_label(bulbs[1])}", callback_data=f"cmd:toggle:{bulbs[1]}"),
            ],
            [
                InlineKeyboardButton(f"{get_light_label(bulbs[2])}", callback_data=f"cmd:toggle:{bulbs[2]}"),
                InlineKeyboardButton(f"{get_light_label(bulbs[3])}", callback_data=f"cmd:toggle:{bulbs[3]}"),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(luci_keyb)
        await query.message.edit_text("Luci:", reply_markup=reply_markup)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    from rich.console import Console
    from rich.traceback import Traceback
    from rich import print
    console = Console()
    tcb = Traceback.from_exception(type(context.error), context.error, context.error.__traceback__, show_locals=False, width=140, max_frames=8, extra_lines=1, locals_max_string=140)
    console.print(tcb)

async def webserver_logs(request):
    with open("logs.txt", "r") as file:
        last_lines = file.readlines()[-20:]
        my_response = ""
        for line in last_lines:
            my_response += line

    return web.Response(text=my_response)

async def post_init(app: Application) -> None:
    if 'last_restart' not in app.bot_data:
        app.bot_data['last_restart'] = config.ID_TESTING
    last_chat_id = app.bot_data['last_restart']

    r = get_reminders_from_db()
    added = 0
    
    for reminder in r['reminders']:
        # print(f"app.job_queue.run_once(send_reminder, {reminder['date_to_remind']}, chat_id={reminder['chat_id']}, name=f'{reminder['chat_id']}_{reminder['reply_id']}', data=reminder)")
        app.job_queue.run_once(send_reminder, reminder['date_to_remind'], chat_id=reminder['chat_id'], name=f"{reminder['chat_id']}_{reminder['reply_id']}", data=reminder)
        added += 1
    print(f"{get_now()} Trovati {r['processed']} reminders. {added} aggiunti e {r['deleted']} eliminati.")



    # wapp = web.Application()
    # wapp.add_routes([web.get('/logs', webserver_logs)])
    # runner = web.AppRunner(wapp)
    # await runner.setup()
    # site = web.TCPSite(runner, '0.0.0.0', 8888)
    # await site.start()

    # print(f'{get_now()} Server web inizializzato!')

    L = instaloader.Instaloader(dirname_pattern="ig/{target}", quiet=True, fatal_status_codes=[429], save_metadata=False, max_connection_attempts=1)
    USER = "emilia_superbot"
    L.load_session_from_file(USER, "db/session-emilia_superbot")

    await app.bot.send_message(chat_id=last_chat_id, text="Bot riavviato correttamente!")
    print(f'{get_now()} Tutto pronto!\n')
    print(f'{get_now()} In esecuzione!\n')
    return

async def post_shutdown(app: Application) -> None:
    import gc
    import aiohttp

    clientsessions = [obj for obj in gc.get_objects() if isinstance(obj, aiohttp.client.ClientSession)]

    for c in clientsessions:
        await c.close()

    return

def get_reminders_from_db():
    import pprint
    reminders_list = []
    reminders_da_processare = 0
    reminders_da_aggiungere = 0
    reminders_cancellati = 0

    for reminder in Reminders.select():
        if reminder:
            if datetime.datetime.strptime(reminder.date_to_remind, "%d/%m/%Y %H:%M") < datetime.datetime.now():
                reminders_cancellati += 1
                deletequery = Reminders.delete().where((Reminders.chat_id == reminder.chat_id) & (Reminders.reply_id == reminder.reply_id))
                deletequery.execute()

            else:
                r = {}
                r['message'] = reminder.message
                r['reply_id'] = reminder.reply_id
                r['user_id'] = reminder.user_id
                r['chat_id'] = reminder.chat_id
                r['date_now'] = datetime.datetime.strptime(reminder.date_now, "%d/%m/%Y %H:%M")
                r['date_to_remind'] = datetime.datetime.strptime(reminder.date_to_remind, "%d/%m/%Y %H:%M")
                reminders_da_aggiungere += 1
                reminders_list.append(r)
            reminders_da_processare += 1
    mydict = {
        "processed": reminders_da_processare,
        "to_add": reminders_da_aggiungere,
        "deleted": reminders_cancellati,
        "reminders": reminders_list
    }
    return mydict

if __name__ == "__main__":

    
    locale.setlocale(locale.LC_ALL, 'it_IT.utf8')
    print()
    print(f'{get_now()} Avvio - versione: {config.VERSION}\n--------------------------------------------')
    print(f'{get_now()} Using python-telegram-bot v{TG_VER} on Python {platform.python_version()}')
    


    db = peewee.SqliteDatabase(config.DBPATH)

    class TensorMessage(peewee.Model):
        tensor_text = peewee.TextField()
        tensor_id = peewee.AutoField()

        class Meta:
            database = db
            table_name = 'tensor'

    class Quote(peewee.Model):
        quote_text = peewee.TextField()
        quote_id = peewee.AutoField()

        class Meta:
            database = db
            table_name = 'quotes'

    class Reminders(peewee.Model):
        reply_id = peewee.TextField()
        user_id = peewee.TextField()
        chat_id = peewee.TextField()
        date_now = peewee.TextField()
        date_to_remind = peewee.TextField()
        message = peewee.TextField()

        class Meta:
            database = db
            table_name = 'reminders'
            primary_key = False

    class Compleanni(peewee.Model):
        user_id = peewee.TextField()
        chat_id = peewee.TextField()
        birthdate = peewee.TextField()

        class Meta:
            database = db
            table_name = 'compleanni'
            primary_key = False


    # creo le tabelle se non ci sono
    print(f'{get_now()} Controllo e creo le tabelle necessarie...')

    TensorMessage.create_table()
    Quote.create_table()
    Reminders.create_table()
    Compleanni.create_table()


    main()
