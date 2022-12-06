import cairo
import uuid
import pytz
import math
import random
from datetime import datetime, timezone
import requests
from PIL import Image, ImageDraw, ImageFont
    
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext, ContextTypes
from rich import print

import config

from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do



async def solarsystem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return
    if update.effective_user.id not in config.ADMINS and update.effective_chat.id == config.ID_TIMELINE:
        return

    # random.seed(f"{update.message.from_user.id}+{update.message.chat.id}+{datetime.datetime.today().strftime('%Y-%m-%d')}")

    

    list_of_colors = [
        (145, 185, 141), (229, 192, 121), (210, 191, 88), (140, 190, 178), (255, 183, 10), (189, 190, 220),
        (221, 79, 91), (16, 182, 98), (227, 146, 80), (241, 133, 123), (110, 197, 233), (235, 205, 188), (197, 239, 247), (190, 144, 212),
        (41, 241, 195), (101, 198, 187), (255, 246, 143), (243, 156, 18), (189, 195, 199), (243, 241, 239)
        ]

    list_of_sun_colors = [
        (255, 95, 83), (253, 209, 162), (255, 243, 161), (252, 255, 212), (248, 247, 253), (201, 216, 255), (154, 175, 255)
        ]

    def planet_name():
        part1 = [
            "Æ",
            "Arc",
            "A",
            "Ab",
            "Ag",
            "At",
            "Am",
            "Amon",
            "An",
            "Ant",
            "Aer",
            "Aeria",
            "Ar",
            "Aria",
            "Atar",
            "Astar",
            "Ana",
            "Av",
            "Ba",
            "Ban",
            "Bant",
            "Bar",
            "Be",
            "Bet",
            "Bi",
            "Bro",
            "Bo",
            "Bon",
            "Brum",
            "B’",
            "Ca",
            "Camp",
            "Car",
            "Carr",
            "Ce",
            "Cer",
            "Ci",
            "Clo",
            "Chur",
            "Cold",
            "Con",
            "Coper",
            "Corr",
            "Cu",
            "Cy",
            "C’",
            "Da",
            "Dark",
            "De",
            "Del",
            "Deep",
            "Dep",
            "Der",
            "Dikar",
            "Du",
            "Dur",
            "Dun",
            "E",
            "Ea",
            "El",
            "Er",
            "Exo",
            "Far",
            "Fox",
            "Fog",
            "Fon",
            "Fur",
            "Fun",
            "Fung",
            "Galad",
            "Gan",
            "Gunt",
            "Gren",
            "H",
            "Hub",
            "Har",
            "Haar",
            "Hark",
            "Hel",
            "Hon",
            "Hed",
            "Ib",
            "Ich",
            "Ian",
            "Int",
            "Iv",
            "Jan",
            "Ko",
            "K'",
            "Kaan",
            "Khan",
            "Kne",
            "Ken",
            "Ket",
            "Kep",
            "Ku",
            "Klin",
            "Lad",
            "Leg",
            "Lig",
            "Lo",
            "Lo",
            "Lone",
            "Long",
            "L'",
            "Ll'",
            "Majest",
            "Maz",
            "Mer",
            "Merg",
            "Merc",
            "Miran",
            "Mun",
            "Nar",
            "Nan",
            "Nad",
            "Nas",
            "Night",
            "Nir",
            "Nit",
            "Nib",
            "Non",
            "No",
            "Ob",
            "Ox",
            "Out",
            "Ov",
            "Oz",
            "Pa",
            "Pat",
            "Pap",
            "Pan",
            "Pert",
            "Plane",
            "Plu",
            "Plo",
            "Pro",
            "Pra",
            "Pran",
            "Por",
            "Pool",
            "Pling",
            "Py",
            "Pyro",
            "Rem",
            "Ran",
            "Rus",
            "Sai",
            "S'",
            "So'",
            "Sat",
            "Sen",
            "Sev",
            "Shan",
            "Shandak",
            "Siden",
            "Sizen",
            "Sot",
            "Sop",
            "Sot Ank",
            "Sot Lo",
            "Son",
            "Scar",
            "Steep",
            "Suil",
            "Sul",
            "Sum",
            "Sun",
            "Sva",
            "Syn",
            "T",
            "Tac",
            "Tad",
            "Taf",
            "Tag",
            "Tai",
            "Tal",
            "Talm",
            "Tam",
            "Tar",
            "Tas",
            "Tash",
            "Tav",
            "Tax",
            "Tat",
            "Tap",
            "Tep",
            "Tha",
            "Than",
            "Than Dok",
            "Thry",
            "Trel",
            "Treep",
            "Ter Threp",
            "Tol",
            "Ur",
            "Uran",
            "Um",
            "Vab",
            "Vad",
            "Vak",
            "Vak",
            "Vam",
            "Vad",
            "Ven",
            "Ves",
            "Ver",
            "Vis",
            "Viv",
            "Vul",
            "Vop",
            "War",
            "Won",
            "Wo",
            "Won",
            "What",
            "Whim",
            "Wim",
            "Win",
            "War",
            "Wad",
            "Wan",
            "Wun",
            "X'",
            "Xe'",
            "Xen",
            "Xio",
            "Xy",
            "Zing",
            "Zed",
            "Zer",
            "Zem",
            "Zeng"
        ]
        part2 = [
            "-o",
            "acalla",
            "addon",
            "adon",
            "acan",
            "aroid",
            "anbula",
            "angolia",
            "angalia",
            "ankor",
            "aldi",
            "aka",
            "aleko",
            "alis",
            "alla",
            "alos",
            "an",
            "andia",
            "anella",
            "ania",
            "amis",
            "arnia",
            "aran",
            "ara",
            "arth",
            "arius",
            "atoid",
            "avera",
            "budram",
            "budria",
            "burto",
            "borto",
            "bongo",
            "can",
            "cania",
            "cania",
            "caris",
            "cury",
            "chil",
            "chin",
            "chia",
            "chania",
            "con",
            "da",
            "dai",
            "dania",
            "daleko",
            "dalekon",
            "doria",
            "donia",
            "dikar",
            "eko",
            "ella",
            "elos",
            "elius",
            "elerth",
            "elialia",
            "eria",
            "era",
            "enia",
            "enella",
            "erebus",
            "es",
            "esh",
            "eaux",
            "ebus",
            "eus",
            "eran",
            "fall",
            "far",
            "finer",
            "gania",
            "gatis",
            "gill",
            "golia",
            "ian",
            "ion",
            "illian",
            "illa",
            "idian",
            "inax",
            "iman",
            "itas",
            "ius",
            "iza",
            "iru",
            "ix",
            "kail",
            "kien",
            "las",
            "lax",
            "lak",
            "ler",
            "land",
            "lejos",
            "lok",
            "los",
            "lox",
            "lon",
            "miniar",
            "nar",
            "nia",
            "nicus",
            "nor",
            "nt",
            "ntos",
            "oda",
            "oid",
            "oin",
            "ol",
            "omi",
            "on",
            "onine",
            "ong",
            "ongolia",
            "onia",
            "ornia",
            "ornania",
            "opa",
            "opia",
            "opia",
            "olok",
            "os",
            "oros",
            "orox",
            "orkon",
            "ovin",
            "ox",
            "pidor",
            "pid",
            "pod",
            "rax",
            "reus",
            "rock",
            "roid",
            "rog",
            "ryn",
            "sea",
            "shaa",
            "tan",
            "tara",
            "taria",
            "ton",
            "tes",
            "tep",
            "thra",
            "tania",
            "to",
            "tos",
            "tose",
            "tonia",
            "tronia",
            "topia",
            "tos",
            "trock",
            "tropic",
            "tus",
            "udros",
            "ule",
            "um",
            "umi",
            "uram",
            "urn",
            "urrinia",
            "ury",
            "urdan",
            "uria",
            "uridan",
            "uridian",
            "us",
            "utlis",
            "va",
            "vana",
            "vas",
            "vav",
            "vin",
            "vis",
            "viz",
            "za",
            "'am",
            "'an",
            "'us",
            "al"
        ]
        return f"{random.choice(part1)}{random.choice(part2)}"

    def generate_planet_name():
        prefix = [
            "Alpha",
            "Alpha Omega",
            "Beta",
            "Gamma",
            "Ceti",
            "Delta",
            "Epsilon",
            "Theta",
            "Zeta",
            "Omega",
            "Tau",
            "Tau Ceti",
            "The planet of",
            "The moon of",
            "The ringed planet of",
            "The robot world of",
            "The mountainous planet of",
            "The mist planet of",
            "The lava world of",
            "The ghost world of",
            "The desert planet of",
            "The ancient planet of",
            "The rock of",
            "New",
            "White",
            "East",
            "West",
            "North",
            "Old",
            "Las",
            "Los",
            "La"
        ]
        suffix = [
            "Alpha",
            "Beta",
            "Gamma",
            "Kappa",
            "Sigma",
            "Prime",
            "Major",
            "Minor",
            "One",
            "Two",
            "Epsilon",
            "Zeta",
            "Quintus",
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
            "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIV", "XV", "XVI",
            "World", "Moon", "gas giant",
            "e1", "e2", "e3", "e4"
        ]
        posession = [
            "Haven",
            "Hope",
            "World",
            "Forge",
            "Paradise",
            "Fall",
            "Reach",
            "Stronghold",
            "Beacon",
            "Outpost",
            "Sanctum",
            "Refuge",
            "Retreat",
            "Terminus",
            "Moon",
            "World",
            "Planetoid"
        ]
        planetname = planet_name()

        prefix_chance = random.randint(0, 100)
        suffix_chance = random.randint(0, 100)

        random_prefix = random.choice(prefix)
        random_suffix = random.choice(suffix)
        second_word_chance = random.choice(suffix)

        if prefix_chance <= 20:
            planetname = f"{random_prefix} {planetname}"

        if second_word_chance in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]:
            planetname = f"{planetname} {planet_name()}"

        if suffix_chance <= 25:
            planetname = f"{planetname} {random_suffix}"
        elif suffix_chance <= 45:
            planetname = f"{planetname} {random.randint(0, 400)}"
        elif suffix_chance <= 50:
            planetname = f"{planetname}'s {random.choice(posession)}"

        return planetname

    def generate_system():
        def gen_system_prefix():
            prefixes = [
                "Alpha",
                "Beta",
                "Gamma",
                "Ceti",
                "Picon",
                "Delta",
                "Epsilon",
                "Theta",
                "Zeta",
                "Omega",
                "Tau",
                "Nebulon",
                "Las",
                "Los",
                "La",
                "Far",
                "Deep",
                "Ultra",
                "Mega",
                "Super",
                "Über",
                "Omicron",
                "Sigma",
                "Kappa",
                "Rho",
                "Minor",
                "Major",
                "Greater"
                ]
            return random.choice(prefixes)  

        def gen_system_name():
            systems = [
                "Arf",
                "Alf",
                "Aeron",
                "Andromeda",
                "Apius",
                "Aquarius",
                "Ara",
                "Alpha Andromeda",
                "Alpha Centauri",
                "Alpha Persei",
                "Alcor",
                "Algol",
                "Antares",
                "Basri",
                "Behram",
                "Beta Picoris",
                "Boötes",
                "Cancri",
                "Canes Venatici",
                "Canis",
                "Capricorn",
                "Cassiopeia",
                "Castor",
                "Cebus",
                "Centaurus",
                "Ceti",
                "Cetus",
                "Columbus",
                "Coma Berenices",
                "Copurnicus",
                "Corona Borealis",
                "Corot",
                "Cygnus",
                "Cygni",
                "Dorado",
                "Draco",
                "Eridanus",
                "Eridanus",
                "Fikes",
                "Fornax",
                "Fomalhaut",
                "Gilese",
                "Goddard",
                "HD",
                "Hat",
                "Hercules",
                "Herculis",
                "Horologium",
                "Holbrook",
                "Hydra",
                "Hydrus",
                "Leo",
                "Leonis",
                "Libra",
                "Librae",
                "Lupus",
                "Luyten",
                "Lyra",
                "Mensa",
                "Mensae",
                "Monocerus",
                "Orion",
                "Pavo",
                "Pi Mensae",
                "Piccard",
                "Pictor",
                "Pisces",
                "Puppis",
                "Raleigh",
                "Reticulum",
                "Regulus",
                "Rho Corona Borealis",
                "Rosa",
                "Rouse",
                "Sagittarius",
                "Scorpius",
                "Serpens",
                "Sextan",
                "Spica",
                "Tau Geminorum",
                "Trappist",
                "Triangulum Australe",
                "Tucana",
                "Tyson",
                "Upsilon Andromedae",
                "Ursa Major",
                "Ursa Minor",
                "Ursae Majoris",
                "Vela",
                "Virgo",
                "Wasp",
                "Kepler",
                "Procyon",
                "Procyon",
                "Vorach",
                "Vorash",
                "Tobin",
                "Adara",
                "Doranda",
                "Copernicus",
                "Newton",
                "Ptolemy",
                "Hubble",
                "Herschel",
                "Sagan",
                "Einstein",
                "Messier",
                "Huygens",
                "Cannon",
                "Samos",
                "Laplace",
                "Burnell",
                "Bell",
                "Leavitt",
                "Penzias",
                "Payne",
                "Hawking",
                "Moore",
                "Rees",
                "Halley",
                "Burbidge",
                "Flamsteed",
                "Couper",
                "Marsden",
                "Gill",
                "Chandra",
                "Chan",
                "Chung",
                "Wickramasinghe",
                "Narlikar",
                "Brahmagupta",
                "Gupta",
                "Somayaji",
                "Bappu",
                "Ball",
                "Saha",
                "Das Gupta",
                "Lalla",
                "Jani",
                "Natarajan",
                "Subramaniam",
                "Fairall",
                "Knox",
                "Paraskevopoulos",
                "Weiss",
                "Wilkins",
                "Llewelyn",
                "Gomez",
                "Evans",
                "Myanmar",
                "Dilhan",
                "Eryurt"
            ]
            return random.choice(systems)

        def gen_system_suffix():
            suffixes = [
                "Expanse",
                "Expanse",
                "Expanse",
                "Nebula",
                "Nebula",
                "Stellar Nursery",
                "Passage",
                "Pass",
                "Phenomenon",
                "Space",
                "Sector",
                "Sector",
                "Sector",
                "Zone",
                "Zone",
                "Region",
                "Region",
                "Quadrant",
                "Quadrant",
                "Territory",
                "Belt",
                "Field",
                "Section",
                "Vicinity",
                "Proximity",
                "Cluster",
                "Cluster",
                "Spiral",
                "Halo Zone",
                "Coronal Stream",
                "Pulsar System",
                "Cloud Node",
                "Supercluster",
                "Vortex",
                "Star System",
                "Cluster System",
            ]
            return random.choice(suffixes)

        system_name = ""
        s_type = random.randint(0, 100)
        s_suffix_type = random.randint(0, 100)
        s_the_chance = random.randint(0, 100)

        if s_type <= 35:
            system_name = planet_name()
        elif s_type <= 65:
            system_name = f"{gen_system_prefix()} {planet_name()}" 
        elif s_type <= 85:
            system_name = f"{planet_name()} {planet_name()}"
        else:
            system_name = gen_system_name()

        if s_suffix_type <= 80:
            system_name += f" {gen_system_suffix()}"
        else:
            system_name += f" System"

        if s_the_chance <= 75:
            system_name = f"The {system_name}"
        return system_name

    def draw_ring(cr, x, y, rad_min, rad_max, r, g, b, a=1.0, gradient=False):
        if GRADIENTS and gradient:
            pattern = cairo.RadialGradient(x, y, rad_min, x, y, rad_max)
            pattern.add_color_stop_rgba(0, r - 0.3, g - 0.3, b - 0.3, a - 0.3)
            pattern.add_color_stop_rgba(1, r, g, b, a)
            cr.set_source(pattern)
        else:
            cr.set_source_rgba(r, g, b, a)
        cr.arc(x, y, rad_max, 0, 2 * math.pi)
        cr.close_path()
        cr.arc(x, y, rad_min, 0, 2 * math.pi)
        cr.close_path()
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        cr.fill()
        cr.set_fill_rule(cairo.FILL_RULE_WINDING)

    def draw_orbit(cr, line, x, y, radius, r, g, b, a=1.0):
        cr.set_source_rgba(r, g, b, a)
        cr.set_line_width(line)
        cr.arc(x, y, radius, 0, 2 * math.pi)
        cr.stroke()

    def draw_circle_fill(cr, x, y, radius, r, g, b, a=1.0, gradient=False):
        if GRADIENTS and gradient:
            orbit_angle = random.randint(0, 20)
            pattern = cairo.LinearGradient(x + orbit_angle, y + radius, x -orbit_angle, y - radius)
            n_colors = random.randint(2, 4)
            for i in range(n_colors):
                rand_color = random.choice(list_of_colors)
                r, g, b = rand_color[0] / 255.0, rand_color[1] / 255.0, rand_color[2] / 255.0
                pattern.add_color_stop_rgb(i, r, g, b)
            cr.set_source(pattern)
        else:
            cr.set_source_rgba(r, g, b, a)

        cr.arc(x, y, radius, 0, 2 * math.pi)
        cr.fill()

    def draw_border(cr, size, r, g, b, width, height):
        cr.set_source_rgb(r, g, b)
        cr.rectangle(0, 0, size, height)
        cr.rectangle(0, 0, width, size)
        cr.rectangle(0, height - size, width, size)
        cr.rectangle(width - size, 0, size, height)
        cr.fill()

    def draw_background(cr, r, g, b, width, height):
        cr.set_source_rgb(r, g, b)
        cr.rectangle(0, 0, width, height)
        cr.fill()

    def random_bg_color(min, max):
        return round(random.uniform(min, max), 2)

    def get_point_on_circle(xc, yc, r, n=360):
        return [
            (
                int(xc + (math.cos(2 * math.pi / n * x) * r)),  # x
                int(yc + (math.sin(2 * math.pi / n * x) * r)),  # y
            )
            for x in range(0, n + 1)
        ]

    def get_random_gaps_segments(total_space, n_segs):
        """
        seleziona n_segs-1 punti casuali, con una distanza minima tra loro pari a un quarto del segmento medio
        crea i gap in quei punti di larghezza random ma piccola (min 1px, max 20% del segmento medio)
        """

        segments = []
        min_distance_between_gaps = math.ceil((total_space / n_segs) / 4)
        gaps = [min_distance_between_gaps * i + x for i, x in enumerate(sorted(random.sample(range(5, total_space - 10), k=n_segs - 1)))]
        gaps.sort()

        seg_start = 0

        for gap in gaps:
            gap_size = random.randint(1, math.ceil((total_space / n_segs) * 0.2))  # gap between segments, 1px - 20% of average segment 
            half_gap_1 = round(gap_size / 2)
            half_gap_2 = gap_size - half_gap_1
            gap_start = gap - half_gap_1
            gap_end = gap + half_gap_2
            segments.append(gap_start - seg_start)
            segments.append(gap_size)
            seg_start = gap_end

        segments.append(total_space - seg_start)  # aggiunge l'ultimo segmento
        return segments

    def draw_black_hole2(cr, x, y, radius, r, b, g, a=1.0, gradient=True):
        hole_radius = radius * 0.8
        sfumatura_min = radius * 0.8
        sfumatura_max = radius * 1

        cr.set_source_rgba(0, 0, 0)
        cr.arc(x, y, hole_radius, 0, 2 * math.pi)
        cr.fill()

        if GRADIENTS and gradient:
            pattern = cairo.RadialGradient(x, y, sfumatura_min, x, y, sfumatura_max)
            pattern.add_color_stop_rgba(0, r, g, b, a)
            # pattern.add_color_stop_rgba(1, bgr, bgb, bgg, bga)
            pattern.add_color_stop_rgba(1, r, g, b, 0)
            cr.set_source(pattern)
        else:
            cr.set_source_rgba(r, g, b, a)

        cr.arc(x, y, sfumatura_min, 0, 2 * math.pi)
        cr.close_path()
        cr.arc(x, y, sfumatura_max, 0, 2 * math.pi)
        cr.close_path()
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        cr.fill()
        cr.set_fill_rule(cairo.FILL_RULE_WINDING)

    def draw_sun(cr, x, y, radius, r, b, g, a=1.0, gradient=True):
        hole_radius = radius * 0.6
        sfumatura_min = radius * 0.55
        sfumatura_max = radius * 1

        # if GRADIENTS and gradient:
        #     pattern = cairo.LinearGradient(x, y + hole_radius, x, y - hole_radius)
        #     n_colors = random.randint(2, 4)
        #     for i in range(n_colors):
        #         rand_color = random.choice(list_of_colors)
        #         r, g, b = rand_color[0] / 255.0, rand_color[1] / 255.0, rand_color[2] / 255.0
        #         pattern.add_color_stop_rgb(i, r, g, b)
        #     cr.set_source(pattern)
        # else:
        #     cr.set_source_rgba(r, g, b, a)
        cr.set_source_rgba(r, g, b, a)

        cr.arc(x, y, hole_radius, 0, 2 * math.pi)
        cr.fill()

        if GRADIENTS and gradient:
            pattern_halo = cairo.RadialGradient(x, y, sfumatura_min, x, y, sfumatura_max)
            pattern_halo.add_color_stop_rgba(0, r, g, b, a)
            # pattern.add_color_stop_rgba(1, bgr, bgb, bgg, bga)
            pattern_halo.add_color_stop_rgba(0.3, r, g, b, 0.5)
            pattern_halo.add_color_stop_rgba(1, r, g, b, 0)
            cr.set_source(pattern_halo)
        else:
            cr.set_source_rgba(r, g, b, a)

        cr.arc(x, y, sfumatura_min, 0, 2 * math.pi)
        cr.close_path()
        cr.arc(x, y, sfumatura_max, 0, 2 * math.pi)
        cr.close_path()
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        cr.fill()
        cr.set_fill_rule(cairo.FILL_RULE_WINDING)

    def draw_star(cr, x, y, size, r, b, g, a=1.0):
        p1 = (x + size, y)
        p2 = (x, y - size)
        p3 = (x - size, y)
        p4 = (x, y + size)
        cr.set_source_rgba(r, g, b, a)
        cr.move_to(p1[0], p1[1])
        cr.curve_to(x, y, x, y, p2[0], p2[1])
        cr.curve_to(x, y, x, y, p3[0], p3[1])
        cr.curve_to(x, y, x, y, p4[0], p4[1])
        cr.curve_to(x, y, x, y, p1[0], p1[1])
        cr.fill()
        # cr.new_sub_path() 
        # cr.arc(p1[0], p1[1], size, 0, math.pi / 2)
        # cr.new_sub_path() 
        # cr.arc(p2[0], p2[1], size, math.pi / 2, math.pi)
        # cr.new_sub_path()
        # cr.arc(p3[0], p3[1], size, math.pi, math.pi * 3 / 2)
        # cr.new_sub_path()
        # cr.arc(p4[0], p4[1], size, math.pi * 3 / 2, 0)
        cr.fill()
        return

    def write_planet_name(cr, x, y, radius, name, type="planet"):
        if type == "planet":
            x1 = x + radius + 20
            y1 = y - 10
        elif type == "moon":
            x1 = x + radius + 35
            y1 = y - 10
        elif type == "rings":
            x1 = x + radius + 20
            y1 = y - 10
        elif type == "belt":
            x1 = x
            y1 = y - radius - 10
        cr.close_path()
        cr.set_font_size(30)
        cr.select_font_face("GeosansLight-NMS", cairo.FONT_SLANT_OBLIQUE, cairo.FONT_WEIGHT_BOLD)
        cr.set_source_rgba(1, 1, 1, 0.8)
        cr.move_to(x1, y1)
        cr.show_text(name.upper())
        cr.move_to(x, y)
        cr.set_source_rgba(0, 0, 0, 0.0)
        return


    DOWNLOAD = False
    WIDTH = 1080
    HEIGHT = 1920

    ORBIT = True
    LINE = True

    RINGS = True
    MOONS = True
    BELTS = True
    STARFIELD = True
    BINARY = True
    BLACKHOLES = True
    SKIPS = True

    GRADIENTS = True

    STARS = 500
    BORDERSIZE = 50
    NOISE = 0.05

    seed = uuid.uuid4()

    if context.args:
        if "-help" in context.args:
            await update.message.reply_html("<code>/stars 1500 2000</code> (larghezza e altezza) come primi due parametri per specificare una dimensione di rendering\n<code>-seed [stringa]</code> per specificare un seed\n<code>-download</code> per farsi mandare il file full-res\n<code>-tinyborder</code> per un bordo più piccolo\n<code>-noborder</code> per eliminare il bordo completamente\n<code>-nostars</code> per non generare le stelline dietro\n<code>-origin</code> disattiva tutte le feature randomiche e lascia solo i pianeti\n<code>-help</code> visualizza questo messaggio")
            return

        if "-download" in context.args:
            DOWNLOAD = True

        if "-seed" in context.args:
            i = context.args.index("-seed")
            seed = context.args[i + 1]  

        if "-nostars" in context.args:
            STARFIELD = False

        if "-origin" in context.args:
            STARFIELD = False
            BELTS = False
            MOONS = False
            RINGS = False
            BINARY = False
            BLACKHOLES = False
            SKIPS = True

        if "-noborder" in context.args:
            BORDERSIZE = 0

        if "-tinyborder" in context.args:
            BORDERSIZE = 5

        if len(context.args) >= 2 and context.args[0].isdigit() and context.args[1].isdigit():
            if int(context.args[0]) < 500 or int(context.args[1]) < 500 or int(context.args[0]) + int(context.args[1]) > 10000:
                update.message.reply_text("Troppo o troppo poco! Minimo 500x500, e le dimensioni sommate non possono superare 10000")
                return
            WIDTH = int(context.args[0])
            HEIGHT = int(context.args[1])

    random.seed(str(seed))
    # print(f"Seed: {str(seed)}")
    await printlog(update, "crea un sistema solare con il seed", str(seed))
    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} crea un sistema di stelle e pianeti unico, seed: {str(seed)}')


    SUNSIZE = random.randint(50, 400)

    width, height = WIDTH, HEIGHT
    border_size = BORDERSIZE
    sun_size = SUNSIZE
    system_name = generate_system()
    planets_list = f"<b>· {system_name.upper()} ·</b>\n<i>{random.randint(15, 10000)} UA</i>\n\n"


    ims = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(ims)

    # Sfondo
    bg_min = 0.05
    bg_max = 0.2
    bg_color = (random_bg_color(bg_min, bg_max), random_bg_color(bg_min, bg_max), random_bg_color(bg_min, bg_max),)

    draw_background(cr, *bg_color, width, height)

    # Starfield
    if STARFIELD:
        for _ in range(STARS):
            star_size = random.randint(1, 30)
            star_x = random.randint(0, 6000)
            star_y = random.randint(0, 6000)
            if star_size < 10:
                draw_circle_fill(cr, star_x, star_y, star_size, 1, 1, 1, a=random.uniform(0.2, 0.4))
            else:
                draw_star(cr, star_x, star_y, star_size, 1, 1, 1, a=random.uniform(0.2, 0.4))

    # Stella
    sun_color = random.choice(list_of_sun_colors)
    sun_center = height - border_size
    sun_r, sun_g, sun_b = sun_color[0] / 255.0, sun_color[1] / 255.0, sun_color[2] / 255.0

    if random.randint(1, 100) < 30 and BLACKHOLES:
        draw_black_hole2(cr, width / 2, sun_center, sun_size, sun_r, sun_g, sun_b, a=1.0, gradient=True)
    else:
        if sun_size > 300 and random.randint(1, 100) > 10 and BINARY:  # binary
            BINARY_PADDING = 5
            sun_color_1 = random.choice(list_of_sun_colors)
            sun_color_2 = random.choice(list_of_sun_colors)
            sun_r_1, sun_g_1, sun_b_1 = sun_color_1[0] / 255.0, sun_color_1[1] / 255.0, sun_color_1[2] / 255.0
            sun_r_2, sun_g_2, sun_b_2 = sun_color_2[0] / 255.0, sun_color_2[1] / 255.0, sun_color_2[2] / 255.0
            ratio = random.uniform(0.1, 0.9)
            r1 = sun_size * ratio
            r2 = sun_size * (1 - ratio)
            # draw_circle_fill(cr, ((width / 2) - (sun_size - r1)), sun_center, int(r1 * 0.9), sun_r_1, sun_g_1, sun_b_1, a=1, gradient=True)
            draw_sun(cr, ((width / 2) - (sun_size - r1)), sun_center, int(r1 * 0.9), sun_r_1, sun_g_1, sun_b_1, a=1, gradient=True)
            # draw_circle_fill(cr, ((width / 2) + (sun_size - r2)), sun_center, int(r2 * 0.9), sun_r_2, sun_g_2, sun_b_2, a=1, gradient=True)
            draw_sun(cr, ((width / 2) + (sun_size - r2)), sun_center, int(r2 * 0.9), sun_r_2, sun_g_2, sun_b_2, a=1, gradient=True)
        else:
            # draw_circle_fill(cr, width / 2, sun_center, sun_size, sun_r, sun_g, sun_b, gradient=True)
            draw_sun(cr, width / 2, sun_center, sun_size, sun_r, sun_g, sun_b, gradient=True)

    distance_between_planets = 20
    last_center = sun_center
    last_size = sun_size
    last_color = sun_color

    min_size = 20
    max_size = 150


    for x in range(1, 20):
        distance_between_planets = random.randint(20, 100)
        next_size = random.randint(min_size, max_size)
        next_center = last_center - last_size - (next_size * 2) - distance_between_planets

        # Seleziono un colore random
        rand_color = random.choice(list_of_colors)
        while (rand_color is last_color):
            rand_color = random.choice(list_of_colors)
        r, g, b = rand_color[0] / 255.0, rand_color[1] / 255.0, rand_color[2] / 255.0

        if not(next_center - next_size < border_size):
            if random.randint(0, 100) <= 10 and SKIPS:  # SKIP!
                if context.args:
                    if "-star" in context.args:
                        draw_star(cr, width / 2, next_center, next_size, 1, 1, 1)
                last_color = rand_color
                last_center = next_center
                last_size = next_size
                continue
            p_name = generate_planet_name()
            planets_list += f"— {p_name}\n"
            planet_size = next_size
            if random.randint(0, 100) <= 30 and planet_size >= 50 and BELTS:   # asteroid belt
                # draw_orbit(cr, next_size, width / 2, sun_center, height - next_center - border_size, r, g, b, a=0.05)  # sfondo
                belt_radius_min = int(height - next_center - border_size - (planet_size / 2))
                belt_radius_max = int(height - next_center - border_size + (planet_size / 2))
                # draw_orbit(cr, 2, width / 2, sun_center, belt_radius_min, r, g, b, a=1)  # bordi netti - inferiore
                # draw_orbit(cr, 2, width / 2, sun_center, belt_radius_max, r, g, b, a=1)  # bordi netti - superiore
                belt_points = []
                for x in range(belt_radius_min, belt_radius_max + 1):
                    belt_points += get_point_on_circle(width / 2, sun_center, x, n=int(belt_radius_max))
                # print(len(belt_points))
                density = 2 * belt_radius_max
                for point in random.choices(belt_points, k=density):
                    asteroid_size = random.randint(0, int(belt_radius_max / random.randint(100, 150)))
                    # asteroid_size = 1
                    draw_circle_fill(cr, point[0], point[1], asteroid_size, r, g, b, a=random.uniform(0.5, 1))
                # write_planet_name(cr=cr, x=width / 2, y=next_center, radius=planet_radius, name=p_name, type="belt")


                last_color = rand_color
                last_center = next_center
                last_size = next_size
                BELTS = False
                continue

            # Planets Generation
            if ORBIT:
                draw_orbit(cr, random.randint(4, max(4, round(planet_size / 10))), width / 2, sun_center, height - next_center - border_size, r, g, b, a=random.uniform(0.5, 1))

            elif LINE:
                cr.move_to(border_size * 2, next_center)
                cr.line_to(width - (border_size * 2), next_center)
                cr.stroke()

            # Padding
            draw_circle_fill(cr, width / 2, next_center, next_size + 8, *bg_color)  # vuoto

            planet_type = random.choices(["rings", "moons", "normal"], weights=(25, 25, 50), k=1)[0]
            planet_radius = next_size

            if planet_type == "rings" and RINGS and planet_radius >= 50:
                planet_size = round(next_size * random.uniform(0.2, 0.5))  # il pianeta è il 20-50% della dimensione totale.
                draw_circle_fill(cr, width / 2, next_center, planet_size, r, g, b, gradient=True)  # pianeta
                empty_space = round(next_size * random.uniform(0.05, 0.2))  # il buffer è il 5-20% della dimensione totale.
                space_remaining = next_size - planet_size - empty_space
                n_rings = random.randint(1, 4)
                rings_list = get_random_gaps_segments(space_remaining, n_rings)
                ring_start = planet_size + empty_space
                for i, ring_size in enumerate(rings_list):
                    if i % 2 == 0:  # è pari, segment
                        draw_ring(cr, x=width / 2, y=next_center, rad_min=ring_start, rad_max=ring_start + ring_size, r=r, g=g, b=b, a=random.uniform(0.1, 1), gradient=True)
                    else:   # gap
                        pass
                    ring_start += ring_size
                # write_planet_name(cr=cr, x=width / 2, y=next_center, radius=planet_radius, name=p_name, type="rings")

            elif planet_type == "moons" and MOONS and planet_radius >= 50:
                n_moons = random.randint(1, 3)
                for i in range(n_moons):
                    moon_radius = round(planet_radius * random.uniform(0.1, 0.3))  # la luna è il 10%-30% del pianeta
                    orbit_radius = planet_radius + moon_radius + (10 * (i + 1))  # orbita sempre più grande ogni luna
                    moon_pos = get_point_on_circle(width / 2, next_center, orbit_radius, n=5)[i + 3]  # seleziono n posizioni sull'orbita e piazzo le lune in ordine
                    # moon_pos = random.choice(circle_points(xc=width / 2, yc=next_center, radius=orbit_radius))  # scelgo una posizione a caso dall'orbita
                    mr, mg, mb = r + random.uniform(-0.1, 0.1), g + random.uniform(-0.1, 0.1), b + random.uniform(-0.1, 0.1)  # modifico un po' il colore
                    draw_orbit(cr, 1, width / 2, next_center, orbit_radius, r=mr, g=mg, b=mb)  # mi disegno l'orbita della luna
                    draw_circle_fill(cr=cr, x=moon_pos[0], y=moon_pos[1], radius=moon_radius, r=mr, g=mg, b=mb, gradient=True)  # disegno luna
                draw_circle_fill(cr=cr, x=width / 2, y=next_center, radius=planet_radius, r=r, g=g, b=b, gradient=True)
                # write_planet_name(cr=cr, x=width / 2, y=next_center, radius=planet_radius, name=p_name, type="moon")

            else:
                draw_circle_fill(cr=cr, x=width / 2, y=next_center, radius=planet_radius, r=r, g=g, b=b, gradient=True)
                # write_planet_name(cr=cr, x=width / 2, y=next_center, radius=planet_radius, name=p_name, type="planet")

            last_color = rand_color
            last_center = next_center
            last_size = next_size
            if planet_type == "moons" and MOONS and planet_radius >= 50:
                last_size = orbit_radius

    draw_border(cr, border_size, sun_r, sun_g, sun_b, width, height)
    image_path = f'images/Stars-{str(width)}x{str(height)}.png'
    ims.write_to_png(image_path)
    
    if BORDERSIZE >= 20:
        img = Image.open(image_path)
    
        font_size = BORDERSIZE - 10

        rgb_bgcolor = tuple(int(x) for x in bg_color)

        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype('fonts/geonms-font.ttf', font_size)

        anchor = (int(WIDTH / 2), int((HEIGHT - (BORDERSIZE / 2))))

        draw.text(anchor, system_name.upper(), font=font, anchor="mm", fill=rgb_bgcolor, stroke_width=0)
        
        img.save(image_path)
    await context.bot.send_chat_action(chat_id=update.message.chat.id, action=ChatAction.UPLOAD_PHOTO)
    planets_list += f"\nSeed:\n<code>{seed}</code>"
    # from wand.image import Image

    # with Image(filename=image_path) as wandimg:
    #     wandimg.noise("poisson", attenuate=50, channel="gray")
    #     wandimg.save(filename=image_path)
        # print(" ".join(command))
        # subprocess.check_call(command)
    if DOWNLOAD:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(image_path, 'rb'), caption=planets_list, parse_mode='HTML')
        return

    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(image_path, 'rb'), caption=f"<b>· {system_name.upper()} ·</b>\n<code>{seed}</code>", parse_mode='HTML')
    return



async def launches(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def delta_to_string(td):
        secs = abs(td).total_seconds()
        days, rem = divmod(secs, 86400)  # Seconds per day: 24 * 60 * 60
        hours, rem = divmod(rem, 3600)  # Seconds per hour: 60 * 60
        mins, secs = divmod(rem, 60)
        return '{:02}:{:02}:{:02}:{:02}'.format(int(days), int(hours), int(mins), int(secs))

    def utc_to_local(utc_dt):
        local_tz = pytz.timezone('Europe/Rome')
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_tz.normalize(local_dt) 

    if await no_can_do(update, context):
        return

    # print(f'{get_now()} {await get_display_name(update.effective_user)} in {await get_chat_name(update.message.chat.id)} chiede la lista dei lanci')
    await printlog(update, "chiede la lista dei lanci spaziali")

    r = requests.get("https://ll.thespacedevs.com/2.2.0/launch/?mode=detailed&name=&slug=&rocket__configuration__name=&rocket__configuration__id=&status=1&rocket__spacecraftflight__spacecraft__name=&rocket__spacecraftflight__spacecraft__name__icontains=&rocket__spacecraftflight__spacecraft__id=&rocket__configuration__manufacturer__name=&rocket__configuration__manufacturer__name__icontains=&rocket__configuration__full_name=&rocket__configuration__full_name__icontains=&mission__orbit__name=&mission__orbit__name__icontains=&r_spacex_api_id=&net__gt=&net__lt=&net__gte=&net__lte=&window_start__gt=&window_start__lt=&window_start__gte=&window_start__lte=&window_end__gt=&window_end__lt=&window_end__gte=&window_end__lte=&last_updated__gte=&last_updated__lte=")

    launches = r.json()
    # print(launches)
    try:
        detail = launches['detail']
        if detail:
            print(launches)
            if detail.startswith("Request was throttled"):
                await update.message.reply_text(detail)
                return
    except KeyError:
        pass

    if not launches:
        await update.message.reply_text("Errore generico.")
        return

    messaggio = ""

    for n in range(3):
        try:
            lancio = launches["results"][n]
        except IndexError:
            continue
        infourl = f"https://spacelaunchnow.me/launch/{lancio['slug']}"
        moreinfo = f'[<a href="{infourl}">More info</a>]\n'
        launchtime = datetime.strptime(lancio['net'], '%Y-%m-%dT%H:%M:%S%z')
        local_launch_time = utc_to_local(launchtime)
        now = datetime.now(timezone.utc)
        delta = launchtime - now

        try:
            link = lancio['vidURLs'][0]['url']
            videolink = f' [<a href="{link}">Stream</a>]'
        except (IndexError, KeyError):
            videolink = ""

        if lancio['mission']:
            tipo = lancio['mission']['type']
            desc = lancio['mission']['description']
        else:
            tipo = "Sconosciuto"
            desc = "Missione sconosciuta"

        name = lancio['name']
        messaggio += f"<b>[{tipo}] {name}</b>\n"
        messaggio += f"<i>{local_launch_time.strftime('%Y-%m-%d %H:%M:%S')} (Rome) - {launchtime.strftime('%Y-%m-%d %H:%M:%S')} (UTC)</i>\n"
        messaggio += f"Al lancio: <code>-{delta_to_string(delta)}</code>{videolink}\n"
        desc = desc.replace("\n", " ")
        desc = f"{desc[:200]}... {moreinfo}"

        if n == 2:
            messaggio += f"{desc}"
        else:
            messaggio += f"{desc}\n\n"

    await update.message.reply_html(messaggio, disable_web_page_preview=True)
