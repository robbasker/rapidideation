#!/usr/bin/env python3
"""
The 12 Days of Christmas on the Vestaboard, with a Christmas song on the Sonos.

It runs at 8am from December 14 (day 1) to Christmas Day (day 12), counting down to
Christmas. Each day's gift and song are in christmas.txt.

    python3 christmas.py              send today's day (only during the 12 days)
    python3 christmas.py --day 3      send day 3, whatever the date
    python3 christmas.py --preview    just show it (works with --day too)
    python3 christmas.py --in-season  succeeds only during the 12 days (used by GitHub)
    python3 christmas.py --check      check every day fits on the board
"""

import argparse
import os
import sys
import time
from datetime import datetime

from love_message import TIME_ZONE
from send_message import build_board, preview, send_to_board

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sonos"))
import sonos  # noqa: E402

DAYS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "christmas.txt")


def load_days():
    """Return a list of (gift, song) pairs, one for each of the 12 days."""
    days = []
    with open(DAYS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            gift, _, song = line.partition("|")
            days.append((gift.strip(), song.strip()))
    if len(days) != 12:
        sys.exit(f"christmas.txt should have 12 days, but it has {len(days)}.")
    return days


def day_of_christmas(today):
    """1 on December 14 up to 12 on Christmas Day; None on any other date."""
    if today.month == 12 and 14 <= today.day <= 25:
        return today.day - 13
    return None


def christmas_text(day, gift):
    return f"{{red}}{{green}} DAY {day} {{green}}{{red}}\n{gift}"


def play_song(song):
    """Start the song on the Sonos; returns True if it started."""
    if not song:
        print("No song chosen for today.")
        return False
    try:
        sonos.play_favourite(song)
        return True
    except SystemExit as problem:
        print(f"No song this time: {problem}")
        return False


def main():
    parser = argparse.ArgumentParser(description="The 12 Days of Christmas on your Vestaboard.")
    parser.add_argument("--day", type=int, choices=range(1, 13), help="Send this day instead of today's")
    parser.add_argument("--preview", action="store_true", help="Only show it; don't send it")
    parser.add_argument("--in-season", action="store_true", help="Succeed only during the 12 days")
    parser.add_argument("--check", action="store_true", help="Check every day fits on the board")
    args = parser.parse_args()

    today = datetime.now(TIME_ZONE).date()
    if args.in_season:
        sys.exit(0 if day_of_christmas(today) else 1)

    days = load_days()

    if args.check:
        for day, (gift, _) in enumerate(days, 1):
            build_board(christmas_text(day, gift))
        print("All 12 days fit on the board.")
        return

    day = args.day or day_of_christmas(today)
    if not day:
        sys.exit("It isn't one of the 12 days of Christmas. Use --day to send one anyway.")
    gift, song = days[day - 1]
    board = build_board(christmas_text(day, gift))
    preview(board)
    if args.preview:
        return

    # Music first, then the Vestaboard a few seconds later.
    if play_song(song):
        time.sleep(3)
    send_to_board(board)


if __name__ == "__main__":
    main()
