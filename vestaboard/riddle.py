#!/usr/bin/env python3
"""
Today's riddle (from riddles.txt) on the Vestaboard, or its answer.

The riddle goes up with a thinking jingle on the Sonos, and the answer with a drum
roll. schedule.py sends them each day; to send one yourself:

    python3 riddle.py               send today's riddle
    python3 riddle.py --answer      send the answer to today's riddle
    python3 riddle.py --date 12-24  send the riddle for another day (works with --answer too)
    python3 riddle.py --preview     just show it (works with the others too)
    python3 riddle.py --check       check every riddle and answer fits on the board
"""

from daily import Show, load_table, pick_for_day, run_cli, sonos_sound


def load_riddles():
    """Return a list of [riddle, answer] pairs."""
    return load_table("riddles.txt", 2)


def answer_text(answer):
    return f"Answer:\n{answer}"


def riddle_for(day):
    riddle, _ = pick_for_day(load_riddles(), day)
    return riddle


def answer_for(day):
    _, answer = pick_for_day(load_riddles(), day)
    return answer_text(answer)


RIDDLE = Show(
    "riddle", riddle_for,
    all_texts=lambda: [riddle for riddle, _ in load_riddles()],
    sound_for=lambda day: sonos_sound("thinking", wait=7),  # the jingle is about 7 seconds
)
ANSWER = Show(
    "riddle answer", answer_for,
    all_texts=lambda: [answer_text(answer) for _, answer in load_riddles()],
    sound_for=lambda day: sonos_sound("drumroll", wait=3),  # lands on the cymbal crash
    flag="--answer",
)

if __name__ == "__main__":
    run_cli(__doc__, [RIDDLE, ANSWER])
