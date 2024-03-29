import traceback

from telegram.ext import ContextTypes

import config
from utils import printlog


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    await printlog(update, f"{tb_string}", error=True)

    await context.bot.send_message(
        chat_id=config.ID_BOTCENTRAL,
        text=f'<pre><code class="language-python">{tb_string[:4000]}</code></pre>',
        parse_mode="HTML",
    )
