import datetime
import json
import locale
import platform
import re
import traceback
import warnings

import instaloader
import peewee
import pytz
from aiohttp import web
from rich import print
from telegram import Update
from telegram import __version__ as TG_VER
from telegram.constants import ParseMode
from telegram.ext import (
    AIORateLimiter,
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    Defaults,
    InlineQueryHandler,
    MessageHandler,
    PicklePersistence,
    PollAnswerHandler,
    PreCheckoutQueryHandler,
    filters,
)

import config
from admin import (
    _eval,
    add_ban,
    banlist,
    cancella,
    check_temp,
    clean_db,
    commandlist,
    count_lines,
    del_ban,
    echo,
    esci,
    executecode,
    flush_arbitrary_callback_data,
    getchat,
    ip,
    lista_chat,
    listen_to,
    parla,
    restart,
    screenshot,
    send_custom_media,
    set_group_picture,
    set_title,
    tg_info,
    trigger_backup,
    wakeup,
)
from asphalto import azzurro
from banca import bot_get_saldo, bot_get_transazioni
from best_timeline import deleta_if_channel, permasilenzia, scrape_tweet_bt, silenzia
from compleanni import compleanni_add, compleanni_list, compleanni_manual_check, compleanno_del
from cron_jobs import (
    check_compleanni,
    do_global_backup,
    lotto_member_count,
    parse_diochan,
    post_solarsystem_mastodon
)
from diochan import (
    add_quote,
    ascendi,
    diochan,
    get_thread_from_dc,
    random_tensor,
    save_tensor,
    search_quote,
)
from donazioni import donazioni, precheckout_callback, successful_payment_callback
from games import sassocartaforbici
from lotto import elenco_maesta, maesta_primo, stat_maesta
from macros import change_my_mind, ispirami
from maps import location, maps_buttons, streetview
from meteo import forecast, meteo_oggi, ora, prometeo_oggi
from misc import (
    alexa,
    aoc_leaderboard,
    bioritmo,
    bomb_react,
    condominioweb,
    fascio,
    fatfingers,
    get_user_info,
    greet_BT_user,
    lurkers,
    lurkers_callbackqueryhandlers,
    markovs,
    polls_callbackqueryhandlers,
    random_trifase,
    scacchi,
    self_delete,
    send_auto_reaction,
    set_auto_reaction,
    spongebob,
    square,
    start,
    traduci,
    voice,
    wikihow,
)
from movies import doveguardo, doveguardo_buttons, imdb
from open_ai import ai_old, ai_stream, openai_stats, whisper_transcribe
from parse_everything import (
    check_for_sets,
    drop_update_from_banned_users,
    exit_from_banned_groups,
    messaggio_spiato,
    new_admin_buttons,
    nuova_chat_rilevata,
    save_messages_stats,
    track_chats,
    update_timestamps_asphalto,
)
from pyrog import reaction_karma
from quiz import classifica, make_poll, punteggio, ricevi_risposta_quiz
from reddit import reddit
from reminders import remindelete, reminder_helper, reminders_list, remindme, send_reminder
from scrapers import (
    facebook_video,
    instagram_stories,
    new_instagram,
    ninofrassica,
    parse_reddit_link,
    scrape_tweet_media,
    tiktok,
    tiktok_inline,
    tiktok_long,
    twitch_clips,
    wikipedia,
    youtube_alts,
)
from sets import addset, deleteset, jukebox, listaset
from smarthome import consumo, luci_status, purificatore, riscaldamento_stats, toggle_light
from space import launches, solarsystem
from spotify import spoty
from stats import send_stats
from tarots import tarot, tarotschema
from testing import getfile, test
from torrent import lista_torrent
from twitter import lista_tweets, tweet
from utils import (
    count_k_v,
    get_now,
    is_forged_command,
    is_inline_button,
    is_lurkers_list,
    printlog,
)
from zoom import zoom_link


warnings.filterwarnings("ignore")

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

    builder.http_version('1.1')
    builder.get_updates_http_version('1.1')

    app = builder.build()

    # cron_jobs.py
    j = app.job_queue

    # j.run_repeating(plot_boiler_stats, interval=2600.0, data=None, job_kwargs={'misfire_grace_time': 25})

    # Run every hour
    j.run_repeating(parse_diochan, interval=1800, data=None, job_kwargs={'misfire_grace_time': 25})


    j.run_daily(lotto_member_count, datetime.time(hour=9, minute=0, tzinfo=pytz.timezone('Europe/Rome')), data=None)
    # j.run_daily(autolurkers, datetime.time(hour=9, minute=0, tzinfo=pytz.timezone('Europe/Rome')), data=None)
    j.run_daily(post_solarsystem_mastodon, datetime.time(hour=8, minute=30, tzinfo=pytz.timezone('Europe/Rome')), data=None)

    j.run_daily(check_compleanni, datetime.time(hour=0, minute=0, tzinfo=pytz.timezone('Europe/Rome')), data=None)
    j.run_daily(check_compleanni, datetime.time(hour=12, minute=00, tzinfo=pytz.timezone('Europe/Rome')), data=None)
    j.run_daily(check_compleanni, datetime.time(hour=20, minute=00, tzinfo=pytz.timezone('Europe/Rome')), data=None)

    j.run_daily(do_global_backup, datetime.time(hour=2, minute=00, tzinfo=pytz.timezone('Europe/Rome')), data=None)

    # parse_everything.py
    # app.add_handler(CallbackQueryHandler(admin_buttons, pattern=r'^cmd:'))
    app.add_handler(CallbackQueryHandler(new_admin_buttons, pattern=is_forged_command))

    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, drop_update_from_banned_users), -1001)
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, exit_from_banned_groups), -20)
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, nuova_chat_rilevata), -19)
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, update_timestamps_asphalto), -18)
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, messaggio_spiato), -17)
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, check_for_sets), -16)
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL, save_messages_stats), -15)

    # Error handler
    app.add_error_handler(error_handler)

    # admin.py
    app.add_handler(CommandHandler(['checktemp', 'check_temp', 'temp', 'temperatura'], check_temp, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('flush_arbitrary_callback_data', flush_arbitrary_callback_data))
    app.add_handler(CommandHandler(['screenshot', 'ss'], screenshot, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
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
    app.add_handler(CommandHandler(['delban', 'del_ban', 'unban', 'sban'], del_ban, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['set_title', 'settitle', 'title'], set_title, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler(['set_propic', 'setpicture', 'propic'], set_group_picture, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('backup', trigger_backup, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    # app.add_handler(CommandHandler("show_chats", show_chats), 48)
    app.add_handler(CommandHandler(['send_media', 'send_custom_media', 'send'], send_custom_media, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    app.add_handler(CommandHandler('clean_db', clean_db, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))
    

    app.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER), 44)

    # asphalto.py
    app.add_handler(CommandHandler(['azzurro', 'azz'], azzurro, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('lurkers', lurkers, filters=~filters.UpdateType.EDITED))
    app.add_handler(CallbackQueryHandler(lurkers_callbackqueryhandlers, pattern=is_lurkers_list), -999)

    # banca.py
    app.add_handler(CommandHandler(['saldo', 'carige_saldo'], bot_get_saldo, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['movimenti', 'transazioni', 'carige_movimenti'], bot_get_transazioni, filters=~filters.UpdateType.EDITED))

    # best_timeline.py
    app.add_handler(MessageHandler(
        ~filters.UpdateType.EDITED & 
        filters.Regex(re.compile(r"(?:(?:http|https):\/\/)?(?:www.|mobile.)?(?:twitter.com)\/(?:\w+)\/status\/(\w+)", re.IGNORECASE)), scrape_tweet_bt
        ), group=929)
    app.add_handler(CommandHandler(['silenzia', 'silenzio', 'taci', 'shhh'], silenzia, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['permasilenzia', 'permasilenzio', 'permataci', 'shhhhhhhh', 'permamute'], permasilenzia, filters=~filters.UpdateType.EDITED))
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
    app.add_handler(CommandHandler('get_thread', get_thread_from_dc, filters=~filters.UpdateType.EDITED))
    # app.add_handler(ChatMemberHandler(greet, ChatMemberHandler.CHAT_MEMBER))
    # app.add_handler(CommandHandler('setgreet', set_greet, filters=~filters.UpdateType.EDITED))
    # app.add_handler(CommandHandler('setgreetpic', set_greet_pic, filters=~filters.UpdateType.EDITED))
    
    # app.add_handler(MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r'\bmon\b', re.IGNORECASE)), mon), 25)

    # donazioni.py
    app.add_handler(CommandHandler("donazione", donazioni))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    # games.py
    app.add_handler(CommandHandler(['sassocartaforbici', 'scf', 'morracinese', 'morra'], sassocartaforbici))

    # lotto.py
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT & filters.Chat(config.ID_LOTTO), maesta_primo), 15)
    app.add_handler(CommandHandler("maesta", elenco_maesta))
    app.add_handler(CommandHandler(["stats_maesta", 'maesta_stats', 'maestats', 'maestat'], stat_maesta))

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
    app.add_handler(CallbackQueryHandler(self_delete, pattern=r'^deleteme_'))
    app.add_handler(CommandHandler('wikihow', wikihow, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('markov', markovs, filters=~filters.UpdateType.EDITED))
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

    # openai.py
    app.add_handler(CommandHandler(["aistatic", 'oldai', 'aiold', 'ai_old'], ai_old))
    app.add_handler(CommandHandler("aistats", openai_stats))
    app.add_handler(CommandHandler(["ai", "new_ai", "aistream"], ai_stream))
    app.add_handler(CommandHandler(["transcribe", "speech", "scrivi", "trascrivi"], whisper_transcribe))

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
        filters.Regex(re.compile(r"http(?:s)?:\/\/(?:[\w-]+?\.)?reddit\.com(\/r\/|\/user\/)?([\w:\.]{2,21})(\/comments\/)?(\w{5,9}(?:\/[\w%\\-]+)?)?(\/\w{7})?\/?(\?)?(\S+)?", re.IGNORECASE)), parse_reddit_link
        ))
    app.add_handler(MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r"(?:https:\/\/)?clips\.twitch\.tv\/(\S+)", re.IGNORECASE)), twitch_clips))


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


    # spotify.py
    app.add_handler(MessageHandler(
        ~filters.UpdateType.EDITED & 
        filters.Regex(re.compile(r"(?:(?:http|https):\/\/)?(?:open\.)(?:spotify\.com)\/(?:track|album)\/(?:\S+)", re.IGNORECASE)), spoty
        ))


    # stats.py
    app.add_handler(CommandHandler(['stats', 'statistiche'], send_stats, filters=~filters.UpdateType.EDITED))
    # app.add_handler(CommandHandler(['populate_chat_data_from_jsons'], populate_chat_data_from_jsons, filters=~filters.UpdateType.EDITED))

    # tarots.py
    app.add_handler(CommandHandler(['tarot', 'tarots', 'tarocchi'], tarot, filters=~filters.UpdateType.EDITED))
    # app.add_handler(CommandHandler(['oroscopo', 'horoscope', 'oro'], oroscopo, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['tarotschema', 'reversetarots', 'schema'], tarotschema, filters=~filters.UpdateType.EDITED))


    # testing.py
    app.add_handler(CommandHandler(['test', 'ping'], test, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler('getfile', getfile, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))


    # torrent.py
    app.add_handler(CommandHandler(['torrents', 'torrentlist', 'listatorrent', 'lista_torrent'], lista_torrent, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF)))

    # twitter.py
    app.add_handler(CommandHandler(['tw', 'tweet'], tweet, filters=~filters.UpdateType.EDITED))
    app.add_handler(CommandHandler(['tweetlists', 'listatweet', 'tweets', 'twlist'], lista_tweets, filters=~filters.UpdateType.EDITED))

    # zoom.py
    app.add_handler(CommandHandler(['zoom', 'zoomlink', 'zoomlinks'], zoom_link, filters=~filters.UpdateType.EDITED))

    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    await printlog(update, f"{tb_string}", error=True)

async def webserver_logs(request):
    current_m = datetime.date.today().strftime("%Y-%m")
    with open(f'logs/{current_m}-logs.txt', "r") as file:
        last_lines = file.readlines()[-100:]
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

    if 'current_sets' not in app.bot_data:
        app.bot_data['current_sets'] = {}
    with open('db/sets.json') as sets_db:
        sets = json.load(sets_db)
        app.bot_data['current_sets'] = sets
    k, v = count_k_v(sets)
    print(f"{get_now()} Sets caricati. {v} keywords totali.")
    for reminder in r['reminders']:
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

    # import gc
    # import aiohttp
    # clientsessions = [obj for obj in gc.get_objects() if isinstance(obj, aiohttp.client.ClientSession)]
    # for c in clientsessions:
    #     await c.close()
    return

def get_reminders_from_db():
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
