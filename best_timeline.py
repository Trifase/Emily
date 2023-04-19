import datetime
import random

from telegram import ChatMember, ChatPermissions, InputMediaPhoto, InputMediaVideo, Update
from telegram.ext import ContextTypes

import config
from utils import get_display_name, no_can_do, printlog


async def scrape_tweet_bt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if (update.message.sender_chat.id == config.ID_BT_CHAN): # or (update.message.chat.id == config.ID_TESTING):
            # print(f'{get_now()} [deep_pink3]{update.message.sender_chat.title}[/deep_pink3] in {await get_chat_name(update.message.chat.id)} posta un tweet: {context.match.group(1)}')
            await printlog(update, "posta un tweet su BT", context.match.group(1))
            pass
        else:
            return
    except AttributeError:
        # if update.message.chat.id == config.ID_TESTING:
        #     print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} posta un tweet: {context.match.group(1)}')
        # else:
        #     return
        return

    import tweepy
    CONSUMER_KEY = config.TW_API
    CONSUMER_SECRET = config.TW_API_SECRET
    ACCESS_KEY = config.TW_ACCESS_TOKEN
    ACCESS_SECRET = config.TW_ACCESS_TOKEN_SECRET

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)
    tw_id = [context.match.group(1)]


    my_tweet = api.lookup_statuses(tw_id, tweet_mode='extended')
    try:
        t = my_tweet[0]
    except IndexError:
        await update.message.reply_html("Tweet non trovato.")
        return

    # print(my_tweet[0]._json)
    try:
        text = t.full_text
        text = text.split('\n\nhttps://t.co/')[0]
        text += "\n"
    except AttributeError:
        text = ""

    name = t.user.screen_name
    url = f"https://twitter.com/{name}/status/{t.id}"

    try:
        text_url = t.entities.urls[0]['expanded_url']
        text_url += "\n"
    except (AttributeError, IndexError):
        text_url = ""
    nitter_instances = [
        "nitter.net",
        "nitter.it",
        "nitter.nl",
        "nitter.cz"
    ]
    nitter_url = url.replace("twitter.com",random.choice(nitter_instances))
    caption = f"<a href='{url}'>@{name}</a>\n{text if text else ''}{text_url if text_url else ''}\n<a href='{nitter_url}'>[Nitter]</a>"
    try:
        medialist = t.extended_entities.get('media', [])
    except AttributeError:
        medialist = []

    medias = []
    if medialist:
        i = 0
        for media in medialist:
            if media.get('type') == 'photo':
                media_url = media.get('media_url')
                medias.append(InputMediaPhoto(media=media_url, caption=caption if i == 0 else '', parse_mode='HTML'))
                i += 1
            elif media.get('type') == 'video':
                media_url = media.get('video_info').get('variants')[0].get('url')
                medias.append(InputMediaVideo(media=media_url, caption=caption if i == 0 else '', parse_mode='HTML'))
                i += 1

        
        await context.bot.send_media_group(reply_to_message_id=update.message.message_id, chat_id=update.message.chat.id, media=medias)
    else:
        await update.message.reply_html(caption, disable_web_page_preview=True)

async def silenzia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def can_user_restrict(user: ChatMember):
        if user.status == ChatMember.OWNER:
            return True
        elif user.status == ChatMember.ADMINISTRATOR and user.can_restrict_members:
            return True
        else:
            return False


    if await no_can_do(update, context):
        return

    if not update.message.reply_to_message:
        return
    
    if not context.args:
        minutes = 30
    else:
        try:
            minutes = int(context.args[0])
        except Exception:
            minutes = 30

    user = await update.message.chat.get_member(update.message.from_user.id)

    chi = update.message.reply_to_message.from_user
    victim_name = await get_display_name(chi, tolog=True)

    if not can_user_restrict(user) and update.effective_user.id != config.ID_TRIF:
        return
    await printlog(update, f"silenzia per {minutes} minuti", f"{victim_name}")

    expires_in = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    sta_zitto = ChatPermissions.no_permissions()
    await context.bot.restrict_chat_member(update.message.chat.id, update.message.reply_to_message.from_user.id, until_date=expires_in, permissions=sta_zitto)
    await update.message.reply_html(f"Silenziatə fino al <code>{expires_in}</code>", reply_to_message_id=update.message.reply_to_message.id)


async def permasilenzia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def can_user_restrict(user: ChatMember):
        if user.status == ChatMember.OWNER:
            return True
        elif user.status == ChatMember.ADMINISTRATOR and user.can_restrict_members:
            return True
        else:
            return False


    if await no_can_do(update, context):
        return

    if not update.message.reply_to_message:
        return
    
    user = await update.message.chat.get_member(update.message.from_user.id)

    chi = update.message.reply_to_message.from_user
    victim_name = await get_display_name(chi, tolog=True)

    if not can_user_restrict(user) and update.effective_user.id != config.ID_TRIF:
        return
    await printlog(update, "silenzia per sempre", f"{victim_name}")

    sta_zitto = ChatPermissions.no_permissions()
    await context.bot.restrict_chat_member(update.message.chat.id, update.message.reply_to_message.from_user.id, permissions=sta_zitto)
    await update.message.reply_html("Silenziatə fino al <code>decadimento termico dell'universo</code>", reply_to_message_id=update.message.reply_to_message.id)


async def deleta_if_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # if update.message.chat.id != config.ID_TIMELINE:
    #     return
    # if update.message.from_user.id == 136817688: # fake user TG sends when commenting as a chan
    #     # await update.message.delete()
    #     await send_reaction(update.message.chat_id, update.message.message_id, "👎")
    #     await printlog(update, "commenta come un canale")
    return