import html
import math
import pprint
import random
import tempfile
import uuid
from datetime import datetime, timezone

import cairo
import numpy as np
import pytz
import requests
from dataclassy import dataclass
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

import config
from utils import no_can_do, printlog


@dataclass
class StelleResult:
    raw_dict: dict
    system_name: str
    system_distance: str
    description: str
    planet_list: str
    seed: str
    file: tempfile._TemporaryFileWrapper

async def make_solar_system(update=None, download:bool=False, width:int=1080, height:int=1920, orbit:bool=True, line:bool=False,
                            rings:bool=True, moons:bool=True, belts:bool=True, starfield:bool=True, binary:bool=True,
                            blackholes:bool=True, skips:bool=True, gradients:bool=True, textures:bool=True,
                            stars:int=50, bordersize:int=50, noise:int=3, seed=None):

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
            system_name += " System"

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

    def draw_orbit(cr, line, x, y, radius, r, g, b, a=1.0, lato=None):
        cr.set_source_rgba(r, g, b, a)
        cr.set_line_width(line)

        if lato == 'sx':
            cr.arc_negative(x, y, radius, 270 * (math.pi / 180), 90 * (math.pi / 180))

        elif lato == 'dx':
            cr.arc(x, y, radius, 90 * (math.pi / 180), 270 * (math.pi / 180))

        else:
            cr.arc(x, y, radius, 0, 2 * math.pi)
        # cr.arc(x, y, radius, 0, math.pi)
       
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

    def draw_planet(cr, x, y, radius, r, g, b, a=1.0, gradient=False, texture_file=None):

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

        if TEXTURES and random.randint(1, 100) < 40:
            texture_file = random.choice(list_of_planet_textures)

        if texture_file:
            # Load the texture
            texture = cairo.ImageSurface.create_from_png(f'images/planet_textures/{texture_file}.png')

            # Set the composition operator to multiply
            cr.set_operator(cairo.Operator.MULTIPLY)
           
            # Create a pattern from the texture
            texture_pattern = cairo.SurfacePattern(texture)

            texture_pattern.set_extend(cairo.EXTEND_REPEAT)
            texture_pattern.set_filter(cairo.FILTER_NEAREST)

            # Matrix transformation: random rotation angle
            angle = math.radians(random.randint(1, 360))
            rotation_matrix = cairo.Matrix(
                math.cos(angle), math.sin(angle),
                -math.sin(angle), math.cos(angle),
                x - math.cos(angle) * x + math.sin(angle) * y,
                y - math.sin(angle) * x - math.cos(angle) * y
                )

            # Matrix transformation: scaling the texture to the planet
            texture_width, texture_height = 400, 400
            scale_factor = max(texture_width, texture_height) / (radius*2)
            scale_matrix = cairo.Matrix(scale_factor, 0, 0, scale_factor, 0, 0)

            # Matrix transformation: aligning the texture to the planet
            move_matrix = cairo.Matrix(1, 0, 0, 1, -x-radius, -y-radius)

            # Matrix transformation: combining all the transformations
            rotate_move_scale_matrix = rotation_matrix * move_matrix * scale_matrix
            texture_pattern.set_matrix(rotate_move_scale_matrix)


            # Apply the texture to the circle
            cr.set_source(texture_pattern)
            cr.arc(x, y, radius, 0, 2 * math.pi)
            cr.fill()

            # Set the composition operator back to default
            cr.set_operator(cairo.Operator.OVER)

            # Set the opacity of the texture
            cr.set_source_rgba(1, 1, 1, 0) # Set the color with alpha value (RGBA)
            cr.paint_with_alpha(0) # Set the opacity of the texture

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

    def get_random_points_on_circle(xc, yc, r, n=100):
        points_list = []
        for _ in range(0, n):
            angle = math.tau * random.random()
            p = (int(xc + r * math.cos(angle)), int(yc + r * math.sin(angle)))
            points_list.append(p)
        return points_list

    def get_uniform_points_on_circle(xc, yc, r, n=360):
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

    def asteroid_density(r, r_min, r_max, max_density):
        """
        Calculates the density of asteroids at a given distance r from the center of an asteroid belt.

        Args:
            r (float): distance from the center of the asteroid belt
            r_min (float): minimum radius of the asteroid belt
            r_max (float): maximum radius of the asteroid belt
            max_density (float): maximum density at the center of the belt

        Returns:
            float: density of asteroids at distance r
        """
        if r < r_min or r > r_max:
            return 1.0
        else:
            midpoint = (r_max - r_min) / 2.0 + r_min
            inner_range = 0.6 * (r_max - r_min) / 2.0
            if r <= midpoint - inner_range or r >= midpoint + inner_range:
                # Calculate the density at the edges of the belt using a modified
                # formula that gradually decreases the density from max_density to 1.0
                # as we move away from the center of the belt towards the edges.
                width = r_max - r_min
                density_range = max_density - 1.0
                peak_location = midpoint
                density = 1.0 + density_range * (math.exp(-((r - peak_location) ** 2) / (2 * ((width / 4) ** 2))))
                density = min(density, max_density)
                density = max(density, 1.0)
            else:
                # The density is constant within the inner 70% of the belt.
                density = max_density
            return density

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

    list_of_colors = [
        (145, 185, 141), (229, 192, 121), (210, 191, 88), (140, 190, 178), (255, 183, 10),
        (189, 190, 220), (221, 79, 91), (16, 182, 98), (227, 146, 80), (241, 133, 123),
        (110, 197, 233), (235, 205, 188), (197, 239, 247), (190, 144, 212), (41, 241, 195),
        (101, 198, 187), (255, 246, 143), (243, 156, 18), (189, 195, 199), (243, 241, 239)
        ]

    list_of_sun_colors = [
        (255, 95, 83), (253, 209, 162), (255, 243, 161), (252, 255, 212),
        (248, 247, 253), (201, 216, 255), (154, 175, 255)
        ]

    list_of_planet_textures = ['craters', 'fibers', 'nubi', 'perlin_poly', 'stripes', 'voronoi', 'splat', 'splot']

    stelle = {}
   
    WIDTH = width
    HEIGHT = height

    ORBIT = orbit
    LINE = line

    RINGS = rings
    MOONS = moons
    BELTS = belts
    STARFIELD = starfield
    BINARY = binary
    BLACKHOLES = blackholes
    SKIPS = skips

    GRADIENTS = gradients
    TEXTURES = textures

    STARS = stars
    BORDERSIZE = bordersize
    NOISE = noise

    if not seed:
        seed = uuid.uuid4()


    random.seed(str(seed))
    if update:
        await printlog(update, "crea un sistema solare con il seed", str(seed))

    SUNSIZE = random.randint(50, 400)

    width, height = WIDTH, HEIGHT
    border_size = BORDERSIZE
    sun_size = SUNSIZE
    system_name = generate_system()
    system_distance = f"{random.randint(15, 10000)} UA"
    description = f"<b>· {system_name.upper()} ·</b>\n<i>{system_distance}</i>\n\n"
    planet_list = ""

    stelle['seed'] = str(seed)
    stelle['system_name'] = system_name
    stelle['settings'] = {}
    stelle['settings']['width'] = WIDTH
    stelle['settings']['height'] = HEIGHT
    stelle['settings']['border_size'] = BORDERSIZE
    stelle['settings']['orbit'] = ORBIT
    stelle['settings']['line'] = LINE
    stelle['settings']['rings'] = RINGS
    stelle['settings']['moons'] = MOONS
    stelle['settings']['belts'] = BELTS
    stelle['settings']['starfield'] = STARFIELD
    stelle['settings']['binary'] = BINARY
    stelle['settings']['blackholes'] = BLACKHOLES
    stelle['settings']['skips'] = SKIPS
    stelle['settings']['gradients'] = GRADIENTS
    stelle['settings']['textures'] = TEXTURES
    stelle['settings']['n_background_stars'] = STARS


    ims = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(ims)

    # Sfondo
    bg_min = 0.05
    bg_max = 0.2
    bg_color = (random_bg_color(bg_min, bg_max), random_bg_color(bg_min, bg_max), random_bg_color(bg_min, bg_max),)

    draw_background(cr, *bg_color, width, height)
    stelle['background'] = {}
    stelle['background']['color'] = bg_color

    # Starfield
    if STARFIELD:
        # stelle['background']['stars'] = []
        for _ in range(STARS):
            star_size = random.randint(1, 30)
            star_x = random.randint(0, WIDTH)
            star_y = random.randint(0, HEIGHT)
            if star_size < 10:
                draw_circle_fill(cr, star_x, star_y, star_size, 1, 1, 1, a=random.uniform(0.2, 0.4))
                # stelle['background']['stars'].append({'x': star_x, 'y': star_y, 'size': star_size, 'type': 'circle'})
            else:
                draw_star(cr, star_x, star_y, star_size, 1, 1, 1, a=random.uniform(0.2, 0.4))
                # stelle['background']['stars'].append({'x': star_x, 'y': star_y, 'size': star_size, 'type': 'star'})

    # Stella
    sun_color = random.choice(list_of_sun_colors)
    sun_center = height - border_size
    sun_r, sun_g, sun_b = sun_color[0] / 255.0, sun_color[1] / 255.0, sun_color[2] / 255.0

    if random.randint(1, 100) < 30 and BLACKHOLES:
        stelle['star'] = {'type': 'blackhole', 'color': sun_color, 'size': sun_size, 'center': sun_center}
        draw_black_hole2(cr, width / 2, sun_center, sun_size, sun_r, sun_g, sun_b, a=1.0, gradient=True)
    else:
        if sun_size > 300 and random.randint(1, 100) > 10 and BINARY:
              # binary
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
            stelle['star'] = {'type': 'binary', 'color1': sun_color_1, 'color2': sun_color_2, 'size1': int(r1 * 0.9), 'size2': int(r2 * 0.9), 'center1': ((width / 2) - (sun_size - r1)), 'center2': ((width / 2) + (sun_size - r2))}
        else:
            # draw_circle_fill(cr, width / 2, sun_center, sun_size, sun_r, sun_g, sun_b, gradient=True)
            draw_sun(cr, width / 2, sun_center, sun_size, sun_r, sun_g, sun_b, gradient=True)
            stelle['star'] = {'type': 'sun', 'color': sun_color, 'size': sun_size, 'center': sun_center}

    distance_between_planets = 20
    last_center = sun_center
    last_size = sun_size
    last_color = sun_color

    min_size = 20
    max_size = 150

    # print(f"Sole: \t{time.perf_counter() - start}")
    stelle['planets'] = []
    for x in range(1, 20):
        planet = {}

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
                # if context.args:
                #     if "-star" in context.args:
                #         draw_star(cr, width / 2, next_center, next_size, 1, 1, 1)
                last_color = rand_color
                last_center = next_center
                last_size = next_size
                planet['type'] = 'skip'
                stelle['planets'].append(planet)
                continue
            p_name = generate_planet_name()
            planet['name'] = p_name

            planet_list += f"— {p_name}\n"
            planet_size = next_size
            if random.randint(0, 100) <= 30 and planet_size >= 50 and BELTS:  # asteroid belt
                # draw_orbit(cr, next_size, width / 2, sun_center, height - next_center - border_size, r, g, b, a=0.05)  # sfondo
                # draw_orbit(cr, 2, width / 2, sun_center, belt_radius_min, r, g, b, a=1)  # bordi netti - inferiore
                # draw_orbit(cr, 2, width / 2, sun_center, belt_radius_max, r, g, b, a=1)  # bordi netti - superiore

                belt_radius_min = int(height - next_center - border_size - (planet_size / 2))
                belt_radius_max = int(height - next_center - border_size + (planet_size / 2))

                belt_points = []
                midpoint = (belt_radius_max - belt_radius_min) / 2.0 + belt_radius_min
                inner_range = 0.6 * (belt_radius_max - belt_radius_min) / 2.0

                planet['type'] = 'asteroid_belt'
                planet['details'] = {}
                planet['details']['radius_min'] = belt_radius_min
                planet['details']['radius_max'] = belt_radius_max
                planet['pos'] = (width / 2, midpoint)

                for x in range(belt_radius_min, belt_radius_max + 1, 2):
                    max_density = 120
                    density = int(asteroid_density(x, belt_radius_min, belt_radius_max, max_density))
                   
                    asteroid_size_min = 2
                    asteroid_size_max = 3
                    belt_points = get_random_points_on_circle(width / 2, sun_center, x, n=density)

                    for point in belt_points:
                        asteroid_size = random.randint(asteroid_size_min, asteroid_size_max)
                        if x <= midpoint - inner_range or x >= midpoint + inner_range:  # bordi esterni
                            asteroid_size = asteroid_size / 2
                            draw_circle_fill(cr, point[0], point[1], asteroid_size, r, g, b, a=random.uniform(0.4, 0.8))
                        else:
                            draw_circle_fill(cr, point[0], point[1], asteroid_size, r, g, b, a=random.uniform(0.8, 1))


                last_color = rand_color
                last_center = next_center
                last_size = next_size
                BELTS = False
                stelle['planets'].append(planet)
                continue

            # Planets Generation
            if ORBIT:
                draw_orbit(cr, random.randint(4, max(4, round(planet_size / 10))), width / 2, sun_center, height - next_center - border_size, r, g, b, a=random.uniform(0.5, 1))

            elif LINE:
                cr.move_to(border_size * 2, next_center)
                cr.line_to(width - (border_size + 10), next_center)
                cr.stroke()

            # Padding
            draw_circle_fill(cr, width / 2, next_center, next_size + 8, *bg_color)

            planet_type = random.choices(["rings", "moons", "normal"], weights=(25, 25, 50), k=1)[0]
            planet_radius = next_size

            if planet_type == "rings" and RINGS and planet_radius >= 50:

                planet['type'] = 'rings'
                planet['pos'] = (width / 2, next_center)
                planet['radius'] = planet_radius
                planet['details'] = {}
                planet['details']['size'] = planet_size
                planet['details']['color'] = (r, g, b)

                planet_size = round(next_size * random.uniform(0.2, 0.5))  # il pianeta è il 20-50% della dimensione totale.
                draw_planet(cr, width / 2, next_center, planet_size, r, g, b, gradient=True)  # pianeta
                empty_space = round(next_size * random.uniform(0.05, 0.2))  # il buffer è il 5-20% della dimensione totale.
                space_remaining = next_size - planet_size - empty_space
                n_rings = random.randint(1, 4)

                planet['details']['empty_space'] = empty_space
                planet['details']['n_rings'] = n_rings
                planet['rings'] = []

                rings_list = get_random_gaps_segments(space_remaining, n_rings)
                ring_start = planet_size + empty_space

                for i, ring_size in enumerate(rings_list):
                    if i % 2 == 0:  # è pari, segment
                        draw_ring(cr, x=width / 2, y=next_center, rad_min=ring_start, rad_max=ring_start + ring_size, r=r, g=g, b=b, a=random.uniform(0.1, 1), gradient=True)
                        planet['rings'].append({'type': 'segment', 'radius_min': ring_start, 'radius_max': ring_start + ring_size, 'color': (r, g, b)})
                    else:   # gap
                        pass
                    ring_start += ring_size
                # write_planet_name(cr=cr, x=width / 2, y=next_center, radius=planet_radius, name=p_name, type="rings")

                stelle['planets'].append(planet)

            elif planet_type == "moons" and MOONS and planet_radius >= 50:
                n_moons = random.randint(1, 3)

                planet['type'] = 'moons'
                planet['pos'] = (width / 2, next_center)
                planet['radius'] = planet_radius
                planet['details'] = {}
                planet['details']['size'] = planet_radius * 2
                planet['details']['color'] = (r, g, b)
                planet['details']['n_moons'] = n_moons
                planet['moons'] = []

                moons = []
                for i in range(n_moons):
                    moon_radius = round(planet_radius * random.uniform(0.1, 0.3))  # la luna è il 10%-30% del pianeta
                    orbit_radius = planet_radius + moon_radius + (10 * (i + 1))  # orbita sempre più grande ogni luna
                    moon_pos = get_uniform_points_on_circle(width / 2, next_center, orbit_radius, n=5)[i + 3]  # seleziono n posizioni sull'orbita e piazzo le lune in ordine
                    mr, mg, mb = r + random.uniform(-0.1, 0.1), g + random.uniform(-0.1, 0.1), b + random.uniform(-0.1, 0.1)  # modifico un po' il colore
                    moons.append((moon_radius, orbit_radius, moon_pos, mr, mg, mb))

                    planet['moons'].append({'pos': moon_pos, 'radius': moon_radius, 'orbit_radius': orbit_radius, 'color': (mr, mg, mb)})

                for m in moons:
                    moon_radius, orbit_radius, moon_pos, mr, mg, mb = m
                    draw_orbit(cr, 2, width / 2, next_center, orbit_radius, r=mr, g=mg, b=mb)  # mi disegno l'orbita della luna

                for m in moons:
                    moon_radius, orbit_radius, moon_pos, mr, mg, mb = m
                    draw_circle_fill(cr=cr, x=moon_pos[0], y=moon_pos[1], radius=moon_radius, r=mr, g=mg, b=mb, gradient=True)  # disegno luna

                draw_planet(cr=cr, x=width / 2, y=next_center, radius=planet_radius, r=r, g=g, b=b, gradient=True)
                # write_planet_name(cr=cr, x=width / 2, y=next_center, radius=planet_radius, name=p_name, type="moon")

                stelle['planets'].append(planet)


            else:
                planet['type'] = 'normal'
                planet['pos'] = (width / 2, next_center)
                planet['radius'] = planet_radius
                planet['details'] = {}
                planet['details']['size'] = planet_radius * 2
                planet['details']['color'] = (r, g, b)

                draw_planet(cr=cr, x=width / 2, y=next_center, radius=planet_radius, r=r, g=g, b=b, gradient=True)
                # write_planet_name(cr=cr, x=width / 2, y=next_center, radius=planet_radius, name=p_name, type="planet")

                stelle['planets'].append(planet)

            last_color = rand_color
            last_center = next_center
            last_size = next_size
            if planet_type == "moons" and MOONS and planet_radius >= 50:
                last_size = orbit_radius
   
    draw_border(cr, border_size, sun_r, sun_g, sun_b, width, height)
    fp = tempfile.NamedTemporaryFile(suffix='.png')

    image_path = fp.name
    ims.write_to_png(image_path)

    img = Image.open(image_path)
    if BORDERSIZE >= 20:
   
        font_size = BORDERSIZE - 10

        rgb_bgcolor = tuple(int(x) for x in bg_color)

        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype('fonts/geonms-font.ttf', font_size)

        anchor = (int(WIDTH / 2), int((HEIGHT - (BORDERSIZE / 2))))

        draw.text(anchor, system_name.upper(), font=font, anchor="mm", fill=rgb_bgcolor, stroke_width=0)
   
    if NOISE:
        # Load image
        img = np.array(img)

        # Define mean and standard deviation
        mean = 0
        stddev = NOISE

        # Create grayscale Gaussian noise array and add it to image
        noise = np.random.normal(mean, stddev, img.shape[:2])
        noisy_img = np.zeros(img.shape, dtype=np.uint8)
        noisy_img[:,:,0] = np.clip(img[:,:,0] + noise, 0, 255)
        noisy_img[:,:,1] = np.clip(img[:,:,1] + noise, 0, 255)
        noisy_img[:,:,2] = np.clip(img[:,:,2] + noise, 0, 255)

        # Convert to grayscale
        noisy_img_gray = np.dot(noisy_img[...,:3], [0.2989, 0.5870, 0.1140])

        # Add opacity to the noisy image
        alpha = np.random.randint(0, 255, img.shape[:2]).astype(np.uint8)
        noisy_img_gray = np.stack((noisy_img_gray,)*3, axis=-1)
        noisy_img_gray = np.concatenate((noisy_img_gray, alpha[:,:,np.newaxis]), axis=2)

        # Save the noisy image
        noisy_img_pil = Image.fromarray(noisy_img)
        img = noisy_img_pil

    img.save(image_path)
    description += planet_list
    description += f"\nSeed:\n<code>{seed}</code>"

    res: StelleResult = StelleResult(
        raw_dict = stelle,
        system_name = system_name,
        system_distance = system_distance,
        description = description,
        planet_list = planet_list,
        seed = seed,
        file = fp
    )
    return res

async def solarsystem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await no_can_do(update, context):
        return

    if update.effective_user.id not in config.ADMINS and update.effective_chat.id == config.ID_TIMELINE:
        return

    kwargs = {}

    if context.args:
        if "-help" in context.args:
            await update.message.reply_html("<code>/stars 1500 2000</code> (larghezza e altezza) come primi due parametri per specificare una dimensione di rendering\n<code>-seed [stringa]</code> per specificare un seed\n<code>-download</code> per farsi mandare il file full-res\n<code>-tinyborder</code> per un bordo più piccolo\n<code>-noborder</code> per eliminare il bordo completamente\n<code>-nostars</code> per non generare le stelline dietro\n<code>-origin</code> disattiva tutte le feature randomiche e lascia solo i pianeti\n<code>-help</code> visualizza questo messaggio")
            return

        if "-download" in context.args:
            kwargs['download'] = True

        if "-seed" in context.args:
            i = context.args.index("-seed")
            seed = context.args[i + 1]
            kwargs['seed'] = seed

        if "-nostars" in context.args:
            kwargs['starfield'] = False

        if "-origin" in context.args:
            kwargs['starfield'] = False
            kwargs['belts'] = False
            kwargs['moons'] = False
            kwargs['rings'] = False
            kwargs['binary'] = False
            kwargs['blackholes'] = False
            kwargs['skips'] = True


        if "-noborder" in context.args:
            kwargs['bordersize'] = 0

        if "-tinyborder" in context.args:
            kwargs['bordersize'] = 5

        if len(context.args) >= 2 and context.args[0].isdigit() and context.args[1].isdigit():
            if int(context.args[0]) < 500 or int(context.args[1]) < 500 or int(context.args[0]) + int(context.args[1]) > 10000:
                await update.message.reply_text("Troppo o troppo poco! Minimo 500x500, e le dimensioni sommate non possono superare 10000")
                return
            WIDTH = int(context.args[0])
            HEIGHT = int(context.args[1])
            kwargs['width'] = WIDTH
            kwargs['height'] = HEIGHT




    result: StelleResult = await make_solar_system(update, **kwargs)

    if result is None:
        await update.message.reply_message("Errore durante la generazione del sistema solare")
        return

    await context.bot.send_chat_action(chat_id=update.message.chat.id, action=ChatAction.UPLOAD_PHOTO)

    image_path = result.file.name
    system_name = result.system_name
    description = result.description
    seed = result.seed
    fp = result.file
    stelle = result.raw_dict


    if kwargs.get('download'):
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(image_path, 'rb'), caption=description, parse_mode='HTML')
    else:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(image_path, 'rb'), caption=f"<b>· {system_name.upper()} ·</b>\n<code>{seed}</code>", parse_mode='HTML')
   
    if '-raw' in context.args:

        rawtext = pprint.pformat(stelle, sort_dicts=False)
        rawtext = html.escape(rawtext)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"<pre>{rawtext}</pre>", parse_mode='HTML')
    fp.close()
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
