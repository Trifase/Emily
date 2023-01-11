import deepl
import json
import pyaztro
import random
from PIL import Image
import pprint
import random
import tempfile
import subprocess
import tempfile

from telegram import Update
from telegram.ext import CallbackContext, ContextTypes
from rich import print
from pathlib import Path
import urllib.request
import config
import PIL
import argparse


from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do

class ArgumentParser(argparse.ArgumentParser):
    """
    The default (and only) argparse behavior is to throw error to sys.stderr via the error method.
    """

    def error(self, message):
        raise ParserError(message)

class ParserError(Exception): pass



def spezza(mazzo):
    n = random.randint(1, 20)
    return mazzo[n:] + mazzo[:n]


def italian_shuffle(mazzo):
    n = random.randint(9, 13)
    a = mazzo[:n]
    b = mazzo[n:]
    c = []

    while a and b:
        if a:
            if random.random() < 0.5:
                c.append(a.pop(0))
        if b:
            if random.random() < 0.5:
                c.append(b.pop(0))
    c += a
    c += b
    return c

def get_piles(mazzo, n_piles):
    piles = []
    cuts = []
    max_len = len(mazzo)
    average_pile = round(max_len/n_piles)
    average_error = round(max_len * 0.10)
    for i in range(n_piles-1):
        cuts.append(random.randint(average_pile - average_error, average_pile + average_error))
    cuts.append(max_len - sum(cuts))
    # print(cuts)
    s = 0
    for limit in cuts:
        piles.append(mazzo[s:s+limit])
        s = s + limit
    return piles

def mischia(mazzo, shuffle=True, n_piles=3, repetition_piles=3, reverse=True, reverse_percentage=0.3):
    # https://lucid.app/lucidchart/d18e73db-743f-4461-96ff-45bb06a3e652/edit?viewport_loc=-469%2C140%2C2219%2C1052%2C0_0&invitationId=inv_2b1ae4d3-75c4-4ee6-ba46-2a55182a746d#
    # print("inizio")
    # pprint.pprint(mazzo)
    if shuffle:
        # random.shuffle(mazzo)
        mazzo = italian_shuffle(mazzo)
        mazzo = italian_shuffle(mazzo)

    # print("shuffle 1")
    # pprint.pprint(mazzo)

    for _ in range(repetition_piles):
        # print(f"Divisione in piles ed eventuale flip, iterazione {n+1}")
        piles = get_piles(mazzo, n_piles=n_piles)
        # pprint.pprint(piles)
        if reverse:
            if random.random() < reverse_percentage:
                # print("Reverso una pila")
                pile_to_flip = piles.pop(random.randint(0, n_piles-1))
                for card in pile_to_flip:
                    card['reverse'] = not card['reverse']
                piles.append(pile_to_flip)
        # print("finito di fare le piles")
        # pprint.pprint(piles)
        # print("mischio le piles")
        random.shuffle(piles)
        # pprint.pprint(piles)
        # print("unisco il mazzo")
        mazzo = []
        for pile in piles:
            for card in pile:
                mazzo.append(card)
        # pprint.pprint(mazzo)
    # print("shuffle 2")
    if shuffle:
        # random.shuffle(mazzo)
        mazzo = italian_shuffle(mazzo)
        mazzo = italian_shuffle(mazzo)
    # pprint.pprint(mazzo)
    # print("spacco")
    mazzo = spezza(mazzo)
    return mazzo

def get_default_deck():
    mazzo = []
    for c in range(0, 22):
        mazzo.append({"n": c, "reverse": False})
    return mazzo

async def get_spread(spread_name='default_three'):
    # dimensioni tipiche tarocco: 263x450
    # dimensioni tipiche bg: 1280x1280

    if spread_name == 'default_three':
        spread = {
            'name': 'Lettura a tre carte',
            'total_cards': 3,
            'need_resize': False,
            'card_size': (263, 450),

            0: {
                'pos': (100, 415),
                'rot': 0
            },

            1: {
                'pos': (510, 415),
                'rot': 0
            },

            2: {
                'pos': (920, 415),
                'rot': 0
            }
        }

    elif spread_name == 'simple_cross':
        spread = {
            'name': 'Croce Semplice',
            'total_cards': 5,
            'need_resize': True,
            'card_size': (230, 394),
            0: {
                'pos': (540, 445),
                'rot': 0
            },

            1: {
                'pos': (210, 445),
                'rot': 0
            },

            2: {
                'pos': (870, 445),
                'rot': 0
            },

            3: {
                'pos': (540, 840),
                'rot': 0
            },

            4: {
                'pos': (540, 50),
                'rot': 0
            }

        }

    elif spread_name == 'mondo':
        spread = {
            'name': 'Tarocchi del Mondo',
            'total_cards': 5,
            'need_resize': False,
            'card_size': (263, 450),
            0: {
                'pos': (509, 415),
                'rot': 0
            },

            1: {
                'pos': (826, 48),
                'rot': 0
            },

            2: {
                'pos': (192, 48),
                'rot': 0
            },

            3: {
                'pos': (826, 766),
                'rot': 0
            },

            4: {
                'pos': (192, 766),
                'rot': 0
            }

        }

    elif spread_name == 'scelta':
        spread = {
            'name': 'Tarocchi della scelta',
            'total_cards': 7,
            'need_resize': True,
            'card_size': (217, 371),
            0: {
                'pos': (532, 56),
                'rot': 0
            },

            1: {
                'pos': (189, 453),
                'rot': 0
            },

            2: {
                'pos': (867, 453),
                'rot': 0
            },

            3: {
                'pos': (80, 838),
                'rot': 0
            },

            4: {
                'pos': (305, 838),
                'rot': 0
            },

            5: {
                'pos': (758, 838),
                'rot': 0
            },

            6: {
                'pos': (983, 838),
                'rot': 0
            }

        }

    elif spread_name == 'wirth':
        spread = {
            'name': 'Croce di Wirth modificata',
            'total_cards': 6,
            'need_resize': True,
            'card_size': (230, 394),


            0: {
                'pos': (890, 445),
                'rot': 0
            },

            1: {
                'pos': (190, 445),
                'rot': 0
            },

            2: {
                'pos': (540, 20),
                'rot': 0
            },

            3: {
                'pos': (540, 870),
                'rot': 0
            },

            4: {
                'pos': (540, 445),
                'rot': 0
            },

            5: {
                'pos': (458, 527),
                'rot': 90
            }

        }

    elif spread_name == 'year':
        # 1    2    3   13
        # 4    5    6   14
        # 7    8    9   15
        # 10   11   12  16

        spread = {
            'name': 'Lettura annuale',
            'total_cards': 16,
            'need_resize': True,
            'card_size': (158, 270),

            0: {
                'pos': (192, 85),
                'rot': 0
            },

            1: {
                'pos': (377, 85),
                'rot': 0
            },

            2: {
                'pos': (561, 85),
                'rot': 0
            },

            3: {
                'pos': (192, 365),
                'rot': 0
            },

            4: {
                'pos': (377, 365),
                'rot': 0
            },

            5: {
                'pos': (561, 365),
                'rot': 0
            },

            6: {
                'pos': (193, 645),
                'rot': 0
            },

            7: {
                'pos': (377, 645),
                'rot': 0
            },

            8: {
                'pos': (561, 645),
                'rot': 0
            },

            9: {
                'pos': (193, 925 ),
                'rot': 0
            },

            10: {
                'pos': (377, 925 ),
                'rot': 0
            },

            11: {
                'pos': (561, 925 ),
                'rot': 0
            },

            12: {
                'pos': (929, 85),
                'rot': 0
            },

            13: {
                'pos': (929, 365),
                'rot': 0
            },

            14: {
                'pos': (929, 645),
                'rot': 0
            },

            15: {
                'pos': (929, 925),
                'rot': 0
            },
        }

    elif spread_name == 'full':

        spread = {
            'name': 'Deck Showcase',
            'total_cards': 22,
            'need_resize': True,
            'card_size': (172, 294),

            0: {
                'pos': (554, 22),
                'rot': 0
            },

            1: {
                'pos': (10, 331),
                'rot': 0
            },

            2: {
                'pos': (191, 331),
                'rot': 0
            },

            3: {
                'pos': (373, 331),
                'rot': 0
            },

            4: {
                'pos': (554, 331),
                'rot': 0
            },

            5: {
                'pos': (735, 331),
                'rot': 0
            },

            6: {
                'pos': (917, 331),
                'rot': 0
            },

            7: {
                'pos': (1098, 331),
                'rot': 0
            },

            8: {
                'pos': (10, 640),
                'rot': 0
            },

            9: {
                'pos': (191, 640),
                'rot': 0
            },

            10: {
                'pos': (373, 640),
                'rot': 0
            },

            11: {
                'pos': (554, 640),
                'rot': 0
            },

            12: {
                'pos': (735, 640),
                'rot': 0
            },

            13: {
                'pos': (917, 640),
                'rot': 0
            },

            14: {
                'pos': (1098, 640),
                'rot': 0
            },

            15: {
                'pos': (10, 949),
                'rot': 0
            },

            16: {
                'pos': (191, 949),
                'rot': 0
            },

            17: {
                'pos': (373, 949),
                'rot': 0
            },

            18: {
                'pos': (554, 949),
                'rot': 0
            },

            19: {
                'pos': (735, 949),
                'rot': 0
            },

            20: {
                'pos': (917, 949),
                'rot': 0
            },

            21: {
                'pos': (1098, 949),
                'rot': 0
            },
        }

    elif spread_name == 'zodiac':
        spread = {
            'name': '12 Case dello Zodiaco',
            'total_cards': 13,
            'need_resize': True,
            'card_size': (158, 270),

            0: {
                'pos': (56, 658),
                'rot': 100
            },
            1: {
                'pos': (169, 813),
                'rot': 132
            },
            2: {
                'pos': (428, 925),
                'rot': 166
            },
            3: {
                'pos': (660, 921),
                'rot': 196
            },
            4: {
                'pos': (817, 810),
                'rot': 360-134
            },
            5: {
                'pos': (936, 640),
                'rot': 360-99
            },
            6: {
                'pos': (933, 403),
                'rot': 360-73
            },
            7: {
                'pos': (813, 162),
                'rot': 360-44
            },
            8: {
                'pos': (652, 38),
                'rot': 360-22
            },
            9: {
                'pos': (394, 50),
                'rot': 18
            },
            10: {
                'pos': (152, 200),
                'rot': 49
            },
            11: {
                'pos': (62, 438),
                'rot': 75
            },
            12: {
                'pos': (561, 505),
                'rot': 0
            }
        }

    elif spread_name == 'single':
        spread = {
            'name': 'Carta singola',
            'total_cards': 1,
            'need_resize': False,
            'card_size': (263, 450),

            0: {
                'pos': (509, 415),
                'rot': 0
            }
        }

    elif spread_name == 'celtic_cross':
            spread = {
                'name': 'Croce Celtica',
                'total_cards': 10,
                'need_resize': True,
                'card_size': (183, 312),

                0: {
                    'pos': (420, 484),
                    'rot': 0
                },
                1: {
                    'pos': (355, 549),
                    'rot': 270
                },
                2: {
                    'pos': (420, 88),
                    'rot': 0
                },
                3: {
                    'pos': (420, 880),
                    'rot': 0
                },
                4: {
                    'pos': (100, 484),
                    'rot': 0
                },
                5: {
                    'pos': (726, 484),
                    'rot': 0
                },
                6: {
                    'pos': (1077, 955),
                    'rot': 0
                },
                7: {
                    'pos': (1077, 641),
                    'rot': 0
                },
                8: {
                    'pos': (1077, 328),
                    'rot': 0
                },
                9: {
                    'pos': (1077, 14),
                    'rot': 0
                }
            }

    else:
        raise ValueError

    return spread

async def draw_cards(spread, reverse=False, deck='rws', context=None):
    def spacca(mazzo):
        return mazzo[1:] + mazzo[:1]

    dir = deck
    n = spread['total_cards']
    

    # if "tarot_deck" not in context.bot_data:
    if context:
        if "tarot_deck" not in context.bot_data:
            # print("Non trovo nessun mazzo in memoria")
            default_mazzo = get_default_deck()
            context.bot_data['tarot_deck'] = default_mazzo
            mazzo = default_mazzo
        else:
            mazzo = context.bot_data['tarot_deck']
    
    # mazzo = [i for i in range(0, 22)]
    # print("Sto usando questo mazzo:")
    # print(mazzo)
    # print("Mischio il mazzo")
    mazzo = mischia(mazzo)
    # print(mazzo)
    # print(all_cards)

    # chosen_cards = random.sample(mazzo, k=n)
    chosen_cards = mazzo[0:n]
    # print("Ho scelto le carte:")
    # print(chosen_cards)
    # print("Le metto sotto")
    mazzo = mazzo[n:] + mazzo[:n]
    # print(mazzo)
    # print("Salvo il mazzo")
    context.bot_data['tarot_deck'] = mazzo
    # print(context.bot_data['tarot_deck'])
    
    # pprint.pprint(chosen_cards)
    # print(chosen_cards)
    if spread['name'] == 'Deck Showcase':
        chosen_cards = get_default_deck()

    returned_cards = []

    i = 0
    
    for card in chosen_cards:
        c = {}
        c['number'] = str(card['n'])
        c['pos'] = i
        c['card_name'] = f"{dir}/{str(card['n'])}.png"
        c['is_reversed'] = card['reverse'] if reverse else False
        returned_cards.append(c)
        i += 1
    return {
        'chosen_cards': n,
        'cards': returned_cards
    }

async def draw_cards_special(reverse=False, deck='rws', force_obliqua=False):
    def soffio(mazzo):
        return mazzo

    def spezza(mazzo):
        n = random.randint(1, 20)
        return mazzo[n:] + mazzo[:n]

    def skip(mazzo):
        return mazzo[1:] + mazzo[:1]

    def random_number():
        return random.randint(1, 10000)

    def cabala_sum(number: int, fool=False):
        while number > 22:
            number = sum([int(x) for x in str(number)])
        if fool:
            if number == 22:
                number = 0
        return number


    # - soffiare sul mazzo
    # - spaccare tre volte
    # - scegliere un numero (n1), scartare n1 - 1 carte ed estrarre: dx
    # - scegliere un numero (n2), se maggiore di n1, scartare n2-n1-1 carte ed estrarre: sx; altrimenti scartare n2-1 ed estrarre sx
    # - scegliere un numero (n3), se maggiore di n2, scartare n3-n2-1 carte ed estrarre: su; altrimenti scartare n3-1 ed estrarre su
    # - scegliere un numero (n4), se maggiore di n3, scartare n4-n3-1 carte ed estrarre: su; altrimenti scartare n4-1 ed estrarre su
    # - se i numeri sono > 22, somma delle cifre fino a n >= 22
    # - sommare i numeri delle carte, somma delle cifre fino a n >22. scartare n-1 ed estrarre al centro. se è 22 prendi il matto
    # - cercare l'arcano n e metterlo al centro - se è uguale metterlo obuliquo
    # dx sx su giu centro centro
    # negativo positivo giudice statointeriore cardine e sintesi


    mazzo = [i for i in range(0, 22)]

    random.shuffle(mazzo)

    mazzo = soffio(mazzo)

    for _ in range(3):
        mazzo = spezza(mazzo)


    random_numbers = [cabala_sum(random_number()), cabala_sum(random_number()), cabala_sum(random_number()), cabala_sum(random_number())]

    carte_estratte = []
    n = 0

    for i in range(4):

        if random_numbers[i] > n:
        
            for _ in range(random_numbers[i] - n - 1):
                mazzo = skip(mazzo)

            carte_estratte.append(mazzo.pop(0))

        else:

            for _ in range(random_numbers[i]-1):
                mazzo = skip(mazzo)

            carte_estratte.append(mazzo.pop(0))

        n = random_numbers[i]

    somma = sum(carte_estratte)

    centrale = cabala_sum(somma, fool=True)
    if force_obliqua:
        centrale = random.choice(carte_estratte)

    for _ in range(centrale - 1):
        mazzo = skip(mazzo)

    carte_estratte.append(mazzo.pop(0))



    obliquo = False
    carta_obliqua = None
    if centrale in carte_estratte:
        obliquo = True
        carta_obliqua = centrale
    else:
        carte_estratte.append(centrale)


    returned_cards = []
    i = 0
    for card in carte_estratte:
        c = {}
        c['number'] = str(card)
        c['pos'] = i
        c['card_name'] = f"{deck}/{str(card)}.png"
        c['is_reversed'] = random.choice([True, False]) if reverse else False
        c['is_obliqua'] = True if card == carta_obliqua else False
        returned_cards.append(c)
        i += 1

    mydict= {
        'chosen_cards': i,
        'cards': returned_cards
    }
    # pprint.pprint(mydict)
    return mydict

async def generate_cards_table(cards_info, imagepath, spread_name, zodiac=False):

    # My cards:
    # {'cards': [{'card_name': 'rws/4.png',
    #             'is_reversed': False,
    #             'number': '4',
    #             'pos': 0}],
    #  'chosen_cards': 1}


    # print(cards_info)
    n = cards_info['chosen_cards']
    cards_list = cards_info['cards']

    basedir = 'images/tarots'

    cards_pos = await get_spread(spread_name)
    # print(cards_pos)
    need_resize = cards_pos['need_resize']
    resize_size = cards_pos['card_size']

    sfondo = f"{basedir}/bg/{random.choice(['01', '02', '04', '05', '06', '07', '08', '09'])}.jpg"
    if zodiac:
        sfondo = f"{basedir}/bg/zodiac.jpg"
    background = Image.open(sfondo)

    for mycard in enumerate(cards_list):
        # print(mycard)
        card = Image.open(f"{basedir}/{mycard[1]['card_name']}")

        if need_resize:
            card = card.resize(resize_size)

        if mycard[1]['is_reversed']:
            card = card.rotate(180)

        card = card.rotate(random.choice([358, 359, 0, 1, 2]) + cards_pos[mycard[0]]['rot'], resample=Image.Resampling.BICUBIC, expand=True)

        if mycard[1].get('is_obliqua', False):
            card = card.rotate(45, resample=Image.Resampling.BICUBIC, expand=True)
            background.paste(card, (cards_pos[mycard[0]]['pos'][0] - 100, cards_pos[mycard[0]]['pos'][1] - 20), card)
        else:
            background.paste(card, cards_pos[mycard[0]]['pos'], card)

    background.save(imagepath)


# Tarocculi
async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return

    reverse = False
    read = True
    zodiac = False
    info = False
    draw = False
    force_obliqua = False
    help_message = False
    deck = random.choice(['rws', 'morgan'])
    spread_name = 'default_three'

    SPREADS = ['yesno', 'wirth', 'zodiac', 'default_three', 'simple_cross', 'celtic_cross', 'mondo', 'scelta']
    DECKS = ['marsiglia', 'rws', 'morgan', 'keymaster', 'heaven', 'santamuerte']

    k_spreads = ['yesno', '3cards', 'simplecross', 'wirth', 'celtic', 'mondo', 'scelta', 'zodiac', 'year']
    k_decks = ['marsiglia', 'thoth', 'keymaster', 'morgan', 'fyodor', 'heaven', 'shadow', 'santamuerte', 'rws']

    if not context.args:
        h = ""
        h += f"ERRORE: devi scegliere un mazzo e uno schema:\n<code>/tarocchi -[mazzo] -[schema]</code>\n\n"
        h += f"Usa il comando <code>-help</code> per la lista completa di opzioni:\n<code>/tarocchi -help</code>\n\n"
        h += f"Un esempio casuale:\n<code>/tarocchi -{random.choice(k_decks)} -{random.choice(k_spreads)}</code>"
        await update.message.reply_html(h, disable_web_page_preview=True)
        return


    if context.args:
        if '-yesno' in context.args:
            spread_name = "single"
        if '-noread' in context.args:
            read = False
        if '-info' in context.args:
            info = True
        if '-reverse' in context.args:
            reverse = True

        if '-simplecross' in context.args:
            spread_name = "simple_cross"
        if '--3cards' in context.args:
            spread_name = "default_three"
        if '-celtic' in context.args:
            spread_name = "celtic_cross"
        if '-zodiac' in context.args:
            spread_name = "zodiac"
            zodiac = True
        if '-mondo' in context.args:
            spread_name = "mondo"
        if '-scelta' in context.args:
            spread_name = "scelta"
        if '-year' in context.args:
            spread_name = "year"
        if '-wirth' in context.args:
            draw = True
            spread_name = "wirth"

        # Non documentati
        if '-full' in context.args:
            spread_name = 'full'
        if '-force_obliqua' in context.args:
            force_obliqua = True

        if '-marsiglia' in context.args:
            deck = 'mars'
        if '-thoth' in context.args:
            deck = 'thoth'  
        if '-morgan' in context.args:
            deck = 'morgan'
        if '-rws' in context.args:
            deck = 'rws'
        if '-keymaster' in context.args:
            deck = 'keymaster'
        if '-fyodor' in context.args:
            deck = 'fyodor'
        if '-heaven' in context.args:
            deck = 'heaven'
        if '-shadow' in context.args:
            deck = 'shadow'
        if '-santamuerte' in context.args:
            deck = 'santamuerte'

        if '-help' in context.args:
            help_message = True

    if help_message:
        h = ""
        h += f"Uso: <code>/tarocchi [mazzo] [schema] [opzioni]</code>\n\n"

        h += f"<b>· Mazzi ·</b>\n"
        h += f"<code>-marsiglia  </code>: usa il mazzo di Marsiglia.\n"
        h += f"<code>-thoth      </code>: usa il mazzo Thoth/Crowley.\n"
        h += f"<code>-keymaster  </code>: usa il mazzo Keymaster.\n"
        h += f"<code>-morgan     </code>: usa il mazzo Morgan-Greer.\n"
        h += f"<code>-fyodor     </code>: usa il mazzo Fyodor Pavlov.\n"
        h += f"<code>-heaven     </code>: usa il mazzo Heaven and Earth.\n"
        h += f"<code>-shadow     </code>: usa il mazzo Shadow and Light.\n"
        h += f"<code>-santamuerte</code>: Usa il mazzo Santa Muerte.\n"
        h += f"<code>-rws        </code>: usa il mazzo Rider-Waite-Smith.\n\n"

        h += f"Una galleria dei mazzi può essere vista <a href='https://imgur.com/a/iLIaqC3'>qui</a>.\n\n"

        h += f"<b>· Schemi ·</b>\n"
        h += f"<code>-yesno      </code>: carta singola, con lettura.\n"
        h += f"<code>-3cards     </code>: Tre carte, con lettura passato presente e futuro.\n"
        h += f"<code>-simplecross</code>: croce <a href='https://www.sortedsoul.com/wp-content/uploads/2017/10/PSX_20181012_191903-1.jpg'>semplice</a>.\n"
        h += f"<code>-wirth      </code>: croce <a href='https://i.imgur.com/1KkWTlf.png'>di Wirth modificata</a>.\n"
        h += f"<code>-celtic     </code>: croce <a href='https://i0.wp.com/angelorum.co/wp-content/uploads/2016/10/The-Celtic-Cross.jpg'>celtica.</a>\n"
        h += f"<code>-mondo      </code>: schema del <a href='https://i.imgur.com/84zgN5b.png'>mondo</a>.\n"
        h += f"<code>-scelta     </code>: tarocchi della <a href='https://i.imgur.com/EZdPooH.png'>scelta</a>.\n"
        h += f"<code>-zodiac     </code>: una carta per <a href='https://i0.wp.com/angelorum.co/wp-content/uploads/2015/12/12-Houses-Zodiac-Tarot-Spread.jpg'>casa zodiacale</a>.\n"
        h += f"<code>-year       </code>: estrazione annuale a 16 carte.\n\n"

        h += f"Una galleria degli schemi può essere vista <a href='https://imgur.com/a/lYgEWWX'>qui</a>.\n\n"
        
        h += f"<b>· Opzioni ·</b>\n"
        h += f"<code>-noread     </code>: non fare la lettura.\n"
        h += f"<code>-info       </code>: la lista, in ordine, delle carte uscite.\n"
        h += f"<code>-reverse    </code>: abilità la possibilità che le carte siano a testa in giù.\n\n"

        
        h += f"Esempio:\n<code>/tarocchi -morgan -wirth</code>: estrazione con schema croce di Wirth e mazzo Morgan-Greer.\n"

        await printlog(update, "chiede l'help dei tarocchi")
        await update.message.reply_html(h, disable_web_page_preview=True)
        return

    imagepath = tempfile.NamedTemporaryFile(suffix='.jpg')

    with open('db/tarots.json') as tarots_db:
        tarots = json.load(tarots_db)

    lettura = ""

    my_spread = await get_spread(spread_name)

    await printlog(update, "fa i tarocchi", my_spread['name'])

    if draw:
        my_cards = await draw_cards_special(reverse=reverse, force_obliqua=force_obliqua, deck=deck)
    else:
        my_cards = await draw_cards(my_spread, reverse=reverse, deck=deck, context=context)

    await generate_cards_table(my_cards, imagepath.name, spread_name, zodiac=zodiac)
    caption = my_spread['name']
    msg = await update.message.reply_photo(photo=imagepath, caption=caption)

    if info:
        info = ''
        for card in my_cards['cards']:
            info += f"<code>{card['pos']+1}: [{card['number']}] · {tarots[card['number']]['name']}</code>\n"
        await update.message.reply_html(info, reply_to_message_id=msg.message_id)

    if read and spread_name == 'single' and deck in ['rws', 'morgan']:
        card_no = my_cards['cards'][0]['number']
        lettura += f"<b>{tarots[card_no]['name']}</b>\n"
        # print(tarots)
        # print(card_no)
        # print(tarots[card_no])
        lettura += f"{tarots[card_no]['yesno']}\n\n"
        await update.message.reply_html(lettura, reply_to_message_id=msg.message_id)

    if read and spread_name == 'default_three' and deck in ['rws', 'morgan']:
        past, present, future = [x['number'] for x in my_cards['cards']]

        lettura += f"<b>{tarots[past]['name']}</b>\n"
        # lettura += f"<i>{tarots[past]['keywords']}</i>\n"
        lettura += f"{tarots[past]['past']}\n\n"

        lettura += f"<b>{tarots[present]['name']}</b>\n"
        # lettura += f"<i>{tarots[present]['keywords']}</i>\n"
        lettura += f"{tarots[present]['present']}\n\n"

        lettura += f"<b>{tarots[future]['name']}</b>\n"
        # lettura += f"<i>{tarots[future]['keywords']}</i>\n"
        lettura += f"{tarots[future]['future']}"

        await update.message.reply_html(lettura, reply_to_message_id=msg.message_id)
    imagepath.close()

async def tarotschema(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return

    a = argparse.ArgumentParser()

    a.add_argument("schema", nargs='?', default='default_three')
    a.add_argument('-c', '--carte', nargs='+', dest='carte', default=['0'], required=True)
    a.add_argument('-d', '--deck', nargs='?', default='rws')

    if not context.args:
        await update.message.reply_html(f'Uso:\n<code>/schema [nome dello schema] -c [numeri delle carte] -d [nome del mazzo]</code>\nAd esempio:\n<code>/schema wirth -c 11 0 15 3 7 5 -d marsiglia</code>\nUsa l\'asterisco <code>*</code> per indicare una carta obliqua.')
        return
    if '-help' in context.args:
        await update.message.reply_html(f'Questo comando serve a creare un\'immagine basandosi sull\'estrazione dei tarocchi hce hai già fatto per conto tuo.\nUso:\n<code>/schema [nome dello schema] -c [numeri delle carte] -d [nome del mazzo]</code>\nAd esempio:\n<code>/schema wirth -c 11 0 15 3 7 5 -d marsiglia</code>\nUsa l\'asterisco <code>*</code> per indicare una carta obliqua.')
        return
    args, unknown = a.parse_known_args(context.args)
    # print(args)

    SPREADS = ['yesno', 'wirth', 'zodiac', 'default_three', 'simple_cross', 'celtic_cross', 'year', 'mondo', 'scelta']
    DECKS = ['marsiglia', 'rws', 'thoth', 'morgan', 'keymaster', 'fyodor', 'heaven', 'shadow', 'santamuerte']

    carte = args.carte
    spread_name = args.schema
    chosen_deck = args.deck

    if spread_name not in SPREADS:
        await update.message.reply_html(f'Schema non riconosciuto, deve essere uno di questi: <code>{[x for x in SPREADS]}</code>')
        return
    if chosen_deck not in DECKS:
        await update.message.reply_html(f'Mazzo non riconosciuto, deve essere uno di questi: <code>{[x for x in DECKS]}</code>')
        return

    spread = await get_spread(spread_name)

    carta_obliqua = None
    deck = 'rws'
    reverse = False
    zodiac = False

    if spread_name == 'zodiac':
        zodiac = True
    if chosen_deck == 'marsiglia':
        deck = 'mars'

    # imagepath = tempfile.mktemp(suffix='.jpg')
    imagepath = tempfile.NamedTemporaryFile(suffix='.jpg')

    await printlog(update, "fa i tarocchi", spread['name'])

    for c in carte:
        if '*' in c:
            carta_obliqua = c
        if int(c.replace('*','')) > 21 or int(c.replace('*','')) < 0:
            await update.message.reply_html(f'Scusa ma i numeri devono essere tra 0 e 21')
            return

    returned_cards = []

    i = 0


    for card in carte:
        c = {}
        c['number'] = str(card).replace('*','')
        c['pos'] = i
        c['card_name'] = f"{deck}/{str(card).replace('*','')}.png"
        c['is_reversed'] = random.choice([True, False]) if reverse else False
        c['is_obliqua'] = True if card == carta_obliqua else False
        returned_cards.append(c)
        i += 1
    my_cards = {
        'chosen_cards': i,
        'cards': returned_cards
    }

    await generate_cards_table(my_cards, imagepath.name, spread_name, zodiac=zodiac)
    caption = spread['name']
    msg = await update.message.reply_photo(photo=imagepath, caption=caption)
    imagepath.close()

# Oroscopulo
async def oroscopo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return
    segni = [
            "ariete", "toro", "gemelli", "cancro", "leone", "vergine", "bilancia", "scorpione", "sagittario", "capricorno", "acquario", "pesci",
            "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        ]
    def get_english_sign(sign):
        all_signs = {
            "ariete": "aries",
            "toro": "taurus",
            "gemelli": "gemini",
            "cancro": "cancer",
            "leone": "leo",
            "vergine": "virgo",
            "bilancia": "libra",
            "scorpione": "scorpio",
            "sagittario": "sagittarius",
            "capricorno": "capricorn",
            "acquario": "aquarius",
            "pesci": "pisces"
        }
        if sign in all_signs.values():
            return sign

        if sign in all_signs.keys():
            return all_signs[sign]
        return None

    parser = ArgumentParser(description='Oroscopo Parser')
    parser.add_argument("segno", nargs='?', default=None)
    parser.add_argument('-setdefault', '-set', type=str)

    # args = parser.parse_args(context.args)
    args, unknown = parser.parse_known_args(context.args)

    if args.setdefault:
        if args.setdefault.lower() in segni:
            mysegno = str(get_english_sign(args.setdefault.lower()))
            context.user_data['segno_zodiacale'] = mysegno
            await printlog(update, "imposta il suo segno doziacale", mysegno)
            await update.message.reply_html(f"Ho impostato il segno {mysegno}. Da adesso in poi ti basterà digitare <code>/oroscopo</code>")
            return
        else:
            await update.message.reply_html(f"{args.setdefault} non è un segno valido.")
            return

    if not context.args or not args.segno:
        if not context.user_data.get('segno_zodiacale', None):
            await update.message.reply_html(f"Uso: <code>/oroscopo [segno]</code>\nPuoi anche usare <code>/oroscopo -setdefault [segno]</code> per memorizzare il tuo segno.")
            return
        else:
            segno = context.user_data.get('segno_zodiacale')

    elif context.args[0] in segni:
        segno = str(get_english_sign(context.args[0].lower()))
    else:
        await update.message.reply_html(f"{context.args[0]} non è un segno valido.\nUso: <code>/oroscopo [segno]</code>\nPuoi anche usare <code>/oroscopo -setdefault [segno]</code> per memorizzare il tuo segno.")
        return

    await printlog(update, "consulta l'oroscopo", segno)
    horoscope = pyaztro.Aztro(sign=segno)
    sign = horoscope.sign
    color = horoscope.color
    compatibility = horoscope.compatibility
    desc = horoscope.description
    lucky_number = horoscope.lucky_number
    lucky_time = horoscope.lucky_time
    mood = horoscope.mood
    
    translator = deepl.Translator(config.DEEPL_API_KEY) 
    target_language = "IT"
    result = translator.translate_text(desc, target_lang=target_language) 
    translated_desc = f'{result.text}'
    oroscopo_emoji = {
        "aries": "♈",
        "taurus": "♉",
        "gemini": "♊",
        "cancer": "♋",
        "leo": "♌",
        "virgo": "♍",
        "libra": "♎",
        "scorpio": "♏",
        "sagittarius": "♐",
        "capricorn": "♑",
        "aquarius": "♒",
        "pisces": "♓"
    }

    message = ""
    message += f"<b>Oroscopo di oggi per il segno {oroscopo_emoji[sign]} {sign.capitalize()}</b>\n"
    message += f"Colore: {color} · Segno compatibile: {compatibility}\n"
    message += f"Numero fortunato: {lucky_number} · Ora fortunata: {lucky_time}\n"
    message += f"Mood: {mood}\n\n"
    message += f"{desc}\n\n"
    message += f"{translated_desc}\n\n"
    # print(message)
    await update.message.reply_html(message)
