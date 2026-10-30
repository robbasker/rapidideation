"""
The parts every daily script shares (riddle.py, christmas.py, halloween.py, on_this_day.py).

Each script describes what it puts on the board as a Show: the text for a given day
(or None if there's nothing that day), every text it could ever show (for --check),
and optionally a sound to play on the Sonos first. schedule.py decides when each
one goes out; run_cli gives every script the same --date, --preview and --check.
"""

import argparse
import os
import random
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from board import build_board, preview
from sender import read_board, send_to_board

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sonos"))
import sonos  # noqa: E402

TIME_ZONE = ZoneInfo("America/New_York")  # what "today" means for the board


def today():
    return datetime.now(TIME_ZONE).date()


def parse_date(text):
    """Turn '12-24' (this year) or '2026-12-24' into a date."""
    try:
        if text.count("-") == 1:
            month, day = (int(part) for part in text.split("-"))
            return date(today().year, month, day)
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{text}' isn't a date like 12-24.")


def load_table(filename, columns):
    """Read a text file of lines with parts separated by |, skipping blank lines and # comments."""
    rows = []
    with open(os.path.join(HERE, filename), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [part.strip() for part in line.split("|")]
            if len(parts) != columns:
                sys.exit(f"This line in {filename} should have {columns} parts separated by |: {line}")
            rows.append(parts)
    return rows


def pick_for_day(items, day):
    """Shuffle the list once per round, then take the item for the day's place in that round.

    So the items come out in a random order, but none repeats until every one has been used.
    """
    round_number, place = divmod(day.toordinal(), len(items))
    shuffled = list(items)
    random.Random(round_number).shuffle(shuffled)
    return shuffled[place]


@dataclass
class Sound:
    """Something to play on the Sonos just before the board changes."""
    play: Callable[[], None]
    wait: float  # seconds between starting the sound and changing the board


def sonos_sound(name, wait):
    """One of the sounds in sonos.py, like 'drumroll' or 'thinking'."""
    return Sound(lambda: sonos.play_sound(name), wait)


def sonos_song(favourite, wait):
    """A song saved as a Sonos favourite."""
    return Sound(lambda: sonos.play_favourite(favourite), wait)


@dataclass
class Show:
    """One thing the board can show, like today's riddle."""
    name: str
    text_for: Callable[[date], Optional[str]]
    all_texts: Callable[[], list]
    sound_for: Callable[[date], Optional[Sound]] = lambda day: None
    flag: Optional[str] = None  # for a script's second show, like riddle.py --answer


def check(shows):
    """Make sure everything each show could send fits on the board. Returns the number of problems."""
    problems = 0
    for show in shows:
        texts = show.all_texts()
        show_problems = 0
        for text in texts:
            try:
                build_board(text)
            except ValueError as error:
                show_problems += 1
                print(f"Problem with \"{text}\": {error}")
        print(f"{show.name}: checked {len(texts)}, {show_problems} problem(s).")
        problems += show_problems
    return problems


def send(show, day, preview_only=False, skip_if_showing=False):
    """Show the day's board in the terminal, play its sound, then send it.

    With skip_if_showing, nothing happens (not even the sound) if the board already
    shows it, so a late duplicate run doesn't replay the jingle or drum roll.
    """
    text = show.text_for(day)
    if text is None:
        sys.exit(f"There's no {show.name} for {day:%B} {day.day}. Use --date to pick another day.")
    try:
        board = build_board(text)
    except ValueError as error:
        sys.exit(f"Sorry: {error}")
    preview(board)
    if preview_only:
        return
    if skip_if_showing and read_board() == board:
        print("The board is already showing this, so there's nothing to do.")
        return

    sound = show.sound_for(day)
    if sound and os.environ.get("VESTABOARD_VIRTUAL"):
        print("Skipping the Sonos, since this is going to the virtual board.")
    elif sound:
        try:
            sound.play()
            time.sleep(sound.wait)
        except SystemExit as problem:
            # If the sound fails, the board still changes straight away.
            print(f"No sound this time: {problem}")
    send_to_board(board)


def run_cli(doc, shows):
    """The command line every daily script shares. The first show is the one sent by default."""
    parser = argparse.ArgumentParser(description=doc.strip().splitlines()[0])
    for show in shows[1:]:
        parser.add_argument(show.flag, action="store_true", help=f"Send the {show.name} instead")
    parser.add_argument("--date", type=parse_date, help="Pretend it's this date, like 12-24")
    parser.add_argument("--preview", action="store_true", help="Only show it; don't send it")
    parser.add_argument("--check", action="store_true", help="Check everything fits on the board")
    args = parser.parse_args()

    if args.check:
        sys.exit(1 if check(shows) else 0)

    chosen = next((show for show in shows[1:] if getattr(args, show.flag.lstrip("-").replace("-", "_"))),
                  shows[0])
    send(chosen, args.date or today(), args.preview)
