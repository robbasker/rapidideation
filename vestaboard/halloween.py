#!/usr/bin/env python3
"""
A Halloween countdown on the Vestaboard.

Every day from October 1 it shows how many days are left, and on Halloween itself
it says Happy Halloween. schedule.py sends it each morning; to send one yourself:

    python3 halloween.py               send today's countdown (only during October)
    python3 halloween.py --date 10-28  send the countdown for October 28
    python3 halloween.py --preview     just show it (works with --date too)
    python3 halloween.py --check       check every day fits on the board
"""

from datetime import date

from daily import Show, run_cli

COUNTDOWN_STARTS = (10, 1)  # October 1


def days_to_go(day):
    """Days left until Halloween, or None if the countdown isn't running."""
    if (day.month, day.day) < COUNTDOWN_STARTS or day.month > 10:
        return None
    return (date(day.year, 10, 31) - day).days


def halloween_text(days):
    if days == 0:
        return "{orange}{black}{orange} Happy {orange}{black}{orange}\nHalloween!"
    unit = "day" if days == 1 else "days"
    return f"{{orange}} {days} {unit} {{orange}}\nuntil\n{{orange}} Halloween {{orange}}"


def text_for(day):
    days = days_to_go(day)
    return None if days is None else halloween_text(days)


def all_texts():
    longest = days_to_go(date(2000, *COUNTDOWN_STARTS))
    return [halloween_text(days) for days in range(longest + 1)]


HALLOWEEN = Show("halloween", text_for, all_texts)

if __name__ == "__main__":
    run_cli(__doc__, [HALLOWEEN])
