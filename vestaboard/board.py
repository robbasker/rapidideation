"""
How a message is laid out on the Vestaboard Note: which tile each character is,
word wrapping, centring, and the preview printed in the terminal.
"""

import re

ROWS = 3
COLS = 15

# Vestaboard identifies each character by a number.
CHAR_CODES = {" ": 0}
for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    CHAR_CODES[letter] = i + 1
for i, digit in enumerate("1234567890"):
    CHAR_CODES[digit] = i + 27
CHAR_CODES.update({
    "!": 37, "@": 38, "#": 39, "$": 40, "(": 41, ")": 42, "-": 44,
    "+": 46, "&": 47, "=": 48, ";": 49, ":": 50, "'": 52, '"': 53,
    "%": 54, ",": 55, ".": 56, "/": 59, "?": 60, "°": 62,
})

# Colour tiles, written in a message like {red}.
COLOR_CODES = {
    "red": 63, "orange": 64, "yellow": 65, "green": 66,
    "blue": 67, "violet": 68, "white": 69, "black": 70,
}
COLOR_SYMBOLS = {
    63: "🟥", 64: "🟧", 65: "🟨", 66: "🟩",
    67: "🟦", 68: "🟪", 69: "⬜", 70: "⬛",
}
CODE_TO_CHAR = {code: char for char, code in CHAR_CODES.items()}


def to_tiles(word):
    """Turn a word like 'HI{red}' into a list of tile codes."""
    tiles = []
    for part in re.split(r"(\{[a-z]+\})", word.lower()):
        if part.startswith("{") and part[1:-1] in COLOR_CODES:
            tiles.append(COLOR_CODES[part[1:-1]])
            continue
        for char in part.upper():
            if char not in CHAR_CODES:
                raise ValueError(f"The Vestaboard can't show the character '{char}'.")
            tiles.append(CHAR_CODES[char])
    return tiles


def wrap(message):
    """Split the message into lines of up to 22 tiles, breaking between words."""
    lines = []
    for paragraph in message.split("\n"):
        line = []
        for word in paragraph.split():
            tiles = to_tiles(word)
            if len(tiles) > COLS:
                raise ValueError(f"'{word}' is too long to fit on one line.")
            if line and len(line) + 1 + len(tiles) > COLS:
                lines.append(line)
                line = []
            line = line + [0] + tiles if line else tiles
        lines.append(line)
    if len(lines) > ROWS:
        raise ValueError(f"The message needs {len(lines)} lines but the board only has {ROWS}.")
    return lines


def build_board(message):
    """Return a 6 x 22 grid of tile codes with the message centred."""
    lines = wrap(message)
    top = (ROWS - len(lines)) // 2
    board = [[0] * COLS for _ in range(ROWS)]
    for i, line in enumerate(lines):
        left = (COLS - len(line)) // 2
        board[top + i][left:left + len(line)] = line
    return board


def preview(board):
    """Print the board in the terminal so you can check it before sending."""
    print("┌" + "─" * (COLS * 2) + "┐")
    for row in board:
        cells = []
        for code in row:
            if code in COLOR_SYMBOLS:
                cells.append(COLOR_SYMBOLS[code])
            else:
                cells.append(CODE_TO_CHAR.get(code, "?") + " ")
        print("│" + "".join(cells) + "│")
    print("└" + "─" * (COLS * 2) + "┘")
