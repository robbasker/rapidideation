#!/usr/bin/env python3
"""
The 12 Days of Christmas on the Vestaboard, with a Christmas song on the Sonos.

It runs from December 14 (day 1) to Christmas Day (day 12), counting down to
Christmas. Each day's gift and song are in christmas.txt. schedule.py sends it each
morning; to send one yourself:

    python3 christmas.py               send today's day (only during the 12 days)
    python3 christmas.py --date 12-16  send the day for December 16 (day 3)
    python3 christmas.py --preview     just show it (works with --date too)
    python3 christmas.py --check       check every day fits on the board
"""

import sys

from daily import Show, load_table, run_cli, sonos_song


def load_days():
    """Return a list of [gift, song] pairs, one for each of the 12 days."""
    days = load_table("christmas.txt", 2)
    if len(days) != 12:
        sys.exit(f"christmas.txt should have 12 days, but it has {len(days)}.")
    return days


def day_of_christmas(day):
    """1 on December 14 up to 12 on Christmas Day; None on any other date."""
    if day.month == 12 and 14 <= day.day <= 25:
        return day.day - 13
    return None


def christmas_text(number, gift):
    return f"{{red}}{{green}} DAY {number} {{green}}{{red}}\n{gift}"


def text_for(day):
    number = day_of_christmas(day)
    if not number:
        return None
    gift, _ = load_days()[number - 1]
    return christmas_text(number, gift)


def sound_for(day):
    """The day's song, if one is chosen. The board changes 3 seconds after it starts."""
    number = day_of_christmas(day)
    song = load_days()[number - 1][1] if number else ""
    return sonos_song(song, wait=3) if song else None


CHRISTMAS = Show(
    "christmas", text_for,
    all_texts=lambda: [christmas_text(number, gift) for number, (gift, _) in enumerate(load_days(), 1)],
    sound_for=sound_for,
)

if __name__ == "__main__":
    run_cli(__doc__, [CHRISTMAS])
