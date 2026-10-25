#!/usr/bin/env python3
"""
Send a custom message to your Vestaboard.

Examples:
    python3 send_message.py "Hello world"
    python3 send_message.py "Dinner at 7" --preview
    python3 send_message.py "{green} Welcome home {green}"

Only uses Python's built-in libraries, so there is nothing to install.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

API_URL = "https://cloud.vestaboard.com/"
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


def load_api_key():
    """Read the key from the VESTABOARD_API_KEY variable or the api_key.txt file."""
    key = os.environ.get("VESTABOARD_API_KEY")
    if key:
        return key.strip()
    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")
    if os.path.exists(key_file):
        with open(key_file) as f:
            return f.read().strip()
    return None


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


def send(board, api_key):
    request = urllib.request.Request(
        API_URL,
        data=json.dumps({"characters": board}).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Vestaboard-Token": api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.status, response.read().decode(errors="replace")


def main():
    parser = argparse.ArgumentParser(description="Send a message to your Vestaboard.")
    parser.add_argument("message", help='The message to show, e.g. "Hello world"')
    parser.add_argument("--preview", action="store_true",
                        help="Only show what the board would look like; don't send it")
    args = parser.parse_args()

    try:
        board = build_board(args.message.replace("\\n", "\n"))
    except ValueError as error:
        sys.exit(f"Sorry: {error}")

    preview(board)
    if not args.preview:
        send_to_board(board)


def send_to_board(board):
    """Send the board using the saved API key, explaining any problem in plain English."""
    api_key = load_api_key()
    if not api_key:
        sys.exit("No API key found. Put your key in vestaboard/api_key.txt (see README.md).")

    try:
        status, reply = send(board, api_key)
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            sys.exit("Vestaboard rejected the API key. Check that it's your Cloud API token.")
        if error.code == 409:
            print("That message is already on the board, so there was nothing to change.")
            return
        sys.exit(f"Vestaboard returned an error: {error.code} {error.reason}")
    except urllib.error.URLError as error:
        sys.exit(f"Couldn't reach Vestaboard: {error.reason}")
    print("Sent to your Vestaboard!")
    print(f"Vestaboard's reply ({status}): {reply}")


if __name__ == "__main__":
    main()
