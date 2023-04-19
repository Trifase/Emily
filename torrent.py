import humanize
import qbittorrentapi
from telegram import Update
from telegram.ext import ContextTypes

import config
from utils import no_can_do, print_progressbar, printlog

_localize = humanize.i18n.activate("it_IT")

async def lista_torrent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return
    if update.effective_user.id not in config.ADMINS:
        return
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede la lista torrent')
    await printlog(update, "chiede la lista torrent")
    # instantiate a Client using the appropriate WebUI configuration
    # TORRENT
    qbt_client = qbittorrentapi.Client(host=f'{config.TORRENT_IP}:{config.TORRENT_PORT}', username=config.TORRENT_USER, password=config.TORRENT_PASSWORD, REQUESTS_ARGS={'timeout': 2.1})

    # the Client will automatically acquire/maintain a logged in state in line with any request.
    # therefore, this is not necessary; however, you many want to test the provided login credentials.
    # try:
    #     qbt_client.auth_log_in()
    # except Exception as e:
    #     print(e)

    # display qBittorrent info
    # print(f'qBittorrent: {qbt_client.app.version}')
    # print(f'qBittorrent Web API: {qbt_client.app.web_api_version}')
    # for k,v in qbt_client.app.build_info.items(): print(f'{k}: {v}')

    # retrieve and show all torrents
    message = ""
    try:
        if qbt_client.torrents_info() is None:
            await update.message.reply_text("Nessun torrent in download")
            return

        for torrent in qbt_client.torrents_info():
            progress_perc = round(torrent.progress * 100, 2)
            message += f'<b>{torrent.name}</b> (<i>{torrent.state}</i>)\n↓ {str(round(torrent.dlspeed/1024/1024, 2))} MB/s · ↑ {str(round(torrent.upspeed/1024/1024, 2))} MB/s\nETA: {"∞" if torrent.eta == 8640000 else (str(humanize.precisedelta(torrent.eta, suppress=["days"], minimum_unit="seconds")))}\nProgress: {print_progressbar(progress_perc, suffix="", prefix="")} - {str(progress_perc)}%\n\n'
        if not message:
            await update.message.reply_text("Nessun torrent in download")
        else:
            await update.message.reply_html(message)
    except Exception as e:
        await update.message.reply_text(f"Errore!\n{e}")
    # # pause all torrents
    # qbt_client.torrents.pause.all()