#!/usr/bin/env python3
"""
A Halloween countdown on the Vestaboard.

Every day from October 1 it shows how many days are left, and on Halloween itself
it says Happy Halloween.

    python3 halloween.py              send today's countdown (only during October)
    python3 halloween.py --days 3     send the countdown for 3 days to go (0 is Halloween)
    python3 halloween.py --preview    just show it (works with --days too)
    python3 halloween.py --in-season  succeeds only during the countdown (used by GitHub)
    python3 halloween.py --check      check every day fits on the board
"""

import argparse
import sys
from datetime import date, datetime

from love_message import TIME_ZONE
from send_message import build_board, preview, send_to_board

COUNTDOWN_STARTS = (10, 1)  # October 1


def days_to_go(today):
    """Days left until Halloween, or None if the countdown isn't running."""
    if (today.month, today.day) < COUNTDOWN_STARTS or today.month > 10:
        return None
    return (date(today.year, 10, 31) - today).days


def halloween_text(days):
    if days == 0:
        return "{orange}{black}{orange} Happy {orange}{black}{orange}\nHalloween!"
    unit = "day" if days == 1 else "days"
    return f"{{orange}} {days} {unit} {{orange}}\nuntil\n{{orange}} Halloween {{orange}}"


def main():
    parser = argparse.ArgumentParser(description="A Halloween countdown on your Vestaboard.")
    parser.add_argument("--days", type=int, help="Send the countdown for this many days to go")
    parser.add_argument("--preview", action="store_true", help="Only show it; don't send it")
    parser.add_argument("--in-season", action="store_true", help="Succeed only during the countdown")
    parser.add_argument("--check", action="store_true", help="Check every day fits on the board")
    args = parser.parse_args()

    today = datetime.now(TIME_ZONE).date()
    if args.in_season:
        sys.exit(0 if days_to_go(today) is not None else 1)

    longest = days_to_go(date(today.year, *COUNTDOWN_STARTS))
    if args.check:
        for days in range(longest + 1):
            build_board(halloween_text(days))
        print(f"All {longest + 1} days of the countdown fit on the board.")
        return

    days = args.days if args.days is not None else days_to_go(today)
    if days is None:
        sys.exit("The countdown runs from October 1 to Halloween. Use --days to send one anyway.")
    if not 0 <= days <= longest:
        sys.exit(f"--days should be between 0 (Halloween) and {longest}.")
    board = build_board(halloween_text(days))
    preview(board)
    if not args.preview:
        send_to_board(board)


if __name__ == "__main__":
    main()
