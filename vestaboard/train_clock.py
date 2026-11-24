#!/usr/bin/env python3
"""
A train-station clock on the Vestaboard: a train arriving at Grand Central from
somewhere on the Metro-North lines, with the time now and its track.

      NEW HAVEN
    🟩GRAND CENTRAL🟩
     10:00  TRK 23

schedule.py sends it every hour; the stations are in stations.txt. To send one yourself:

    python3 train_clock.py            send it with the time now
    python3 train_clock.py --preview  just show it
    python3 train_clock.py --check    check every station fits on the board
"""

import random
from datetime import datetime

from daily import TIME_ZONE, Show, load_table, run_cli

TRACKS = range(11, 43)  # Grand Central's upper-level tracks


def load_stations():
    return [station for station, in load_table("stations.txt", 1)]


def clock_text(station, hour, minute, track):
    return f"{station}\n{{green}}Grand Central{{green}}\n{hour}:{minute:02d}  Trk {track}"


def text_at(day, moment):
    """The board at this time of day. A new train and track each hour."""
    pick = random.Random(f"{day}-{moment.hour}")
    return clock_text(pick.choice(load_stations()), moment.hour % 12 or 12, moment.minute, pick.choice(TRACKS))


def text_for(day):
    """The board with the time right now."""
    return text_at(day, datetime.now(TIME_ZONE).time())


def all_texts():
    # The widest time and track, with every station.
    return [clock_text(station, 12, 59, max(TRACKS)) for station in load_stations()]


TRAIN_CLOCK = Show("train clock", text_for, all_texts)

if __name__ == "__main__":
    run_cli(__doc__, [TRAIN_CLOCK])
