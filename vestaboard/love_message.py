#!/usr/bin/env python3
"""
Send today's love message (from love_messages.txt) to the Vestaboard.

The messages come out in a random order, but none repeats until every
message in the list has been used once.

    python3 love_message.py            send today's message
    python3 love_message.py --preview  just show it
    python3 love_message.py --check    check every message fits on the board
"""

import argparse
import os
import random
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from send_message import build_board, preview, send_to_board

MESSAGES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "love_messages.txt")
TIME_ZONE = ZoneInfo("Europe/London")


def load_messages():
    with open(MESSAGES_FILE, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def todays_message(messages):
    """Shuffle the list once per round, then take the message for today's place in that round."""
    day = datetime.now(TIME_ZONE).date().toordinal()
    round_number, place = divmod(day, len(messages))
    shuffled = list(messages)
    random.Random(round_number).shuffle(shuffled)
    return shuffled[place]


def main():
    parser = argparse.ArgumentParser(description="Send today's love message to your Vestaboard.")
    parser.add_argument("--preview", action="store_true", help="Only show today's message; don't send it")
    parser.add_argument("--check", action="store_true", help="Check every message fits on the board")
    args = parser.parse_args()

    messages = load_messages()

    if args.check:
        problems = 0
        for message in messages:
            try:
                build_board(message)
            except ValueError as error:
                problems += 1
                print(f"Problem with \"{message}\": {error}")
        print(f"Checked {len(messages)} messages, {problems} problem(s).")
        sys.exit(1 if problems else 0)

    board = build_board(todays_message(messages))
    preview(board)
    if not args.preview:
        send_to_board(board)


if __name__ == "__main__":
    main()
