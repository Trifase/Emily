import subprocess
import tempfile
import urllib.request
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from utils import no_can_do, printlog


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
        subprocess.check_call(command) #nosec

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
    urllib.request.urlretrieve(url, "templates/motivational_poster.jpg") #nosec

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
            pass
    with tempfile.TemporaryDirectory() as tmp_dir:
        photo = make_photo(text, nickname, Path(tmp_dir))
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo.open('rb'))

async def change_my_mind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return

    def make_photo(text: str, destination_dir: Path) -> Path:
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

