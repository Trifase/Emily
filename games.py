
import random

import requests
from codetiming import Timer
from rich import print
from telegram import Update
from telegram.ext import ContextTypes

import config
from utils import no_can_do, printlog


async def sassocartaforbici(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await no_can_do(update, context):
        return

    lista = ['sasso', 'carta', 'forbici', 'lucertola', 'spock']

    if not context.args or (context.args[0].lower() not in lista):
        await update.message.reply_text("Devi scegliere uno tra: carta, sasso, forbici, lucertola, spock")
        return

    a = context.args[0].lower()
    b = random.choice(lista)

    winners = {
        "sasso": {
            "lucertola": "schiaccia la",
            "forbici": "rompe le"
        },
        "carta": {
            "sasso": "avvolge il",
            "spock": "invalida"
        },
        "forbici": {
            "carta": "tagliano la",
            "lucertola": "decapitano la"
        },
        "lucertola": {
            "carta": "mangia la",
            "spock": "avvelena"
        },
        "spock": {
            "forbici": "rompe le",
            "sasso": "vaporizza il"
        },
    }

    await printlog(update, "gioca a sasso carta forbici lucertola spock", f"{a.capitalize()} vs {b.capitalize()}")

    if a == b:
        await update.message.reply_text(f"Scelgo {b.capitalize()}!\n🌝 Pari!")
        return

    try:
        verbo = winners[a][b]
        await update.message.reply_text(f"Scelgo {b.capitalize()}!\n\n{a.capitalize()} {verbo} {b.capitalize()}\n✅ Hai vinto!")
        return
    except KeyError:
        verbo = winners[b][a]
        await update.message.reply_text(f"Scelgo {b.capitalize()}!\n\n{b.capitalize()} {verbo} {a.capitalize()}\n❌ Hai perso!")
        return

def sudoku():

    def get_sudoku(diff):
        url = "https://sudoku-board.p.rapidapi.com/new-board"

        querystring = {"diff":str(diff),"stype":"list","solu":"true"}

        headers = {
            "X-RapidAPI-Key": config.RAPIDAPI_KEY,
            "X-RapidAPI-Host": "sudoku-board.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring).json()
        puzzle = response['response']['unsolved-sudoku']
        for c in range(9):
            for r in range(9):
                if puzzle[c][r] == 0:
                    puzzle[c][r] = -1
        return puzzle

    def print_sudoku(puzzle):

        max_len = len(puzzle[0])
        # print(f"\n+{'---+' * max_len}")
        print()
        for c in range(max_len):
            if c == 0:
                pass
            elif c % 3 == 0:
                print(f"-{'----' * max_len}")
               
            print(' ', end='')
            for r in range(max_len):
                if (r == 0) or ((r+1) % 3 != 0) or (r == max_len-1):
                    if puzzle[c][r] < 0:
                        print('    ', end='')
                    else:
                        print(f' {puzzle[c][r]}  ', end='')

                else:
                    if puzzle[c][r] < 0:
                        print('   |', end='')
                    else:
                        print(f' {puzzle[c][r]} |', end='')

            # print(f"\n+{'---+' * max_len}")
            print()

    def find_next_empy_cell(puzzle):
        max_len = len(puzzle[0])

        for r in range(max_len):
            for c in range(max_len):
                if puzzle[r][c] == -1:  # It's empty
                    return r, c

        # Abbiamo riempito tutte le celle, assurdo
        return None, None

    def is_valid(puzzle, guess, row, col) -> bool:
        max_len = len(puzzle[0])

        # Horizontal Check
        if guess in puzzle[row]:
            return False

        # Vertical Check
        if guess in [puzzle[x][col] for x in range(max_len)]:
            return False

        # Square Check
        row_i = (row // 3) * 3
        col_i = (col // 3) * 3

        for r in range(row_i, row_i + 3):
            for c in range(col_i, col_i + 3):
                if puzzle[r][c] == guess:
                    return False
       
        return True

    def solve_sudoku(puzzle):
        row, col = find_next_empy_cell(puzzle)

        if row is None:  # Abbiamo riempito tutte le celle
            return True

        for guess in range(1, 10):
           
            if is_valid(puzzle, guess, row, col):
                puzzle[row][col] = guess

                if solve_sudoku(puzzle):
                    return True # Vinto

                puzzle[row][col] = -1

        # print_sudoku(puzzle)
        return False # unsolvable


    # 3x3

    # 6x6

    # 9x9
    sudoku9x9 = [
        [-1,  2,  3, -1, -1, -1, -1,  9,  7],
        [-1,  8, -1,  1, -1, -1, -1,  3,  6],
        [ 5,  6,  7, -1, -1, -1, -1, -1,  8],
        [-1,  1, -1, -1, -1, -1,  8,  7,  9],
        [ 3, -1,  8, -1,  9, -1,  6,  2, -1],
        [-1,  9,  6, -1, -1,  2,  4,  5, -1],
        [-1,  4, -1, -1, -1, -1, -1,  1, -1],
        [-1, -1, -1,  9, -1,  1,  7, -1, -1],
        [ 9, -1, -1,  5, -1, -1,  3,  6,  2]
        ]

    # hardest sudoku
    # https://abcnews.go.com/blogs/headlines/2012/06/can-you-solve-the-hardest-ever-sudoku

    # blank sudoku

    sudoku = sudoku9x9

    # get a new 9x9 solvable
    sudoku = get_sudoku(3)

    print_sudoku(sudoku)

    with Timer(name="solver"):
        solve_sudoku(sudoku)
        print_sudoku(sudoku)

# sudoku()