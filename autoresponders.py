# import random
# import config

# from telegram import Update
# from telegram.ext import CallbackContext, ContextTypes

# from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do

# Auto Responders
# Deprecated
# def dimmi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if no_can_do(update, context):
#         return
#     if update.effective_chat.id not in config.AUTORESPONDER:
#         return

#     frase = context.match.group(1).strip()
#     if frase == "":
#         return
#     update.message.reply_text(f'"{frase}"')
#     return

# async def cosa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if no_can_do(update, context):
#         return
#     if update.effective_chat.id in config.NOAUTORESPONDER:
#         return
#     if update.effective_chat.id == config.ID_ASPHALTO:
#         return

#     def escape(string):
#         for c in ["-"]:
#             if c in string:
#                 string = string.replace("-", "\-")  # –
#         return string

#     print(f'{get_now()} {await get_display_name(update.effective_user)} in {get_chat_name(update.message.chat.id)} ma che sei sordo??')
#     if update.message.from_user.id == 208435168:
#         update.message.reply_markdown_v2(f'Basta aurora', quote=True)
#         return
#     try:
#         messaggio_originale = update.message.reply_to_message.text
#         if messaggio_originale.isupper():
#             newmessage = f'<b>{messaggio_originale}</b>'
#         else:
#             newmessage = messaggio_originale.upper()
#         # print(newmessage)
#         update.message.reply_html(f'{newmessage}', quote=True)
#     except AttributeError:
#         print(f'{get_now()} {await get_display_name(update.effective_user)} in {get_chat_name(update.message.chat.id)} è sordo, ma parla da solo.')

# async def saichi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if await no_can_do(update, context):
#         return
#     if update.effective_chat.id not in config.NOAUTORESPONDER:
#         return
#     print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} triggera SAI CHI?')


#     if update.message.chat.id == config.ID_RITALY:
#         listamadri = ['Trifase', 'ddf', 'Jules', 'delma', 'fabri', 'mauro magi', 'giulia', 'jacopo', 'pastina', 'nico',
#                       'faggin', 'marcog', 'mario', 'drpeace', 'bertoldi', 'alupeto', 'lita', 'misspesca', 'crisbal',
#                       'mariarita', 'asaggese', 'cazo', 'izabera', 'denvit', 'alessia', 'danielina']

#     elif update.message.chat.id == config.ID_DIOCHAN:
#         listamadri = ['Trifase', 'sushi', 'Stefano', 'Gesù', 'touchdown', 'exe', 'MadAdam', 'mainde', 'Porvora', 'fry',
#                       'draw', 'manu', 'nrz']

#     elif update.message.chat.id == config.ID_ASPHALTO:
#         listamadri = ['Trifase', 'Nicola', 'Franti', 'Idio', 'Pacciani', 'Fra', 'Floriana', 'Rebis', 'Louis', 'Clio', 'Dulcamara', 'Supermaz', 'Leonardo', 'Elvis', 'Stocazzo']

#     else:
#         listamadri = ['Trifase']

#     if random.randint(0, 100) < 50:
#         madre_scelta = random.choice(listamadri)
#         update.message.reply_text(f'la madre di {madre_scelta}')
#     else:
#         update.message.reply_text(f'tua madre')

# async def particellachi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if await no_can_do(update, context):
#         return
#     if update.effective_chat.id not in config.NOAUTORESPONDER:
#         return
#     prepo = context.match.group(1).lower()

#     print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} triggera {prepo.upper()} CHI?')

#     if update.message.chat.id == config.ID_RITALY:
#         listaamadri = ['Trifase', 'ddf', 'Jules', 'delma', 'fabri', 'mauro magi', 'giulia', 'jacopo', 'pastina', 'nico',
#                        'faggin', 'marcog', 'mario', 'drpeace', 'bertoldi', 'alupeto', 'lita', 'misspesca', 'crisbal',
#                        'mariarita', 'asaggese', 'cazo', 'izabera', 'denvit', 'alessia', 'danielina']

#     elif update.message.chat.id == config.ID_DIOCHAN:
#         listaamadri = ['Trifase', 'sushi', 'Stefano', 'Gesù', 'touchdown', 'exe', 'MadAdam', 'mainde', 'Porvora', 'fry',
#                        'draw', 'manu', 'nrz']

#     elif update.message.chat.id == config.ID_ASPHALTO:
#         listaamadri = ['Trifase', 'Nicola', 'Franti', 'Idio', 'Pacciani', 'Fra', 'Floriana', 'Rebis', 'Louis', 'Clio', 'Dulcamara', 'Supermaz', 'Leonardo', 'Elvis', 'Stocazzo']

#     else:
#         listaamadri = ['Trifase']

#     if random.randint(0, 100) < 50:
#         madre_ascelta = random.choice(listaamadri)
#         if prepo == 'di':
#             update.message.reply_text(f'della madre di {madre_ascelta}')
#         elif prepo == 'a':
#             update.message.reply_text(f'alla madre di {madre_ascelta}')
#         elif prepo == 'da':
#             update.message.reply_text(f'dalla madre di {madre_ascelta}')
#         elif prepo == 'in':
#             update.message.reply_text(f'nella madre di {madre_ascelta}')
#         elif prepo == 'su':
#             update.message.reply_text(f'sulla madre di {madre_ascelta}')
#         else:
#             update.message.reply_text(f'{prepo} la madre di {madre_ascelta}')
#     else:
#         update.message.reply_text(f'{prepo} tua madre')

# def quanto(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.effective_chat.id in config.NOAUTORESPONDER:
#         return
#     num = random.randint(1, 1500)
#     risp = random.choice(["", "Almeno ", "Credo che la cifra esatta sia ", "Più di ", "Meno di ", "Esattamente "])
#     update.message.reply_text(f'{risp}{num}.', quote=False)
#     return
