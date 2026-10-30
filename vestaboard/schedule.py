#!/usr/bin/env python3
"""
What goes on the Vestaboard, and when. GitHub runs this a few times a day.

The plan is the SLOTS list below, in US Eastern time. Each slot is set 13 minutes
before the hour because GitHub is busiest on the hour and often starts late. If a
run starts so late that it would cover up the next slot's message, or more than
3 hours late, it's skipped rather than showing up at the wrong time of day.

    python3 schedule.py --plan                 show what's planned today (works with --date)
    python3 schedule.py --send riddle          send one now (works with --date and --preview)
    python3 schedule.py --check                check everything fits, and the GitHub times match
    python3 schedule.py --cron "47 11 * * *"   what GitHub runs: send whatever that run is for
    python3 schedule.py --due                  what the outside timer runs: send whatever is due now
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone

import christmas
import halloween
import on_this_day
import riddle
from daily import HERE, TIME_ZONE, check, parse_date, send, today


@dataclass
class Slot:
    time: time
    shows: list  # the first one with something to show that day goes up


SLOTS = [
    Slot(time(7, 47), [christmas.CHRISTMAS, halloween.HALLOWEEN]),
    Slot(time(8, 47), [on_this_day.ON_THIS_DAY]),
    Slot(time(11, 47), [riddle.RIDDLE]),
    Slot(time(17, 47), [riddle.ANSWER]),
]
SHOWS = {show.name: show for slot in SLOTS for show in slot.shows}
MAX_LATE = timedelta(hours=3)
WORKFLOW = os.path.join(HERE, "..", ".github", "workflows", "vestaboard.yml")


def clock(t):
    """7:47am, 5:47pm."""
    return f"{t.hour % 12 or 12}:{t.minute:02d}{'am' if t.hour < 12 else 'pm'}"


def due_show(slot, day):
    """The show going up in this slot on this day, or None if there's nothing."""
    return next((show for show in slot.shows if show.text_for(day) is not None), None)


def planned_time(cron, now):
    """The Eastern time a GitHub run was planned for, from its cron line like "47 11 * * *"."""
    minute, hour = (int(part) for part in cron.split()[:2])
    planned = now.astimezone(timezone.utc).replace(hour=hour, minute=minute, second=0, microsecond=0)
    if planned > now:
        planned -= timedelta(days=1)
    return planned.astimezone(TIME_ZONE)


def run_scheduled(cron, now=None):
    """Send whatever this GitHub run is for. Returns the show sent, or None."""
    now = now or datetime.now(timezone.utc)
    planned = planned_time(cron, now)
    slot = next((slot for slot in SLOTS if slot.time == planned.time()), None)
    if slot is None:
        # Each time has two cron lines, one for summer time and one for winter; this is the other one.
        print(f"This run is for {clock(planned.time())} Eastern, which isn't in the plan, so nothing to do.")
        return None
    return run_slot(slot, planned, now)


def run_due(now=None):
    """Send whatever slot is due at this moment. Used by the outside timer (cron-job.org),
    which starts the workflow at each slot's time. Returns the show sent, or None."""
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(TIME_ZONE)
    passed = [slot for slot in SLOTS if slot.time <= local.time()]
    if not passed:
        print(f"Nothing is due yet at {clock(local.time())} Eastern.")
        return None
    slot = passed[-1]
    return run_slot(slot, datetime.combine(local.date(), slot.time, TIME_ZONE), now)


def run_slot(slot, planned, now):
    """Send the slot's show, unless it's too late or the next slot's time has come."""
    day = planned.date()
    show = due_show(slot, day)
    if show is None:
        print(f"Nothing planned for {clock(slot.time)} today.")
        return None

    late = now - planned
    minutes = int(late.total_seconds() // 60)
    print(f"This is the {clock(slot.time)} {show.name}. It started {minutes} minute{'' if minutes == 1 else 's'} late.")
    if late > MAX_LATE:
        print(f"That's more than {int(MAX_LATE.total_seconds() // 3600)} hours late, so it's skipped today.")
        return None
    for later in SLOTS[SLOTS.index(slot) + 1:]:
        later_show = due_show(later, day)
        if later_show and now >= datetime.combine(day, later.time, TIME_ZONE):
            print(f"It's already time for the {clock(later.time)} {later_show.name}, so this one is skipped today.")
            return None

    # The outside timer and GitHub's own (often late) schedule can both run the same slot,
    # so skip quietly if it's already up rather than replaying its sound.
    send(show, day, skip_if_showing=True)
    return show


def print_plan(day):
    print(f"The plan for {day:%A, %B} {day.day}:")
    for slot in SLOTS:
        show = due_show(slot, day)
        what = f"{show.name:14} {show.text_for(day).replace(chr(10), ' / ')}" if show else "(nothing)"
        print(f"  {clock(slot.time):>7}  {what}")


def check_workflow():
    """Make sure vestaboard.yml has a cron line for every slot, in both summer and winter time."""
    with open(WORKFLOW, encoding="utf-8") as f:
        crons = set(re.findall(r'cron:\s*"([^"]+)"', f.read()))
    problems = 0
    for slot in SLOTS:
        for hours_behind in (4, 5):  # US Eastern is 4 hours behind UTC in summer, 5 in winter
            needed = f"{slot.time.minute} {(slot.time.hour + hours_behind) % 24} * * *"
            if needed not in crons:
                problems += 1
                print(f"Add  - cron: \"{needed}\"  to .github/workflows/vestaboard.yml "
                      f"for the {clock(slot.time)} slot.")
    print(f"GitHub times: {problems} problem(s).")
    return problems


def main():
    parser = argparse.ArgumentParser(description="What goes on the Vestaboard, and when.")
    parser.add_argument("--plan", action="store_true", help="Show what's planned for the day")
    parser.add_argument("--send", choices=SHOWS, metavar="NAME",
                        help=f"Send one now: {', '.join(SHOWS)}")
    parser.add_argument("--date", type=parse_date, help="Pretend it's this date, like 12-24")
    parser.add_argument("--preview", action="store_true", help="With --send, only show it; don't send it")
    parser.add_argument("--check", action="store_true", help="Check everything fits on the board")
    parser.add_argument("--cron", help="Used by GitHub: send whatever this cron line's run is for")
    parser.add_argument("--due", action="store_true", help="Used by the outside timer: send whatever is due now")
    args = parser.parse_args()

    if args.check:
        problems = check(list(SHOWS.values())) + check_workflow()
        sys.exit(1 if problems else 0)
    if args.cron:
        run_scheduled(args.cron)
    elif args.due:
        run_due()
    elif args.send:
        send(SHOWS[args.send], args.date or today(), args.preview)
    else:
        print_plan(args.date or today())


if __name__ == "__main__":
    main()
