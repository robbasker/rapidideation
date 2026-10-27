#!/usr/bin/env python3
"""
Send something that happened on this day in history (from on_this_day.txt) to the Vestaboard.

    python3 on_this_day.py                send today's (if there is one)
    python3 on_this_day.py --date 12-24   send the one for December 24
    python3 on_this_day.py --preview      just show it (works with --date too)
    python3 on_this_day.py --has-today    succeeds only if there's one for today (used by GitHub)
    python3 on_this_day.py --check        check every one fits on the board
"""

import argparse
import os
import sys
from datetime import datetime

from love_message import TIME_ZONE
from send_message import build_board, preview, send_to_board

EVENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "on_this_day.txt")


def load_events():
    """Return a dict of "MM-DD" -> (year, headline), skipping blank lines and # comments."""
    events = {}
    with open(EVENTS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [part.strip() for part in line.split("|")]
            if len(parts) != 3:
                sys.exit(f"This line in on_this_day.txt needs a date, year and headline: {line}")
            day, year, headline = parts
            events[day] = (year, headline)
    return events


def event_text(year, headline):
    return f"{{violet}} {year} {{violet}}\n{headline}"


def main():
    parser = argparse.ArgumentParser(description="Send today in history to your Vestaboard.")
    parser.add_argument("--date", help="Send the one for this date (month-day, like 12-24)")
    parser.add_argument("--preview", action="store_true", help="Only show it; don't send it")
    parser.add_argument("--has-today", action="store_true", help="Succeed only if there's one for today")
    parser.add_argument("--check", action="store_true", help="Check every one fits on the board")
    args = parser.parse_args()

    events = load_events()
    today = datetime.now(TIME_ZONE).strftime("%m-%d")

    if args.has_today:
        sys.exit(0 if today in events else 1)

    if args.check:
        problems = 0
        for day, (year, headline) in events.items():
            try:
                build_board(event_text(year, headline))
            except ValueError as error:
                problems += 1
                print(f"Problem with {day} \"{headline}\": {error}")
        print(f"Checked {len(events)} days, {problems} problem(s).")
        sys.exit(1 if problems else 0)

    day = args.date or today
    if day not in events:
        sys.exit(f"There's nothing in on_this_day.txt for {day}.")
    board = build_board(event_text(*events[day]))
    preview(board)
    if not args.preview:
        send_to_board(board)


if __name__ == "__main__":
    main()
