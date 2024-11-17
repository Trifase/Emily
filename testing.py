import pprint
import time
import asyncio
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from utils import printlog
from atproto import AsyncClient, client_utils
import config


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s = time.time()
    start = time.perf_counter()
    m = await update.message.reply_html("Test fallito.")
    await m.edit_text(f"[{s}] Test fallito in {round((time.perf_counter() - start) * 1000)}ms")

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} testa tantissimo!')
    await printlog(update, "testa tantissimo")

    await update.message.set_reaction(reaction='👌')
    # await react_to_message(update, context, update.effective_chat.id, update.effective_message.id, "👌", True)
    # im = ImageGrab.grab()
    # tempphoto = tempfile.NamedTemporaryFile(suffix='.jpg')
    # im.save(tempphoto.name, quality=100, subsampling=0)
    # await update.message.reply_photo(photo=open(tempphoto.name, "rb"))
    # await update.message.reply_document(document=open(tempphoto.name, "rb"))

    # invite_link = await context.bot.create_chat_invite_link(update.message.chat.id, member_limit=1, name='something')
    # print(invite_link.to_json())

    # print(update.to_json())
    # print()
    # user = await context.bot.get_chat_member(update.message.chat.id, update.effective_user.id)
    # print(user.to_json())

    # await alert(update, context, "ha testato tantissimo", "errore di prova")

    # pprint.pprint(sys.modules['space'])


async def getfile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    picture = update.message.reply_to_message.photo[-1]
    actual_picture = await picture.get_file()
    pprint.pprint(actual_picture.to_dict())


# async def main():
#     # Set up Bluesky
#     bluesky = AsyncClient()
#     await bluesky.login(config.BS_HANDLE, config.BS_PASS)

#     message = 'yo we rollin 2'
#     post = await bluesky.send_post(text=message)
#     print(post.model_dump_json())
#     bs_post_id = post.uri.split('/')[-1]
#     bs_post_id = f'https://bsky.app/profile/{config.BS_HANDLE}/post/{bs_post_id}'
#     bluesky_url = f'https://bsky.app/profile/{config.BS_HANDLE}/post/{bs_post_id}'
#     bs_url = f'<a href="{bluesky_url}">Bluesky</a>'

#     try:
#         message = 'this is fire yo'
#         with open('test.png', 'rb') as f:
#             img_data = f.read()
#         bs_response = await bluesky.send_image(text=message, image=img_data, image_alt=message)
#         print('Post reference:', bs_response)
#         bs_post_id = bs_response.uri.split('/')[-1]
#         bluesky_url = f'https://bsky.app/profile/{config.BS_HANDLE}/post/{bs_post_id}'
#         bs_url = f'<a href="{bluesky_url}">Bluesky</a>'

#         # bs_url = f'<a href="{bs_response.get("url")}">Bluesky</a>'
#     except Exception:
#         print(traceback.format_exc())


#     try:
#         message = 'this is fire yo'
#         with open('test.png', 'rb') as f:
#             vid_data = f.read()
#         bs_response = await bluesky.send_video(text=message, video=vid_data, video_alt=message)
#         print('Post reference:', bs_response)
#         bs_post_id = bs_response.uri.split('/')[-1]
#         bluesky_url = f'https://bsky.app/profile/{config.BS_HANDLE}/post/{bs_post_id}'
#         bs_url = f'<a href="{bluesky_url}">Bluesky</a>'

#         # bs_url = f'<a href="{bs_response.get("url")}">Bluesky</a>'
#     except Exception:
#         print(traceback.format_exc())


# # run main in async
# asyncio.run(main())