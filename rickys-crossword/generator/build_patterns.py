"""Builds patterns.json, the library of grid shapes the daily generator picks from.
Run once (takes a few minutes); the result is committed, so the daily job doesn't redo it.

    python3 build_patterns.py
"""
import json, random, sys, time
from grid import search_pattern

COMBOS = [(o, m) for o in (10, 11, 12, 13, 14, 15) for m in (9, 11, 13, 15)]
PER_COMBO = int(sys.argv[1]) if len(sys.argv) > 1 else 6

lib = {}
rng = random.Random(1)
for outer, middle in COMBOS:
    found, start = set(), time.time()
    while len(found) < PER_COMBO and time.time() - start < 50:
        p = search_pattern(outer, middle, rng)
        if p:
            found.add("/".join(p))
    lib[f"{outer}-{middle}"] = sorted(found)
    print(outer, middle, len(found), flush=True)
json.dump(lib, open("patterns.json", "w"), indent=1)
