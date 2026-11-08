"""Makes one day's crossword in steps, so Claude (running as a scheduled Claude Code
routine) can do the creative parts itself: no API key needed.

    python3 make_puzzle.py next                      # which date needs a puzzle, recent themes, allowed lengths
    python3 make_puzzle.py grid  --ideas ideas.json  # fit a theme into a grid and fill it
    python3 make_puzzle.py polish --avoid WORD,WORD  # replace entries you don't like
    python3 make_puzzle.py finish --clues clues.json # check the clues and save the puzzle

All steps take --date YYYY-MM-DD (default: tomorrow, UTC). Work in progress is kept in
generator/.work/DATE.json between steps.

ideas.json: [{"title": ..., "link": ..., "answers": [first, middle, last]}, ...]
  Answers are normal phrases; letter counts must match a size listed by `next`.
clues.json: {"title": ..., "explanation": ...,
             "clues": [{"number": 1, "direction": "A", "clue": ...}, ...]}
"""
import argparse, concurrent.futures as cf, datetime as dt, json, os, random, re, sys, time

from grid import N, numbered, problems, theme_cells
import filler

HERE = os.path.dirname(os.path.abspath(__file__))
PUZZLES = os.path.join(HERE, "..", "puzzles")
WORK = os.path.join(HERE, ".work")

# How long the grid search may run, in seconds. Kept under ten minutes so one shell
# command can wait for it.
FILL_BUDGET = 540
GOOD = 55   # word-list score a fill word should reach; anything lower counts as weak
FLOOR = 40  # lowest score the first rough fill may use


def letters(s):
    return re.sub("[^A-Z]", "", s.upper())


# ---- Grid ---------------------------------------------------------------------------

_index = {}


def _init():
    words = filler.word_scores(FLOOR)
    _index["rough"] = filler.Index(words)
    _index["good"] = filler.Index({w: s for w, s in words.items() if s >= GOOD})


def _attempt(job):
    """One worker's try: rough fill of one shape, then upgrade weak words."""
    rows, keep, seed, seconds, avoid = job
    start = time.time()
    if any("." in r for r in rows):
        out = filler.fill(rows, _index["rough"], seed=seed, seconds=min(60, seconds), avoid=avoid)
    else:  # already filled: just swap out weak and avoided words
        out = rows
    if not out:
        return None
    left = seconds - (time.time() - start)
    out = filler.improve(out, _index["good"], keep, seconds=max(5, left), seed=seed, extra_bad=avoid,
                        backup_index=_index["rough"])
    weak = filler.weak_entries(out, _index["good"].words, avoid)
    return len(weak), out


def place(pattern, answers):
    """The pattern with the three theme answers written in, or None if it doesn't fit."""
    o, m = len(answers[0]), len(answers[1])
    if len(answers[2]) != o:
        return None
    g = [list(r) for r in pattern.split("/")]
    cells, _ = theme_cells(o, m)
    for word, cs in zip(answers, cells):
        for (r, c), ch in zip(cs, word):
            g[r][c] = ch
    return ["".join(r) for r in g], {x for cs in cells for x in cs}


def build_grid(candidates, library, avoid=(), seconds=FILL_BUDGET, start_from=None):
    """Try theme ideas in order until one fills well. Returns (idea, answers, grid, weak)."""
    workers = os.cpu_count() or 2
    best = None
    deadline = time.time() + seconds
    with cf.ProcessPoolExecutor(workers, initializer=_init) as pool:
        for idea, answers in candidates:
            shapes = library.get(f"{len(answers[0])}-{len(answers[1])}", [])
            jobs = []
            if start_from:  # re-polish an existing grid (after Claude's review)
                keep = {x for cs in theme_cells(len(answers[0]), len(answers[1]))[0] for x in cs}
                jobs = [(start_from, keep, s, None) for s in range(workers)]
            else:
                for shape in shapes:
                    placed = place(shape, answers)
                    if placed:
                        jobs += [(placed[0], placed[1], s, None) for s in range(2)]
            random.shuffle(jobs)
            while jobs and time.time() < deadline:
                batch, jobs = jobs[:workers], jobs[workers:]
                left = deadline - time.time()
                per = max(20, min(150, left / max(1, (len(jobs) // workers + 1))))
                futures = [pool.submit(_attempt, (rows, keep, seed, per, set(avoid))) for rows, keep, seed, _ in batch]
                for f in futures:
                    r = f.result()
                    if r and (best is None or r[0] < best[3]):
                        best = (idea, answers, r[1], r[0])
                if best and best[3] <= 2:
                    return best
            if best and best[3] <= 6:
                return best
            if time.time() >= deadline:
                break
    return best


# ---- Steps --------------------------------------------------------------------------

def load_index():
    path = os.path.join(PUZZLES, "index.json")
    return json.load(open(path)) if os.path.exists(path) else {"puzzles": []}


def library():
    return json.load(open(os.path.join(HERE, "patterns.json")))


def work_path(date):
    return os.path.join(WORK, f"{date}.json")


def show(work):
    grid, answers = work["grid"], work["answers"]
    good = filler.word_scores(GOOD)
    weak = {w for w, _ in filler.weak_entries(grid, good, set(work.get("avoid", [])))}
    print(f"Theme: {work['idea']['title']} ({work['idea']['link']})")
    print("Grid:\n  " + "\n  ".join(grid))
    print("Entries (A = Across, D = Down; * = theme answer, ? = weak by word-list score):")
    for n, d, _, _, w in numbered(grid):
        mark = " *" if w in answers else (" ?" if w in weak else "")
        print(f"  {n}{d} {w}{mark}")


def cmd_next(date, args):
    out_path = os.path.join(PUZZLES, f"{date}.json")
    index = load_index()
    print(f"Date: {date:%A %d %B %Y} ({date})")
    print("Puzzle already exists." if os.path.exists(out_path) else "No puzzle yet.")
    print("Recent themes (avoid these): " + ("; ".join(p["title"] for p in index["puzzles"][-60:]) or "none"))
    sizes = sorted({tuple(map(int, k.split("-"))) for k, v in library().items() if v})
    print("Allowed theme letter counts (first, middle, last): " + "; ".join(f"{o},{m},{o}" for o, m in sizes))


def cmd_grid(date, args):
    ideas = json.load(open(args.ideas))
    lib = library()
    candidates = []
    for idea in ideas:
        answers = [letters(a) for a in idea["answers"]]
        key = f"{len(answers[0])}-{len(answers[1])}" if len(answers) == 3 else ""
        if len(answers) == 3 and len(answers[0]) == len(answers[2]) and lib.get(key):
            candidates.append((idea, answers))
        else:
            print(f"Skipping {idea['title']}: letter counts {[len(a) for a in answers]} don't fit a grid shape")
    if not candidates:
        sys.exit("None of the theme ideas fit a grid shape.")
    print(f"Filling the grid (up to {args.seconds}s) ...", flush=True)
    found = build_grid(candidates, lib, seconds=args.seconds)
    if not found:
        sys.exit("Couldn't fill a grid for any theme idea. Try other ideas.")
    idea, answers, grid, _ = found
    os.makedirs(WORK, exist_ok=True)
    work = {"idea": idea, "answers": answers, "grid": grid, "avoid": []}
    json.dump(work, open(work_path(date), "w"), indent=1)
    show(work)


def cmd_polish(date, args):
    work = json.load(open(work_path(date)))
    avoid = set(work["avoid"]) | {letters(w) for w in args.avoid.split(",") if w.strip()}
    entries = {w for *_, w in numbered(work["grid"])}
    if avoid & set(work["answers"]):
        sys.exit("Theme answers can't be replaced.")
    print(f"Replacing {', '.join(sorted(avoid & entries)) or 'nothing'} (up to {args.seconds}s) ...", flush=True)
    better = build_grid([(work["idea"], work["answers"])], library(), avoid=avoid,
                        seconds=args.seconds, start_from=work["grid"])
    if better:
        work["grid"] = better[2]
    work["avoid"] = sorted(avoid)
    json.dump(work, open(work_path(date), "w"), indent=1)
    left = avoid & {w for *_, w in numbered(work["grid"])}
    if left:
        print(f"Couldn't get rid of: {', '.join(sorted(left))}")
    show(work)


def cmd_finish(date, args):
    work = json.load(open(work_path(date)))
    grid, answers = work["grid"], work["answers"]
    assert not problems(grid), problems(grid)
    written = json.load(open(args.clues))
    rows = numbered(grid)
    clues = {"A": {}, "D": {}}
    for c in written["clues"]:
        clues[c["direction"]][str(c["number"])] = c["clue"].strip()
    wanted = {(str(n), d) for n, d, *_ in rows}
    missing = [f"{n}{d}" for n, d, *_ in rows if str(n) not in clues[d]]
    extra = [f"{n}{d}" for d in clues for n in clues[d] if (n, d) not in wanted]
    leaks = [f"{n}{d}" for n, d, _, _, w in rows if len(w) > 3 and w in letters(clues[d].get(str(n), ""))]
    if missing or extra or leaks:
        sys.exit("Fix clues.json and run finish again:"
                 + (f"\n  missing clues: {', '.join(missing)}" if missing else "")
                 + (f"\n  clues for entries that don't exist: {', '.join(extra)}" if extra else "")
                 + (f"\n  clues containing their answer: {', '.join(leaks)}" if leaks else ""))
    puzzle = {
        "date": str(date),
        "title": written["title"].strip(),
        "grid": grid,
        "clues": clues,
        "theme": written["explanation"].strip(),
        "themeAnswers": answers,
    }
    out_path = os.path.join(PUZZLES, f"{date}.json")
    os.makedirs(PUZZLES, exist_ok=True)
    json.dump(puzzle, open(out_path, "w"), indent=1)
    index = load_index()
    index["puzzles"] = sorted([p for p in index["puzzles"] if p["date"] != str(date)]
                              + [{"date": str(date), "title": puzzle["title"]}], key=lambda p: p["date"])
    json.dump(index, open(os.path.join(PUZZLES, "index.json"), "w"), indent=1)
    os.remove(work_path(date))
    print(f"Saved {os.path.relpath(out_path, os.path.join(HERE, '..', '..'))}: {puzzle['title']}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("next", "grid", "polish", "finish"):
        p = sub.add_parser(name)
        p.add_argument("--date", help="YYYY-MM-DD (default: tomorrow, UTC)")
        if name == "grid":
            p.add_argument("--ideas", required=True)
            p.add_argument("--seconds", type=int, default=FILL_BUDGET)
        if name == "polish":
            p.add_argument("--avoid", required=True, help="comma-separated entries to replace")
            p.add_argument("--seconds", type=int, default=180)
        if name == "finish":
            p.add_argument("--clues", required=True)
    args = ap.parse_args()
    date = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1)
    globals()["cmd_" + args.cmd](date, args)


if __name__ == "__main__":
    main()
