#!/usr/bin/env python3
"""
Something that happened on this day in history (from on_this_day.txt), on the Vestaboard.

schedule.py sends it each morning, on any date that has a headline. To send one yourself:

    python3 on_this_day.py               send today's (if there is one)
    python3 on_this_day.py --date 12-24  send the one for December 24
    python3 on_this_day.py --preview     just show it (works with --date too)
    python3 on_this_day.py --check       check every one fits on the board
"""

from daily import Show, load_table, run_cli


def load_events():
    """Return a dict of "MM-DD" -> (year, headline)."""
    return {day: (year, headline) for day, year, headline in load_table("on_this_day.txt", 3)}


def event_text(year, headline):
    return f"{{violet}} {year} {{violet}}\n{headline}"


def text_for(day):
    event = load_events().get(f"{day:%m-%d}")
    return event_text(*event) if event else None


ON_THIS_DAY = Show(
    "on this day", text_for,
    all_texts=lambda: [event_text(year, headline) for year, headline in load_events().values()],
)

if __name__ == "__main__":
    run_cli(__doc__, [ON_THIS_DAY])
