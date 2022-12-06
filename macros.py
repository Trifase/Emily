import random
import tempfile
import subprocess

from telegram import Update
from telegram.ext import CallbackContext, ContextTypes
from rich import print
from pathlib import Path
import urllib.request
import config
import PIL


from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do

# Inspirational
async def ispirami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return

    def make_photo(text: str, nickname: str, destination_dir: Path) -> Path:
        template_photo = "templates/motivational_poster.jpg"
        font_file = "fonts/Vollkorn-Italic.ttf"
        darken_file = "templates/darken.png"
        destination_photo = Path("images/motivational_poster.png")
        size = 42
        if len(text) > 400:
            size = 26
        elif len(text) > 300:
            size = 32
        elif len(text) > 200:
            size = 36

        text = text.replace("&", "\&amp;")
        nickname = nickname.replace("&", "\&amp;")
        command = [
            "convert",
            "(",
            str(template_photo),
            str(darken_file),
            "-flatten",
            ")",
            "(",
            "-gravity", "center",
            # "-size", "760x560",
            "-font", str(font_file),
            "-pointsize", str(size),
            "-background", "none",
            # "-stroke", "#000",
            "-fill", "#fff",
            "-size", "760",
            f'pango:<span font_family="Vollkorn" style="italic" size="{size * 600}">“{text}”</span>',
            "+repage",
            ")",
            "(",
            "-clone", "1",
            "-background", "black",
            "-shadow", "100x2+2+2",
            ")",
            "(",
            "-clone", "1",
            "-clone", "2",
            "+swap", 
            "-background", "none",
            "-layers", "merge",
            "+repage",
            ")", 
            "-delete", "1,2",
            "-gravity", "center",
            "-geometry", "+0-50",
            "-compose", "over",
            "-composite",  # fine
            "(",
            "-gravity", "SouthEast",
            "-size", "760",
            "-font", str(font_file),
            "-pointsize", str(size),
            "-background", "none",
            "-fill", "#fff",
            f'pango:<span font_family="Vollkorn" style="italic" size="{size * 600}"> - {nickname}</span>',
            "+repage",
            ")",
            "(",
            "-clone", "1",
            "-background", "black",
            "-shadow", "100x2+2+2",
            ")",
            "(",
            "-clone", "1",
            "-clone", "2",
            "+swap", 
            "-background", "none",
            "-layers", "merge",
            "+repage",
            ")", 
            "-delete", "1,2",
            "-gravity", "SouthEast",
            "-geometry", "+20+0",
            "-compose", "over",
            # "-geometry", "+455+777",
            # "-compose", "Multiply",
            "-composite",  # fine
            str(destination_photo)
        ]
        subprocess.check_call(command)

        return destination_photo
    if not update.message.reply_to_message:
        return
    else:
        if not update.message.reply_to_message.text:
            await update.message.reply_text("Non c'è nessun testo.")
            return

    text = update.message.reply_to_message.text

    if len(text) > 700:
        await update.message.reply_text("It's too long man!")
        return
    chars = ("q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "a", "s", "d", "f", "g", "h", "j", "k", "l", "z", "x", "c", "v", "b", "n", "m", "è", "é", "ò", "à", "ù", "ì")
    text = text[0].upper() + text[1:]
    if text.lower().endswith(chars):
        text += "."
    url = "https://picsum.photos/800/600"
    urllib.request.urlretrieve(url, "templates/motivational_poster.jpg")

    first_name = ""
    last_name = ""
    username = ""
    if update.message.reply_to_message.forward_date:  # è un forward
        try:
            first_name = update.message.reply_to_message.forward_from.first_name
            last_name = update.message.reply_to_message.forward_from.last_name
            username = update.message.reply_to_message.forward_from.username
            if first_name and last_name:
                nickname = f"{first_name} {last_name}"
            elif first_name and not last_name:
                nickname = first_name 
            else:
                nickname = f"@{username}"

        except AttributeError:  # Privacy Forward
            nickname = update.message.reply_to_message.forward_sender_name

        if nickname:
            nickname += f", {update.message.reply_to_message.forward_date.strftime('%-d %B %Y')}"
        else:
            nickname = f"Anonimo, {update.message.reply_to_message.forward_date.strftime('%-d %B %Y')}"
    else:
        first_name = update.message.reply_to_message.from_user.first_name
        last_name = update.message.reply_to_message.from_user.last_name
        username = update.message.reply_to_message.from_user.username
        if first_name and last_name:
            nickname = f"{first_name} {last_name}"
        elif first_name and not last_name:
            nickname = first_name 
        else:
            nickname = f"@{username}"
        nickname += f", {update.message.reply_to_message.date.strftime('%-d %B %Y')}"

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} fa un poster motivazionale')
    await printlog(update, "fa un poster motivazionale")
    if context.args:
        if context.args[0] in ["-a", "-anonimo", "-anon"]:
            anonimi = [
                "Anonimo",
                ""
            ]
    with tempfile.TemporaryDirectory() as tmp_dir:
        photo = make_photo(text, nickname, Path(tmp_dir))
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo.open('rb'))

async def change_my_mind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return

    def make_photo(text: str, destination_dir: Path) -> Path:
        THIS_DIR = Path(__file__).parent
        template_photo = "templates/changemymind.jpg"
        font_file = "fonts/calibri.ttf"
        destination_photo = destination_dir / "changemymind.jpg"
        command = [
            "convert",
            str(template_photo),
            "(",
            "-size", "650x290!",
            "-font", str(font_file),
            "-background", "none",
            "-fill", "#222222",
            f"caption:{text}",
            "-rotate", "337",
            # "+distort", "perspective", "0,0 10,0 0,290 115,254 666,290 691,-94 666,0 625,-155",
            ")",
            "-geometry", "+910+700",
            "-compose", "Multiply",
            "-composite",
            str(destination_photo)
        ]
        subprocess.check_call(command)
        return destination_photo
    if not context.args:
        return

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} fa un poster motivazionale')
    await printlog(update, "fa un change my mind")

    # text = ' '.join(context.args)
    text = update.message.text[14:]
    if len(text) > 200:
        await update.message.reply_text("It's too long man!")
        return
    with tempfile.TemporaryDirectory() as tmp_dir:
        photo = make_photo(text, Path(tmp_dir))
        await update.message.reply_photo(photo=photo.open('rb'))


# # Images
# def salvimuro(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if no_can_do(update, context):
#         return

#     def make_photo(text: str, destination_dir: Path) -> Path:
#         THIS_DIR = Path(__file__).parent
#         template_photo = "templates/salvini-template.jpg"
#         # font_file = THIS_DIR / "Spray Letters.otf"
#         font_file = "fonts/Graffiti City.otf"
#         destination_photo = destination_dir / "salvini.png"
#         command = [
#             "convert",
#             str(template_photo),
#             "(",
#             "-size", "580x320!",
#             "-font", str(font_file),
#             "-background", "none",
#             "-fill", "#06080fee",
#             f"caption:{text}",
#             "+distort", "perspective", "0,0 0,0 0,320 9,314 580,320 571,355 580,0 594,-30",
#             ")",
#             "-geometry", "+511+200",
#             "-compose", "Multiply",
#             "-composite",
#             str(destination_photo)
#         ]
#         # print(" ".join(command))
#         subprocess.check_call(command)
#         return destination_photo
#     if not context.args:
#         return
#     print(f'{get_now()} {await get_display_name(update.effective_user)} in {get_chat(update.message.chat.id)} fa un salvingraffito')
#     text = ' '.join(context.args)
#     if len(text) > 100:
#         update.message.reply_text("It's too long man!")
#         return
#     with tempfile.TemporaryDirectory() as tmp_dir:
#         photo = make_photo(text, Path(tmp_dir))
#         context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo.open('rb'))

# def striscione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if no_can_do(update, context):
#         return
#     from PIL import Image, ImageFont, ImageDraw
#     string = " ".join(context.args)
#     string = string.upper()
#     print(f'{get_now()} {await get_display_name(update.effective_user)} in {get_chat(update.message.chat.id)} protesta con uno striscione')
#     if string == "":
#         string = random.choice([
#             "I PADRONI DEI CANI|SONO PEGGIO DEI CANI",
#             "GENITORE UNO|GENITORE DUE",
#             "SE CI SEI | BATTI UN COLPO", 
#             "LA ZOMPAPERETA | E MAMMET", 
#             "SCRIVI UN MESSAGGIO SCEMO", 
#             "for c in string | print(c)"
#         ])

#     if "|" in string:
#         single_line = False
#         lines = string.split("|", maxsplit=1)
#         string1 = lines[0]
#         string2 = lines[1]
#     else:
#         single_line = True

#     font_size = 85 if single_line else 45
#     font = ImageFont.truetype('fonts/ultrasliberi.ttf', font_size)
#     text_max_size = 580

#     if single_line:
#         text_w, text_h = font.getsize(string)
#     else:
#         text_w1, text_h1 = font.getsize(string1)
#         text_w2, text_h2 = font.getsize(string2)
#         text_w = max(text_w1, text_w2)
#     box_w = text_w + 10
#     box_h = 95
#     img_text = Image.new('RGBA', (box_w, box_h), (255, 0, 0, 0))
#     draw = ImageDraw.Draw(img_text)
#     red = (180, 10, 10)

#     if single_line:
#         draw.text((5, 0), string, font=font, fill=red)
#     else:
#         draw.text(((box_w - text_w1) / 2, 0), string1, font=font, fill=red)
#         draw.text(((box_w - text_w2) / 2, 50), string2, font=font, fill=red)
#     background = Image.open('templates/striscione.jpg', 'r')
#     if text_w > 2000:
#         update.message.reply_text("It's too long man!")
#         return
#     elif text_w > 580 and text_w < 2000:
#         resized_img_text = img_text.resize((text_max_size, 95))
#         background.paste(resized_img_text, (int((625 + 45 - text_max_size) / 2), 225), resized_img_text)
#     else:
#         background.paste(img_text, (int((625 - text_w) / 2), 225), img_text)
#     tempphoto = tempfile.mktemp(suffix='.jpg')
#     background.save(tempphoto, "PNG")
#     update.message.reply_photo(open(tempphoto, 'rb'))

# def playlover(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if no_can_do(update, context):
#         return

#     def make_photo(text: str, destination_dir: Path) -> Path:
#         THIS_DIR = Path(__file__).parent
#         template_photo = "templates/playlover-template.jpg"
#         font_file = "fonts/ARIAL.ttf"
#         destination_photo = destination_dir / "playlover.png"
#         command = [
#             "convert",
#             str(template_photo),
#             "(",
#             "-gravity", "North",
#             "-size", "470x200",
#             "-font", str(font_file),
#             "-background", "none",
#             "-fill", "#677680",
#             "-pointsize", "30",
#             f"caption:{text}",
#             "-blur", "3",
#             "-rotate", "359.5",
#             ")",
#             "-geometry", "+0+180",
#             "-compose", "Multiply",
#             "-composite",
#             str(destination_photo)
#         ]
#         subprocess.check_call(command)
#         return destination_photo
#     if not context.args:
#         return
#     try:
#         print(f'{get_now()} {await get_display_name(update.effective_user)} in [yellow1]{update.effective_chat.title[:10]}[/yellow1] ({str(update.message.chat.id)[4:]}) fa una slide di playlover')
#     except TypeError:
#         print(f'{get_now()} Qualcuno ({update.effective_user.username}) fa una slide di playlover in privato')
#     # text = ' '.join(context.args)
#     text = update.message.text[11:]
#     if len(text) > 200:
#         update.message.reply_text("It's too long man!")
#         return
#     with tempfile.TemporaryDirectory() as tmp_dir:
#         photo = make_photo(text, Path(tmp_dir))
#         update.message.reply_photo(photo=photo.open('rb'))

# def cartello(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if no_can_do(update, context):
#         return

#     def make_photo(text: str, destination_dir: Path) -> Path:
#         THIS_DIR = Path(__file__).parent
#         template_photo = "templates/template_cartello.jpg"
#         font_file = "fonts/cartello-CHARLY.ttf"
#         destination_photo = destination_dir / "cartello.jpg"
#         command = [
#             "convert",
#             str(template_photo),
#             "(",
#             "-size", "480x280!",
#             "-font", str(font_file),
#             "-background", "none",
#             "-fill", "#06080fee",
#             f"caption:{text}",
#             "+distort", "perspective", "0,0 0,0 0,270 0,270 480,270 460,350 480,0 480,-15",
#             "-blur", "0.2x0.5",
#             ")",
#             "-geometry", "+620+300",
#             "-compose", "Multiply",
#             "-composite",
#             str(destination_photo)
#         ]
#         subprocess.check_call(command)
#         return destination_photo
#     if not context.args:
#         return
#     try:
#         print(f'{get_now()} {await get_display_name(update.effective_user)} in [yellow1]{update.effective_chat.title[:10]}[/yellow1] ({str(update.message.chat.id)[4:]}) fa un cartello!')
#     except TypeError:
#         print(f'{get_now()} Qualcuno ({update.effective_user.username}) fa un cartello in privato')
#     text = ' '.join(context.args)
#     if len(text) > 200:
#         update.message.reply_text("It's too long man!")
#         return
#     with tempfile.TemporaryDirectory() as tmp_dir:
#         photo = make_photo(text, Path(tmp_dir))
#         update.message.reply_photo(photo=photo.open('rb'))

# def salvifoglio(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if no_can_do(update, context):
#         return

#     def make_photo(text: str, destination_dir: Path) -> Path:
#         THIS_DIR = Path(__file__).parent
#         template_photo = "templates/salvifoglio.jpg"
#         font_file = "fonts/calibri.ttf"
#         destination_photo = destination_dir / "salvifoglio.jpg"
#         command = [
#             "convert",
#             str(template_photo),
#             "(",
#             "-size", "730x500!",
#             "-font", str(font_file),
#             "-background", "none",
#             "-fill", "#040405",
#             f"caption:{text}",
#             "+distort", "perspective", "0,0 0,0 0,500 0,524 730,500 730,500 730,0 730,0",
#             ")",
#             "-geometry", "+455+777",
#             "-compose", "Multiply",
#             "-composite",
#             str(destination_photo)
#         ]
#         subprocess.check_call(command)
#         return destination_photo
#     if not context.args:
#         return
#     try:
#         print(f'{get_now()} {await get_display_name(update.effective_user)} in [yellow1]{update.effective_chat.title[:10]}[/yellow1] ({str(update.message.chat.id)[4:]}) fa un salvini-foglio')
#     except TypeError:
#         print(f'{get_now()} Qualcuno ({update.effective_user.username}) fa un salvini-foglio in privato')
#     text = update.message.text[13:]
#     if len(text) > 500:
#         update.message.reply_text("It's too long man!")
#         return
#     with tempfile.TemporaryDirectory() as tmp_dir:
#         photo = make_photo(text, Path(tmp_dir))
#         update.message.reply_photo(photo=photo.open('rb'))
#         # context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo.open('rb'))
