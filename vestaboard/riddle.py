#!/usr/bin/env python3
"""
Send today's riddle (from riddles.txt) to the Vestaboard, or its answer.

    python3 riddle.py            send today's riddle
    python3 riddle.py --answer   send the answer to today's riddle
    python3 riddle.py --preview  just show it (works with --answer too)
    python3 riddle.py --check    check every riddle and answer fits on the board
"""

import argparse
import os
import sys

from send_message import build_board, preview, send_to_board, todays_message

RIDDLES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "riddles.txt")


def load_riddles():
    """Return a list of (riddle, answer) pairs, skipping blank lines and # comments."""
    riddles = []
    with open(RIDDLES_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" not in line:
                sys.exit(f"This line in riddles.txt needs a | before the answer: {line}")
            riddle, answer = line.split("|", 1)
            riddles.append((riddle.strip(), answer.strip()))
    return riddles


def answer_text(answer):
    return f"Answer:\n{answer}"


def main():
    parser = argparse.ArgumentParser(description="Send today's riddle to your Vestaboard.")
    parser.add_argument("--answer", action="store_true", help="Send the answer instead of the riddle")
    parser.add_argument("--preview", action="store_true", help="Only show it; don't send it")
    parser.add_argument("--check", action="store_true", help="Check every riddle and answer fits")
    args = parser.parse_args()

    riddles = load_riddles()

    if args.check:
        problems = 0
        for riddle, answer in riddles:
            for text in (riddle, answer_text(answer)):
                try:
                    build_board(text)
                except ValueError as error:
                    problems += 1
                    print(f"Problem with \"{text}\": {error}")
        print(f"Checked {len(riddles)} riddles, {problems} problem(s).")
        sys.exit(1 if problems else 0)

    riddle, answer = todays_message(riddles)
    board = build_board(answer_text(answer) if args.answer else riddle)
    preview(board)
    if not args.preview:
        send_to_board(board)


if __name__ == "__main__":
    main()
