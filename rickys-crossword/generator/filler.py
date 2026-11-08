"""Fills a crossword grid with real words.

The word lists are downloaded the first time and cached in generator/.cache:
- the Crossword Nexus collaborative word list (scores how good each entry is), and
- Christopher Jones's crossword word list (a second opinion on the same).

The filler keeps, for every slot, the set of words that still fit (as a bitmask over a
length's word list), and after each choice prunes every crossing slot down to words
that agree on the shared letter. It always tries the slot with the fewest options next.
"""
import math, os, random, re, time, urllib.request
from collections import defaultdict
from grid import slots

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".cache")
LISTS = {
    "xwordlist.dict": "https://raw.githubusercontent.com/Crossword-Nexus/collaborative-word-list/main/xwordlist.dict",
    "crossword_wordlist.txt": "https://raw.githubusercontent.com/christophsjones/crossword-wordlist/master/crossword_wordlist.txt",
}
LETTERS = [chr(65 + i) for i in range(26)]


def _read(name):
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        urllib.request.urlretrieve(LISTS[name], path)
    out = {}
    for line in open(path, encoding="utf-8", errors="ignore"):
        if ";" not in line:
            continue
        w, s = line.strip().rsplit(";", 1)
        w = re.sub("[^A-Za-z]", "", w).upper()
        try:
            s = int(s)
        except ValueError:
            continue
        if 3 <= len(w) <= 15:
            out[w] = max(s, out.get(w, 0))
    return out


def blocked():
    path = os.path.join(HERE, "blocklist.txt")
    return {l.strip().upper() for l in open(path) if l.strip() and not l.startswith("#")}


def word_scores(min_score=50):
    """{WORD: score}: entries from the main list scoring at least min_score, nudged up if
    the second list rates them well too, minus anything in blocklist.txt."""
    main, second = _read("xwordlist.dict"), _read("crossword_wordlist.txt")
    words = {w: s + (10 if second.get(w, 0) >= 45 else 0) for w, s in main.items() if s >= min_score}
    for w in blocked():
        words.pop(w, None)
    return words


class TimeUp(Exception):
    pass


class Index:
    """Words grouped by length, with a bitmask per (position, letter) for fast matching.
    Bit i of a mask stands for the i-th best-scoring word of that length."""

    def __init__(self, words):
        self.words = words
        self.bylen = defaultdict(list)
        for w in sorted(words, key=lambda w: -words[w]):
            self.bylen[len(w)].append(w)
        self.idx = {}
        self.pos = {}
        for L, ws in self.bylen.items():
            d = defaultdict(int)
            for i, w in enumerate(ws):
                b = 1 << i
                for p, ch in enumerate(w):
                    d[(p, ch)] |= b
            self.idx[L] = d
            self.pos[L] = {w: i for i, w in enumerate(ws)}

    def full(self, L):
        return (1 << len(self.bylen[L])) - 1

    def mask_of(self, L, words):
        m = 0
        for w in words:
            i = self.pos.get(L, {}).get(w)
            if i is not None:
                m |= 1 << i
        return m


def fill(rows, index, seed=0, seconds=60, branch=4, look=25, avoid=()):
    """Fill every "." in rows using words from index (an Index). Letters already in the
    grid stay, and answers that are already complete are left alone. Returns the filled
    rows, or None if no fill was found in time. avoid: words not to use this time."""
    rng = random.Random(seed)
    g = [list(r) for r in rows]
    SL, done = [], set()
    for _, cells in slots(g):
        w = "".join(g[r][c] for r, c in cells)
        if "." in w:
            SL.append(cells)
        else:
            done.add(w)
    if not SL:
        return ["".join(r) for r in g]
    idx, bylen = index.idx, index.bylen
    at = defaultdict(list)
    for i, cells in enumerate(SL):
        for p, x in enumerate(cells):
            at[x].append((i, p))
    cross = defaultdict(list)
    for lst in at.values():
        if len(lst) == 2:
            (a, pa), (b, pb) = lst
            cross[a].append((pa, b, pb))
            cross[b].append((pb, a, pa))
    dom = []
    for cells in SL:
        L = len(cells)
        m = index.full(L) & ~index.mask_of(L, set(avoid) | done)
        for p, (r, c) in enumerate(cells):
            if g[r][c] != ".":
                m &= idx.get(L, {}).get((p, g[r][c]), 0)
        dom.append(m)

    def prune(dom, queue):
        queue = list(queue)
        while queue:
            i = queue.pop()
            Li = len(SL[i])
            for pi, j, pj in cross[i]:
                Lj = len(SL[j])
                allow = 0
                for ch in LETTERS:
                    if dom[i] & idx[Li].get((pi, ch), 0):
                        allow |= idx[Lj].get((pj, ch), 0)
                nd = dom[j] & allow
                if nd != dom[j]:
                    if not nd:
                        return False
                    dom[j] = nd
                    queue.append(j)
        return True

    def first_bits(m, k):
        out = []
        while m and len(out) < k:
            b = m & -m
            out.append(b.bit_length() - 1)
            m ^= b
        return out

    def some_bits(m, k):
        """The best few words plus a random sample of the rest, so restarts differ."""
        top = first_bits(m, k)
        if m.bit_count() > k:
            rest = first_bits(m, 4 * k)[k // 2:]
            top = top[:k // 2] + rng.sample(rest, min(len(rest), k - k // 2))
        return top

    start = time.time()

    def solve(dom):
        if time.time() - start > seconds:
            raise TimeUp
        best, bc = None, None
        for i, m in enumerate(dom):
            c = m.bit_count()
            if c > 1 and (best is None or c < bc):
                best, bc = i, c
        if best is None:
            if any(m == 0 for m in dom):
                return None
            ws = [bylen[len(SL[i])][first_bits(m, 1)[0]] for i, m in enumerate(dom)]
            return ws if len(set(ws)) == len(ws) else None
        # Try good words that fit, ordered by how much room they leave for the crossing
        # answers, so the search doesn't paint itself into a corner.
        options = []
        for k in some_bits(dom[best], look):
            d2 = dom[:]
            d2[best] = 1 << k
            if prune(d2, [best]):
                room = sum(math.log(m.bit_count()) for m in d2)
                options.append((room + rng.random() * 3, d2))
        options.sort(key=lambda o: -o[0])
        for _, d2 in options[:branch]:
            r = solve(d2)
            if r:
                return r
        return None

    try:
        ws = solve(dom) if prune(dom, range(len(SL))) else None
    except TimeUp:
        ws = None
    if not ws:
        return None
    for w, cells in zip(ws, SL):
        for (r, c), ch in zip(cells, w):
            g[r][c] = ch
    return ["".join(r) for r in g]


def weak_entries(rows, good, extra_bad=()):
    """Answers in the grid that aren't in the good-word dict, or that were flagged."""
    out = []
    for _, cells in slots(rows):
        w = "".join(rows[r][c] for r, c in cells)
        if w not in good or w in extra_bad:
            out.append((w, cells))
    return out


def improve(rows, good_index, keep, seconds=120, seed=0, extra_bad=(), backup_index=None):
    """Swap out weak answers. Repeatedly picks a weak answer, blanks it (and, if that's
    not enough room, the answers crossing it), and refills the gap using only words from
    the good index. A change is kept only if it leaves fewer weak answers. Squares in `keep`
    (the theme) are never touched. If the good words can't fit (a weak answer crossing the
    gap fixes a letter no good word has), backup_index is tried instead. Returns the best
    grid found."""
    rng = random.Random(seed)
    best = list(rows)
    all_slots = [cells for _, cells in slots(best)]
    good = good_index.words
    start = time.time()
    while time.time() - start < seconds:
        weak = [x for x in weak_entries(best, good, extra_bad) if not all(c in keep for c in x[1])]
        if not weak:
            break
        word, cells = rng.choice(weak)
        region = set(cells)
        for radius in range(3):
            if radius:
                region |= {x for s in all_slots if set(s) & region for x in s}
            region -= set(keep)
            trial = [list(r) for r in best]
            for r, c in region:
                trial[r][c] = "."
            left = seconds - (time.time() - start)
            if left <= 0:
                break
            out = None
            for index in (good_index, backup_index):
                if index is not None and not out:
                    out = fill(["".join(r) for r in trial], index, seed=rng.random(),
                               seconds=min(8, max(0.1, seconds - (time.time() - start))), avoid=set(extra_bad))
            if out and len(weak_entries(out, good, extra_bad)) < len(weak):
                best = out
                break
    return best
