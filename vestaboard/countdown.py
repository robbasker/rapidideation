#!/usr/bin/env python3
"""
Count down the days to the next event in countdowns.txt on the Vestaboard.

    python3 countdown.py                       send today's countdown
    python3 countdown.py --preview             just show it
    python3 countdown.py --date 2026-12-24     pretend it's another day (works with --preview)
    python3 countdown.py --check               check every event fits on the board
"""

import argparse
import os
import sys
from datetime import date, datetime

from love_message import TIME_ZONE
from send_message import build_board, preview, send_to_board

EVENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "countdowns.txt")


def load_events():
    """Return a list of (when, name) pairs. 'when' is 'MM-DD' (every year) or 'YYYY-MM-DD'."""
    events = []
    with open(EVENTS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" not in line:
                sys.exit(f"This line in countdowns.txt needs a | before the name: {line}")
            when, name = line.split("|", 1)
            events.append((when.strip(), name.strip()))
    return events


def next_date(when, today):
    """The next time this event happens, on or after today. None if a one-off has passed."""
    try:
        if when.count("-") == 2:
            day = date.fromisoformat(when)
            return day if day >= today else None
        month, day_of_month = (int(part) for part in when.split("-"))
        for year in range(today.year, today.year + 8):
            try:
                day = date(year, month, day_of_month)
            except ValueError:
                continue  # February 29 in a year that isn't a leap year
            if day >= today:
                return day
    except ValueError:
        pass
    sys.exit(f"Couldn't understand the date '{when}' in countdowns.txt. Use 12-25 or 2027-03-14.")


def soonest_event(events, today):
    """Return (days to go, name) for the next event, or None if there's nothing ahead."""
    upcoming = []
    for when, name in events:
        day = next_date(when, today)
        if day:
            upcoming.append(((day - today).days, name))
    return min(upcoming) if upcoming else None


def countdown_text(days, name):
    if days == 0:
        return f"{{yellow}} TODAY IS {{yellow}}\n{name}!"
    if days == 1:
        return f"{{green}} TOMORROW {{green}}\n{name}!"
    return f"{days} DAYS UNTIL\n{name}"


def main():
    parser = argparse.ArgumentParser(description="Count down to the next event on your Vestaboard.")
    parser.add_argument("--date", type=date.fromisoformat, help="Pretend today is this date, e.g. 2026-12-24")
    parser.add_argument("--preview", action="store_true", help="Only show it; don't send it")
    parser.add_argument("--check", action="store_true", help="Check every event fits on the board")
    args = parser.parse_args()

    events = load_events()

    if args.check:
        problems = 0
        for _, name in events:
            # The longest version is a three-digit number of days.
            for days in (0, 1, 365):
                try:
                    build_board(countdown_text(days, name))
                except ValueError as error:
                    problems += 1
                    print(f"Problem with \"{name}\": {error}")
                    break
        print(f"Checked {len(events)} events, {problems} problem(s).")
        sys.exit(1 if problems else 0)

    today = args.date or datetime.now(TIME_ZONE).date()
    soonest = soonest_event(events, today)
    if not soonest:
        sys.exit("Nothing to count down to. Add an event to countdowns.txt.")
    board = build_board(countdown_text(*soonest))
    preview(board)
    if not args.preview:
        send_to_board(board)


if __name__ == "__main__":
    main()
