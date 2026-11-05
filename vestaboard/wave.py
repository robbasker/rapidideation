#!/usr/bin/env python3
"""
A sea-coloured wave that rolls across the Vestaboard from left to right, crashes
against the right side, then rolls back and crashes against the left.

    VESTABOARD_VIRTUAL=1 python3 wave.py   watch it on the virtual board
    python3 wave.py --times 3              crash against each side three times
    python3 wave.py --delay 2              wait 2 seconds between frames
    python3 wave.py --preview              just show the frames in the terminal

The real board only takes a new message about every 15 seconds, so there the
wave moves one step every 15 seconds. It's much smoother on the virtual board.

Only uses Python's built-in libraries, so there is nothing to install.
"""

import argparse
import os
import time

from board import COLOR_CODES, COLS, ROWS, preview
from sender import send_to_board

BLUE, GREEN, WHITE = COLOR_CODES["blue"], COLOR_CODES["green"], COLOR_CODES["white"]

REAL_BOARD_DELAY = 15  # seconds; Vestaboard refuses messages sent faster than this
VIRTUAL_BOARD_DELAY = 0.5

# The wave crashing against the right side of the board, one frame per list:
# b is blue water, g is the green swell, w is white foam and spray. It's flipped
# over for the left side.
CRASH = [
    ["...........bwww",
     ".........ggwwww",
     "........bbbbbbw"],
    [".........w.wwww",
     "........gggwwww",
     ".......bbbbbbbb"],
    ["........w..w.w.",
     ".........ggwwww",
     "........bbbbbbb"],
    ["..........w...w",
     ".............gg",
     "...........bbbb"],
]
TILES = {".": 0, "b": BLUE, "g": GREEN, "w": WHITE}


def height(ahead):
    """How many rows of water a column has, by how far it is ahead of the crest.

    The front of the wave is steep and the back slopes away gently, like a real one.
    """
    if ahead == 2:
        return 1
    if ahead == 1:
        return 2
    if -1 <= ahead <= 0:
        return 3
    if -3 <= ahead <= -2:
        return 2
    if -5 <= ahead <= -4:
        return 1
    return 0


def frame(crest, direction):
    """The board with the wave's crest at column `crest`, travelling in `direction` (+1 or -1)."""
    board = [[0] * COLS for _ in range(ROWS)]
    for col in range(COLS):
        ahead = (col - crest) * direction
        for level in range(height(ahead)):  # level 0 is the bottom row
            if level == 2:
                tile = WHITE if ahead == 0 else BLUE  # foam on the crest
            elif level == 1:
                tile = GREEN
            else:
                tile = BLUE
            board[ROWS - 1 - level][col] = tile
    return board


def crash(direction):
    """The frames of the wave crashing against the side it's travelling towards."""
    frames = []
    for rows in CRASH:
        if direction == -1:
            rows = [row[::-1] for row in rows]
        frames.append([[TILES[char] for char in row] for row in rows])
    return frames


def wave_frames(times):
    """Every frame: the wave rolls in, crashes against each side `times` times, and drains away."""
    frames = [frame(crest, 1) for crest in range(-3, 0)]
    for _ in range(times):
        frames += [frame(crest, 1) for crest in range(COLS)] + crash(1)
        frames += [frame(crest, -1) for crest in range(COLS - 1, -1, -1)] + crash(-1)
    frames.append([[BLUE, BLUE] + [0] * (COLS - 2) if row == ROWS - 1 else [0] * COLS
                   for row in range(ROWS)])
    frames.append([[0] * COLS for _ in range(ROWS)])
    return frames


def main():
    parser = argparse.ArgumentParser(description="Roll a sea-coloured wave across the Vestaboard.")
    parser.add_argument("--times", type=int, default=1, help="How many times to crash against each side (default 1)")
    parser.add_argument("--delay", type=float, help="Seconds between frames")
    parser.add_argument("--preview", action="store_true",
                        help="Only show the frames in the terminal; don't send them")
    args = parser.parse_args()

    virtual = bool(os.environ.get("VESTABOARD_VIRTUAL"))
    delay = args.delay if args.delay is not None else (VIRTUAL_BOARD_DELAY if virtual else REAL_BOARD_DELAY)
    if not virtual and not args.preview and delay < REAL_BOARD_DELAY:
        print(f"The real board needs {REAL_BOARD_DELAY} seconds between messages, so using that.")
        delay = REAL_BOARD_DELAY

    last = None
    for board in wave_frames(args.times):
        if board == last:  # the board refuses the same message twice in a row
            continue
        last = board
        preview(board)
        if not args.preview:
            send_to_board(board)
            time.sleep(delay)


if __name__ == "__main__":
    main()
