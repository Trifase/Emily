import re
from telegram.ext import (
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
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
from best_timeline import deleta_if_channel, permasilenzia, silenzia#, scrape_tweet_bt
from compleanni import compleanni_add, compleanni_list, compleanni_manual_check, compleanno_del
from diochan import add_quote, ascendi, diochan, get_thread_from_dc, random_tensor, save_tensor, search_quote
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
    movie,
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
from open_ai import ai_old, ai_stream, openai_stats, riassuntone, whisper_transcribe
from parse_everything import (
    check_for_sets,
    drop_update_from_banned_users,
    exit_from_banned_groups,
    log_message,
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
from reminders import remindelete, reminder_helper, reminders_list, remindme
from scrapers import (
    # facebook_video,
    instagram_stories,
    new_instagram,
    ninofrassica,
    parse_reddit_link,
    # scrape_tweet_media,
    tiktok,
    tiktok_inline,
    tiktok_long,
    twitch_clips,
    wikipedia,
    # youtube_alts,
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
from utils import is_forged_command, is_inline_button, is_lurkers_list
from zoom import zoom_link


def generate_handlers_dict() -> dict:

    h = {}

    # parse_everything.py
    h[-1001] = [CallbackQueryHandler(new_admin_buttons, pattern=is_forged_command)]
    h[-1002] = [MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, drop_update_from_banned_users)]
    h[-20] = [MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, exit_from_banned_groups)]
    h[-19] = [MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, nuova_chat_rilevata)]
    h[-18] = [MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, update_timestamps_asphalto)]
    h[-17] = [MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, messaggio_spiato)]
    h[-16] = [MessageHandler(~filters.UpdateType.EDITED & ~filters.COMMAND & filters.TEXT, log_message)]
    h[-15] = [MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT, check_for_sets)]
    h[-14] = [MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL, save_messages_stats)]
    h[-13] = [ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER)]

    # admin.py
    h[-12] = [CommandHandler(['checktemp', 'check_temp', 'temp', 'temperatura'], check_temp, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[-11] = [CommandHandler('flush_arbitrary_callback_data', flush_arbitrary_callback_data)]
    h[-10] = [CommandHandler(['screenshot', 'ss'], screenshot, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[-9] = [CommandHandler(['parla', 'say'], parla, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[-8] = [CommandHandler('restart', restart, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[-7] = [CommandHandler('print', _eval, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[-6] = [CommandHandler(['commandlist','lista_comandi', 'commands'], commandlist, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[-5] = [CommandHandler(['del','cancella', 'delete'], cancella, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[-4] = [CommandHandler('sloc', count_lines, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[-3] = [CommandHandler('exec', executecode, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[-2] = [CommandHandler(['ripeti', 'echo'], echo, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[-1] = [CommandHandler('info', tg_info, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[0] = [CommandHandler(['getchat', 'get_chat'], getchat, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[1] = [CommandHandler(['chatlist', 'listachat', 'lista_chat'], lista_chat, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[2] = [CommandHandler(['listen_to', 'listen'], listen_to, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[3] = [CommandHandler('esci', esci, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[4] = [CommandHandler(['ip', 'myip'], ip, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[5] = [CommandHandler('wakeup', wakeup, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[6] = [CommandHandler(['listaban', 'ban_list', 'banlist'], banlist, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[7] = [CommandHandler(['addban', 'ban', 'add_ban'], add_ban, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[8] = [CommandHandler(['delban', 'del_ban', 'unban', 'sban'], del_ban, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[9] = [CommandHandler(['set_title', 'settitle', 'title'], set_title, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[10] = [CommandHandler(['set_propic', 'setpicture', 'propic'], set_group_picture, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[11] = [CommandHandler('backup', trigger_backup, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[12] = [CommandHandler(['send_media', 'send_custom_media', 'send'], send_custom_media, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]
    h[13] = [CommandHandler('clean_db', clean_db, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]

    # asphalto.py
    h[14] = [CommandHandler(['azzurro', 'azz'], azzurro, filters=~filters.UpdateType.EDITED)]
    h[15] = [CommandHandler('lurkers', lurkers, filters=~filters.UpdateType.EDITED)]
    h[-101] = [CallbackQueryHandler(lurkers_callbackqueryhandlers, pattern=is_lurkers_list)]

    # banca.py
    h[16] = [CommandHandler(['saldo', 'carige_saldo'], bot_get_saldo, filters=~filters.UpdateType.EDITED)]
    h[17] = [CommandHandler(['movimenti', 'transazioni', 'carige_movimenti'], bot_get_transazioni, filters=~filters.UpdateType.EDITED)]

    # best_timeline.py
    # best_timeline_twitter_regex = r"(?:(?:http|https):\/\/)?(?:www.|mobile.)?(?:twitter.com)\/(?:\w+)\/status\/(\w+)"
    # h[-201] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(best_timeline_twitter_regex, re.IGNORECASE)), scrape_tweet_bt)]
    h[18] = [CommandHandler(['silenzia', 'silenzio', 'taci', 'shhh'], silenzia, filters=~filters.UpdateType.EDITED)]
    h[19] = [CommandHandler(['permasilenzia', 'permasilenzio', 'permataci', 'shhhhhhhh', 'permamute'], permasilenzia, filters=~filters.UpdateType.EDITED)]
    h[20] = [MessageHandler(filters.SenderChat.CHANNEL, deleta_if_channel)]
    h[21] = [CommandHandler(['aoc', 'leaderboard'], aoc_leaderboard, filters=~filters.UpdateType.EDITED)]

    # compleanni.py
    h[22] = [CommandHandler(['compleanno', 'addcompleanno'], compleanni_add, filters=~filters.UpdateType.EDITED)]
    h[23] = [CommandHandler(['compleanni', 'listacompleanni'], compleanni_list, filters=~filters.UpdateType.EDITED)]
    h[24] = [CommandHandler(['cancellacompleanno', 'delcompleanno'], compleanno_del, filters=~filters.UpdateType.EDITED)]
    h[25] = [CommandHandler('compleanni_check', compleanni_manual_check, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]

    # diochan.py
    h[26] = [CommandHandler('quote', search_quote, filters=~filters.UpdateType.EDITED & filters.Chat(config.ID_DIOCHAN))]
    h[27] = [CommandHandler('addquote', add_quote, filters=~filters.UpdateType.EDITED & filters.Chat(config.ID_DIOCHAN))]
    h[28] = [CommandHandler('ascendi', ascendi, filters=~filters.UpdateType.EDITED & filters.Chat(config.ID_DIOCHAN))]
    h[29] = [CommandHandler('diochan', diochan, filters=~filters.UpdateType.EDITED)]
    h[30] = [CommandHandler(['tensor', 'tensorbot'], random_tensor, filters=~filters.UpdateType.EDITED)]
    h[-301] = [MessageHandler(~filters.UpdateType.EDITED & filters.TEXT & filters.User(username="@Tensor1987"), save_tensor)]
    h[32] = [CommandHandler('get_thread', get_thread_from_dc, filters=~filters.UpdateType.EDITED)]

    # donazioni.py
    h[33] = [CommandHandler("donazione", donazioni)]
    h[34] = [PreCheckoutQueryHandler(precheckout_callback)]
    h[35] = [MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)]

    # games.py
    h[36] = [CommandHandler(['sassocartaforbici', 'scf', 'morracinese', 'morra'], sassocartaforbici)]

    # lotto.py
    h[-401] = [MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL & filters.TEXT & filters.Chat(config.ID_LOTTO), maesta_primo)]
    h[38] = [CommandHandler("maesta", elenco_maesta)]
    h[39] = [CommandHandler(["stats_maesta", 'maesta_stats', 'maestats', 'maestat'], stat_maesta)]

    # macros.py
    h[40] = [CommandHandler('ispirami', ispirami, filters=~filters.UpdateType.EDITED)]
    h[41] = [CommandHandler(['changemymind', 'change'], change_my_mind, filters=~filters.UpdateType.EDITED)]

    # maps.py
    h[42] = [CommandHandler(['loc', 'localize', 'location', 'dove'], location, filters=~filters.UpdateType.EDITED)]
    h[43] = [CommandHandler(['sw', 'street', 'streetview'], streetview, filters=~filters.UpdateType.EDITED)]
    h[44] = [CallbackQueryHandler(maps_buttons, pattern=r'^m_')]

    # meteo.py
    h[45] = [CommandHandler('ora', ora, filters=~filters.UpdateType.EDITED)]
    h[46] = [CommandHandler('prometeo', prometeo_oggi, filters=~filters.UpdateType.EDITED)]
    h[47] = [CommandHandler('meteo', meteo_oggi, filters=~filters.UpdateType.EDITED)]
    h[48] = [CommandHandler(['forecast', 'previsioni'], forecast, filters=~filters.UpdateType.EDITED)]

    # misc.py
    h[49] = [CallbackQueryHandler(self_delete, pattern=r'^deleteme_')]
    h[491] = [CommandHandler('movie', movie, filters=~filters.UpdateType.EDITED)]
    h[50] = [CommandHandler('wikihow', wikihow, filters=~filters.UpdateType.EDITED)]
    h[51] = [CommandHandler('markov', markovs, filters=~filters.UpdateType.EDITED)]
    h[52] = [CommandHandler(['trifase', 'randomtrif', 'randomtrifase'], random_trifase, filters=~filters.UpdateType.EDITED)]
    h[53] = [MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_BT_user)]
    h[-501] = [CallbackQueryHandler(polls_callbackqueryhandlers, pattern=is_inline_button)]
    h[54] = [CommandHandler('condominioweb', condominioweb, filters=~filters.UpdateType.EDITED)]
    h[55] = [CommandHandler(['start'], start, filters=filters.ChatType.PRIVATE)]
    h[56] = [CommandHandler(['bioritmo', 'bio', 'biorhythm'], bioritmo, filters=~filters.UpdateType.EDITED)]
    h[57] = [CommandHandler('traduci', traduci, filters=~filters.UpdateType.EDITED)]
    h[58] = [CommandHandler('get_user_info', get_user_info, filters=~filters.UpdateType.EDITED)]
    h[59] = [CommandHandler('spongebob', spongebob, filters=~filters.UpdateType.EDITED)]
    h[60] = [CommandHandler('square', square, filters=~filters.UpdateType.EDITED)]
    h[61] = [CommandHandler('fascio', fascio, filters=~filters.UpdateType.EDITED)]
    h[62] = [CommandHandler(['lichess', 'lichness'], scacchi, filters=~filters.UpdateType.EDITED)]
    h[63] = [CommandHandler('voice', voice, filters=~filters.UpdateType.EDITED)]
    h[64] = [CommandHandler(['fatfinger', 'fatfingers'], fatfingers, filters=~filters.UpdateType.EDITED)]
    h[65] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r"[Aa]lexa (?:[Pp]lay|[Rr]iproduci) (.+)", re.IGNORECASE)), alexa)]
    h[66] = [CommandHandler('autoreaction', set_auto_reaction, filters=~filters.UpdateType.EDITED)]
    h[67] = [MessageHandler(~filters.UpdateType.EDITED & ~filters.ChatType.CHANNEL, send_auto_reaction)]
    h[68] = [CommandHandler('bombreact', bomb_react, filters=~filters.UpdateType.EDITED)]

    # movies.py
    h[69] = [CommandHandler(['doveguardo', 'dove_guardo'], doveguardo, filters=~filters.UpdateType.EDITED)]
    h[70] = [CallbackQueryHandler(doveguardo_buttons, pattern=r'^dvg_')]
    h[71] = [CommandHandler(['imdb', 'torrent'], imdb, filters=~filters.UpdateType.EDITED)]

    # openai.py
    h[72] = [CommandHandler(["aistatic", 'oldai', 'aiold', 'ai_old'], ai_old)]
    h[73] = [CommandHandler("aistats", openai_stats)]
    h[74] = [CommandHandler(["ai", "new_ai", "aistream"], ai_stream)]
    h[75] = [CommandHandler(["transcribe", "speech", "scrivi", "trascrivi"], whisper_transcribe)]
    h[76] = [CommandHandler(["riassunto", "riassuntone"], riassuntone)]

    # pyrog.py
    h[77] = [CommandHandler(['karma', 'reactionlist', 'reactkarma'], reaction_karma, filters=~filters.UpdateType.EDITED)]

    # quiz.py
    h[78] = [CommandHandler('trivia', make_poll, filters=~filters.UpdateType.EDITED)]
    h[79] = [PollAnswerHandler(ricevi_risposta_quiz)]
    h[80] = [CommandHandler('punteggio', punteggio, filters=~filters.UpdateType.EDITED)]
    h[81] = [CommandHandler('classifica', classifica, filters=~filters.UpdateType.EDITED)]

    # reddit.py
    h[82] = [CommandHandler(['redd', 'reddit'], reddit, filters=~filters.UpdateType.EDITED)]

    # reminders.py
    h[83] = [CommandHandler(['reminder', 'remindhelp'], reminder_helper, filters=~filters.UpdateType.EDITED)]
    h[84] = [CommandHandler(['remindme', 'remind'], remindme, filters=~filters.UpdateType.EDITED)]
    h[85] = [CommandHandler(['reminderlist', 'remindlist', 'listareminder', 'reminder_list'], reminders_list, filters=~filters.UpdateType.EDITED)]
    h[86] = [CommandHandler(['reminder_delete', 'remindelete', 'deletereminder'], remindelete, filters=~filters.UpdateType.EDITED)]

    # scrapers.py
    regex_instagram = r"(\b\S+(:?instagram\.com|instagr\.am)\S+\b)"
    regex_tiktok = r"(?:https?://vm.tiktok.com\/(\w+))"
    regex_tiktok_long = r"(?:(?:http|https):\/\/)?(?:www.)?(?:tiktok.com)\/(@[a-zA-Z0-9_.]+)\/video\/(\w+)"
    # regex_tweet_media = r"(?:(?:http|https):\/\/)?(?:www.|mobile.)?(?:twitter.com)\/(?:\w+)\/status\/(\w+)"
    # regex_youtube_alts = r"(?:(?:http:\/\/)?|(?:https:\/\/)?)?(?:yewtu.be|utew.be)\/(?:watch\?v=)?([a-zA-Z0-9_-]{6,11})"
    # regex_fb_video = r"(?:(?:http|https):\/\/)?(?:www\.|fb\.watch)\/([^\/]{10})"
    # regex_facebok_video = r"(?:(?:http|https):\/\/)?(?:www.|fb.|m.)?(?:watch|facebook.com)(?:\/[\w.]+)(?:\/videos|\/watch)\/([\w.]+)"
    regex_reddit = r"http(?:s)?:\/\/(?:[\w-]+?\.)?reddit\.com(\/r\/|\/user\/)?([\w:\.]{2,21})(\/comments\/)?(\w{5,9}(?:\/[\w%\\-]+)?)?(\/\w{7})?\/?(\?)?(\S+)?"
    regex_twitch_clip = r"(?:https:\/\/)?clips\.twitch\.tv\/(\S+)"

    h[87] = [CommandHandler(["wikipedia", "wiki"], wikipedia, filters=~filters.UpdateType.EDITED)]
    h[88] = [CommandHandler('ninofrassica', ninofrassica, filters=~filters.UpdateType.EDITED)]
    h[89] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(regex_instagram, re.IGNORECASE)), new_instagram)]
    h[90] = [CommandHandler(['stories', 'storie'], instagram_stories, filters=~filters.UpdateType.EDITED)]
    h[91] = [InlineQueryHandler(tiktok_inline)]
    h[92] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(regex_tiktok, re.IGNORECASE)), tiktok)]
    h[93] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(regex_tiktok_long, re.IGNORECASE)), tiktok_long)]
    # h[94] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(regex_tweet_media, re.IGNORECASE)), scrape_tweet_media)]
    # h[95] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(regex_youtube_alts, re.IGNORECASE)), youtube_alts)]
    # h[96] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(regex_fb_video, re.IGNORECASE)), facebook_video)]
    # h[97] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(regex_facebok_video, re.IGNORECASE)), facebook_video)]
    h[98] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(regex_reddit, re.IGNORECASE)), parse_reddit_link)]
    h[99] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(regex_twitch_clip, re.IGNORECASE)), twitch_clips)]

    # sets.py
    h[100] = [CommandHandler(['addset', 'set'], addset, filters=~filters.UpdateType.EDITED)]
    h[101] = [CommandHandler(['listaset', 'setlist'], listaset, filters=~filters.UpdateType.EDITED)]
    h[102] = [CommandHandler(['deleteset', 'delset'], deleteset, filters=~filters.UpdateType.EDITED)]
    h[103] = [CommandHandler(['jukebox', 'audio'], jukebox, filters=~filters.UpdateType.EDITED)]

    # smarthome.py
    h[104] = [CommandHandler(['status_luci', 'statusluci', 'luci', 'luci_status'], luci_status, filters=~filters.UpdateType.EDITED)]
    h[105] = [CommandHandler(['toggle', 'luce', 'toggla'], toggle_light, filters=~filters.UpdateType.EDITED)]
    h[106] = [CommandHandler(['consumo'], consumo, filters=~filters.UpdateType.EDITED)]
    h[107] = [CommandHandler(['purificatore', 'purifier'], purificatore, filters=~filters.UpdateType.EDITED)]
    h[108] = [CommandHandler(['riscaldamento', 'boiler', 'caldaia'], riscaldamento_stats, filters=~filters.UpdateType.EDITED)]

    # space.py
    h[109] = [CommandHandler(['solarsystem', 'stelle', 'stars'], solarsystem, filters=~filters.UpdateType.EDITED)]
    h[110] = [CommandHandler(['lanci', 'launches'], launches, filters=~filters.UpdateType.EDITED)]

    # spotify.py
    regex_spotify = r"(?:(?:http|https):\/\/)?(?:open\.)(?:spotify\.com)\/(?:track|album)\/(?:\S+)"
    h[111] = [MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(regex_spotify, re.IGNORECASE)), spoty)]

    # stats.py
    h[112] = [CommandHandler(['stats', 'statistiche'], send_stats, filters=~filters.UpdateType.EDITED)]

    # tarots.py
    h[113] = [CommandHandler(['tarot', 'tarots', 'tarocchi'], tarot, filters=~filters.UpdateType.EDITED)]
    h[114] = [CommandHandler(['tarotschema', 'reversetarots', 'schema'], tarotschema, filters=~filters.UpdateType.EDITED)]

    # testing.py
    h[115] = [CommandHandler(['test', 'ping'], test, filters=~filters.UpdateType.EDITED)]
    h[116] = [CommandHandler('getfile', getfile, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]

    # torrent.py
    h[117] = [CommandHandler(['torrents', 'torrentlist', 'listatorrent', 'lista_torrent'], lista_torrent, filters=~filters.UpdateType.EDITED & filters.User(config.ID_TRIF))]

    # twitter.py
    h[118] = [CommandHandler(['tw', 'tweet'], tweet, filters=~filters.UpdateType.EDITED)]
    h[119] = [CommandHandler(['tweetlists', 'listatweet', 'tweets', 'twlist'], lista_tweets, filters=~filters.UpdateType.EDITED)]

    # zoom.py
    h[120] = [CommandHandler(['zoom', 'zoomlink', 'zoomlinks'], zoom_link, filters=~filters.UpdateType.EDITED)]

    # DEPRECATED
    # parse_everything.py   CallbackQueryHandler(admin_buttons, pattern=r'^cmd:')
    # admin.py              CommandHandler("show_chats", show_chats)
    # asphalto.py           ChatMemberHandler(greet, ChatMemberHandler.CHAT_MEMBER)
    # asphalto.py           CommandHandler('setgreet', set_greet, filters=~filters.UpdateType.EDITED)
    # asphalto.py           CommandHandler('setgreetpic', set_greet_pic, filters=~filters.UpdateType.EDITED)
    # asphalto.py           MessageHandler(~filters.UpdateType.EDITED & filters.Regex(re.compile(r'\bmon\b', re.IGNORECASE)), mon)
    # misc.py [py3.11]      CommandHandler('is_safe', is_safe, filters=~filters.UpdateType.EDITED)
    # misc.py               CommandHandler('chiedi_opinione', chiedi_opinione)
    # misc.py               CommandHandler('help', call_help, filters=~filters.UpdateType.EDITED)
    # stats                 CommandHandler(['populate_chat_data_from_jsons'], populate_chat_data_from_jsons, filters=~filters.UpdateType.EDITED)
    #tarots                 CommandHandler(['oroscopo', 'horoscope', 'oro'], oroscopo, filters=~filters.UpdateType.EDITED)

    return h

def generate_jobs() -> dict:
    return