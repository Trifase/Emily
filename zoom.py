
import base64
import urllib

import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

import config
from utils import printlog


async def zoom_link(update: Update, context: CallbackContext):
    def get_meeting_uuid_from_url(url):
        return urllib.parse.unquote(url.split('meeting_id=')[1], encoding='utf-8', errors='replace')

    def get_access_token(acc_id, client_id, client_secret) -> str:
        message = f"{client_id}:{client_secret}"
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_string = base64_bytes.decode("ascii")


        headers = {
            'Host': 'zoom.us',
            'Authorization': f'Basic {base64_string}',
        }

        data = {
        'grant_type': 'account_credentials',
        'account_id': acc_id
        }

        response = requests.post('https://zoom.us/oauth/token', headers=headers, data=data).json()
        return response['access_token']

    # def get_all_recordings(token):

    #     headers = {
    #         'Authorization': f'Bearer {token}',
    #     }
    #     response = requests.get('https://api.zoom.us/v2/users/me/recordings', headers=headers).json()
    #     return response

    def double_encode(meeeting_uuid):
        single_encoded = urllib.parse.quote_plus(meeeting_uuid, encoding='utf-8', errors='replace')
        double_encoded = urllib.parse.quote_plus(single_encoded, encoding='utf-8', errors='replace')
        return double_encoded

    def get_meeting_recordings(token, meeting_uuid):

        headers = {
            'Authorization': f'Bearer {token}',
        }

        response = requests.get(f'https://api.zoom.us/v2/meetings/{meeting_uuid}/recordings', headers=headers).json()

        return response

    def get_meeting_setting(token, meeting_uuid):
        headers = {
            'Authorization': f'Bearer {token}',
        }

        response = requests.get(f'https://api.zoom.us/v2/meetings/{meeting_uuid}/recordings/settings', headers=headers).json()

        return response

    def check_correct_permissions(token, meeting_uuid):
        settings = get_meeting_setting(token, meeting_uuid)
        assert settings['password'] == ''
        assert settings['viewer_download'] is False
        assert settings['topic'] == f'{oggi} Lezione di Yoga'
        assert settings['on_demand'] is True
        return True

    def patch_default_permissions(token, meeting_uuid, oggi):
        new_settings = {
            'password': '',
            'viewer_download': False,
            'on_demand': True,
            'topic': f'{oggi} Lezione di Yoga',
        }

        headers = {
            'Authorization': f'Bearer {token}',
        }

        response = requests.patch(f'https://api.zoom.us/v2/meetings/{meeting_uuid}/recordings/settings', headers=headers, json=new_settings)

        return response

    def create_tg_post(oggi, share_url):
        return f"🧘🏻‍♀️ Buona sera miei adorati Yogi 🧘🏻‍♀️\nEcco la <a href='{share_url}'>registrazione dell'ultima lezione</a>, buona pratica 💜🙏🏻\n"

    if update.effective_user.id not in config.ADMINS:
        return

    acc_id = config.ZOOM_acc_id
    client_id = config.ZOOM_client_id
    client_secret = config.ZOOM_client_secret

    if not context.args:
        await update.message.reply_html("Devi mandarmi un link alla registrazione zoom")
        return

    url = context.args[0]
   
    if 'meeting_id' not in url:
        await update.message.reply_html("Devi mandarmi un link alla registrazione zoom")
        return

    mytoken = get_access_token(acc_id, client_id, client_secret)
    meeting_uuid = get_meeting_uuid_from_url(url)
    if meeting_uuid.startswith('/') or '//' in meeting_uuid:
        meeting_uuid = double_encode(meeting_uuid)
    recordings = get_meeting_recordings(mytoken, meeting_uuid)
    oggi = recordings['start_time'][:10]
    share_url = recordings['share_url']

    patch_default_permissions(mytoken, meeting_uuid, oggi)
    if check_correct_permissions(mytoken, meeting_uuid):
        message = create_tg_post(oggi, share_url)

    await printlog(update, "manda un link alla registrazione zoom")
    if update.effective_user.id == config.ID_ANNALISA:
        await context.bot.send_message(-1001551199754, message, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_html(message)





   
