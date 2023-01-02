
import tempfile
import traceback

from rich import print
from telegram import Update
from telegram.ext import CallbackContext, ContextTypes

import config
from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do, crea_sondaggino


# async def chiedi_opinione(update, context, original_update=None, poll_passed=False):

#     if poll_passed:
#         await original_update.message.reply_html('IT WERKS')
#         return

    
#     if not context.args:
#         max_votes = 8
#     else: 
#         max_votes = int(context.args[0])

#     await crea_sondaggino(context, update, max_votes, chiedi_opinione)


async def tweet(update: Update, context: ContextTypes.DEFAULT_TYPE, poll_passed=False) -> None:
    if await no_can_do(update, context):
        return

    MASTODON = True
    TWITTER = True

    from mastodon import Mastodon

    #   Set up Mastodon
    mastodon = Mastodon(
        access_token = 'db/mastodon.token',
        api_base_url = 'https://botsin.space/'
    )

    message = " ".join(context.args)

    if not update.message.reply_to_message and not message:
        await update.message.reply_html(f'Uso: <code>/tweet messaggio</code> oppure <code>/tweet</code> in risposta a qualcosa.')
        return

    max_votes = 4
    if update.effective_chat.id in [config.ID_TIMELINE]:
        max_votes = 6

    if not poll_passed and update.effective_user.id not in config.ADMINS:
        await crea_sondaggino(context, update, max_votes, tweet, domanda='Vogliamo veramente twittarlo?')
        return

    import tweepy
    BEARER_TOKEN = config.TW_BEARER_TOKEN
    CONSUMER_KEY = config.TW_API
    CONSUMER_SECRET = config.TW_API_SECRET
    ACCESS_KEY = config.TW_ACCESS_TOKEN
    ACCESS_SECRET = config.TW_ACCESS_TOKEN_SECRET

    # CONSUMER_KEY = config.DDF_TW_API
    # CONSUMER_SECRET = config.DDF_TW_API_SECRET
    # ACCESS_KEY = config.DDF_TW_ACCESS_TOKEN
    # ACCESS_SECRET = config.DDF_TW_ACCESS_TOKEN_SECRET

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)
    client = tweepy.Client(bearer_token=BEARER_TOKEN, access_token=ACCESS_KEY, access_token_secret=ACCESS_SECRET, consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET)



    if update.message.reply_to_message and not message:
        message = update.message.reply_to_message.text
    
    tw_url = ""
    mast_url = ""
    try:
        if update.message.reply_to_message.photo:
            if update.message.reply_to_message.caption:
                message = update.message.reply_to_message.caption
            elif not message:
                message = "beh che dire"
            else:
                message = message
            picture = update.message.reply_to_message.photo[-1]
            tempphoto = tempfile.mktemp(suffix='.jpg')
            actual_picture = await picture.get_file()
            await actual_picture.download_to_drive(custom_path=tempphoto)

            if TWITTER:
                try:
                    media = api.media_upload(tempphoto)
                    post_result = api.update_status(status=message, media_ids=[media.media_id])
                    status_id = post_result.id_str
                    tw_url = f'<a href="https://twitter.com/Emily_superbot/status/{status_id}">Twitter</a>'
                except Exception as e:
                    print(traceback.format_exc())

            if MASTODON:
                try:
                    mast_media = mastodon.media_post(tempphoto)
                    mast_response = mastodon.status_post(message, media_ids=mast_media)
                    mastodon_url = mast_response.get('url')
                    mast_url = f'<a href="{mastodon_url}">Mastodon</a>'
                except Exception as e:
                    print(traceback.format_exc())

            if tw_url or mast_url:
                await update.message.reply_html(f"Postato su {', '.join([x for x in [tw_url, mast_url] if x])}!", disable_web_page_preview=True)
                await printlog(update, "vuole inviare un tweet con una foto")

            else:
                await update.message.reply_html("Qualcosa è andato storto, scusa")
            return

        elif update.message.reply_to_message.video:
            if update.message.reply_to_message.caption:
                message = update.message.reply_to_message.caption
            elif not message:
                message = "guarda qua"
            else:
                message = message

            video = update.message.reply_to_message.video
            tempvideo = tempfile.mktemp(suffix='.mp4')
            actual_video = await video.get_file()
            await actual_video.download_to_drive(custom_path=tempvideo)

            if TWITTER:
                try:
                    media = api.media_upload(tempvideo)
                    post_result = api.update_status(status=message, media_ids=[media.media_id])
                    status_id = post_result.id_str
                    tw_url = f'<a href="https://twitter.com/Emily_superbot/status/{status_id}">Twitter</a>'
                except Exception as e:
                    print(traceback.format_exc())

            if MASTODON:
                try:
                    mast_media = mastodon.media_post(tempvideo, synchronous=True)
                    mast_response = mastodon.status_post(message, media_ids=mast_media)
                    mastodon_url = mast_response.get('url')
                    mast_url = f'<a href="{mastodon_url}">Mastodon</a>'
                except Exception as e:
                    print(traceback.format_exc())

            if tw_url or mast_url:
                await update.message.reply_html(f"Postato su {', '.join([x for x in [tw_url, mast_url] if x])}!", disable_web_page_preview=True)
                await printlog(update, "vuole inviare un tweet con un video")

            else:
                await update.message.reply_html("Qualcosa è andato storto, scusa")

            return

    except AttributeError:
        pass

    if message:
        # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} vuole inviare un tweet:\n{message}')
        await printlog(update, "vuole inviare un tweet", message)
        if len(message) > 270:
            await update.message.reply_text(f"it's too long man!")
            return

        if TWITTER:
            try:
                status = api.update_status(status=message)
                status_id = status.id_str
                tw_url = f'<a href="https://twitter.com/Emily_superbot/status/{status_id}">Twitter</a>'
            except Exception as e:
                print(traceback.format_exc())

        if MASTODON:
            try:
                mast_response = mastodon.status_post(message)
                mastodon_url = mast_response.get('url')
                mast_url = f'<a href="{mastodon_url}">Mastodon</a>'
            except Exception as e:
                print(traceback.format_exc())

        if tw_url or mast_url:
            await update.message.reply_html(f"Postato su {', '.join([x for x in [tw_url, mast_url] if x])}!", disable_web_page_preview=True)
            return
        else:
            await update.message.reply_html("Qualcosa è andato storto, scusa")
    else:
        await update.message.reply_markdown_v2(f'Uso: `/tweet messaggio`')
        return


async def lista_tweets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    import tweepy

    CONSUMER_KEY = config.TW_API
    CONSUMER_SECRET = config.TW_API_SECRET
    ACCESS_KEY = config.TW_ACCESS_TOKEN
    ACCESS_SECRET = config.TW_ACCESS_TOKEN_SECRET

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)
    screen_name = "emily_superbot"
    count = 5
    statuses = api.user_timeline(screen_name=screen_name, count=count)
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede gli ultimi {count} tweets')
    await printlog(update, f"chiede gli ultimi {count} tweets")
    message = ""
    for status in statuses:
        text = "• " + status.text + "\n"
        message = message + text
    await update.message.reply_html(f'Ultimi <a href="https://twitter.com/Emily_superbot/">tweets</a>:\n\n{message}',
                              disable_web_page_preview=True)

# Unused
async def twitter_pms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    import tweepy
    CONSUMER_KEY = config.TW_API
    CONSUMER_SECRET = config.TW_API_SECRET
    ACCESS_KEY = config.TW_ACCESS_TOKEN
    ACCESS_SECRET = config.TW_ACCESS_TOKEN_SECRET

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)

    messages = api.list_direct_messages(count=5)
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} controlla gli ultimi 5 PM di twitter')
    await printlog(update, "controlla gli ultimi 5 PM di twitter")
    tosend = ""
    for message in reversed(messages):
        # print(message)
        # who is sending?
        sender_id = message.message_create["sender_id"]
        recipient_id = message.message_create["target"]["recipient_id"]
        sender = api.get_user(sender_id)
        recipient = api.get_user(recipient_id)
        # print(sender)

        tw_sender_screen_name = sender.screen_name
        tw_recipient_screen_name = recipient.screen_name
        # what is she saying?
        text = message.message_create["message_data"]["text"]
        pm = "@" + tw_sender_screen_name + " → " + "@" + tw_recipient_screen_name + ": " + text + "\n"
        tosend = tosend + pm
    await update.message.reply_html(f'Ultimi <a href="https://twitter.com/Emily_superbot/">PM</a>:\n\n{tosend}',
                              disable_web_page_preview=True)

# Unused
async def tweet_pm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return
    import tweepy
    CONSUMER_KEY = config.TW_API
    CONSUMER_SECRET = config.TW_API_SECRET
    ACCESS_KEY = config.TW_ACCESS_TOKEN
    ACCESS_SECRET = config.TW_ACCESS_TOKEN_SECRET

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)

    message = " ".join(context.args)
    try:
        text = message.split(" ", 1)
        pm_dest = text[0]
        pm_text = text[1]
        # print(
            # f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} vuole inviare un PM su twitter a {pm_dest}: {pm_text}')
        await printlog(update, f"invia un PM su twitter a {pm_dest}", pm_text)
    except IndexError:
        await update.message.reply_text('Usa: /tweet_pm @username messaggio.')
        return
    if text[0][0] != "@":
        await update.message.reply_text(f'L\'username deve iniziare con @.')
        return
    else:
        pm_dest = pm_dest[1:]
        # print(f'User: {pm_dest}')
        user = api.get_user(pm_dest)
        recipient_id = user.id_str
        # print(f'ID: {recipient_id}')
        await printlog(update, f"invia un PM su twitter a {pm_dest}", recipient_id)
        # print(
        #     f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} vuole inviare un PM su twitter a {pm_dest}: {recipient_id}')
        try:
            api.send_direct_message(recipient_id, pm_text)
            await update.message.reply_html(f'Fatto!', disable_web_page_preview=True)
        except tweepy.TweepError as e:
            await update.message.reply_html(f"Something went wrong! {e.reason}", disable_web_page_preview=True)

