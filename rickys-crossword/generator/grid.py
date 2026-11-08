"""Crossword grid shapes: finding answer slots, checking the rules, numbering, and
searching for black-square patterns that hold a given set of theme answers.

Grids are lists of 15 strings. "#" is a black square, "." an empty white square,
and a letter is a filled white square.
"""
import random

N = 15


def slots(g):
    """Every Across and Down answer slot of two or more squares: (dir, [(r, c), ...])."""
    out = []
    for r in range(N):
        c = 0
        while c < N:
            if g[r][c] == "#":
                c += 1
                continue
            s = c
            while c < N and g[r][c] != "#":
                c += 1
            if c - s > 1:
                out.append(("A", [(r, x) for x in range(s, c)]))
    for c in range(N):
        r = 0
        while r < N:
            if g[r][c] == "#":
                r += 1
                continue
            s = r
            while r < N and g[r][c] != "#":
                r += 1
            if r - s > 1:
                out.append(("D", [(x, c) for x in range(s, r)]))
    return out


def problems(g, max_len=None, fixed=()):
    """A list of rule breaks: not symmetric, answers under 3 letters, squares in only one
    answer, white squares cut off from the rest, or (if max_len) non-theme answers that
    are too long. An empty list means the grid shape is legal."""
    errs = []
    for r in range(N):
        for c in range(N):
            if (g[r][c] == "#") != (g[N - 1 - r][N - 1 - c] == "#"):
                errs.append(("asymmetric", r, c))
    count = {}
    for d, cells in slots(g):
        if len(cells) < 3:
            errs.append(("short", d, cells[0]))
        if max_len and len(cells) > max_len and not all(x in fixed for x in cells):
            errs.append(("long", d, cells[0]))
        for x in cells:
            count[x] = count.get(x, 0) + 1
    whites = [(r, c) for r in range(N) for c in range(N) if g[r][c] != "#"]
    for x in whites:
        if count.get(x, 0) < 2:
            errs.append(("unchecked",) + x)
    if whites:
        seen, todo = {whites[0]}, [whites[0]]
        while todo:
            r, c = todo.pop()
            for y in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= y[0] < N and 0 <= y[1] < N and g[y[0]][y[1]] != "#" and y not in seen:
                    seen.add(y)
                    todo.append(y)
        if len(seen) != len(whites):
            errs.append(("disconnected",))
    return errs


def numbered(g):
    """[(number, dir, row, col, answer)] in the order a newspaper prints them."""
    black = lambda r, c: r < 0 or c < 0 or r >= N or c >= N or g[r][c] == "#"
    out, n = [], 0
    for r in range(N):
        for c in range(N):
            if black(r, c):
                continue
            a = black(r, c - 1) and not black(r, c + 1)
            d = black(r - 1, c) and not black(r + 1, c)
            if a or d:
                n += 1
            for flag, dr, dc, name in ((a, 0, 1, "A"), (d, 1, 0, "D")):
                if flag:
                    w, rr, cc = "", r, c
                    while not black(rr, cc):
                        w += g[rr][cc]
                        rr, cc = rr + dr, cc + dc
                    out.append((n, name, r, c, w))
    return out


# ---- Theme layouts ------------------------------------------------------------
# Three theme answers: one across row 3 from the left edge, one centred on row 7, and
# one across row 11 to the right edge (the mirror of row 3, so both are the same length).

def theme_cells(outer, middle):
    """The squares the three theme answers fill, in order, and the black squares that
    must end them."""
    s = (N - middle) // 2
    cells = [[(3, c) for c in range(outer)],
             [(7, c) for c in range(s, s + middle)],
             [(11, c) for c in range(N - outer, N)]]
    stops = set()
    if outer < N:
        stops |= {(3, outer), (11, N - 1 - outer)}
    if middle < N:
        stops |= {(7, s - 1), (7, s + middle)}
    return cells, stops


def ugliness(g, max_black=40):
    """Penalties for legal but unattractive shapes: too many black squares, 2x2 black
    clumps, long black walls and too many three-letter answers."""
    nb = sum(row.count("#") for row in g)
    bad = max(0, nb - max_black) * 5
    for r in range(N - 1):
        for c in range(N - 1):
            if g[r][c] == g[r + 1][c] == g[r][c + 1] == g[r + 1][c + 1] == "#":
                bad += 4
    for line in list(g) + ["".join(g[r][c] for r in range(N)) for c in range(N)]:
        line = "".join(line)
        bad += 4 * sum(max(0, len(run) - 3) for run in line.replace(".", " ").split() if set(run) == {"#"})
    threes = sum(1 for d, cells in slots(g) if len(cells) == 3)
    bad += max(0, threes - 16) * 2
    return bad


def search_pattern(outer, middle, rng, max_len=8, max_black=40, steps=40000):
    """Simulated annealing over symmetric black-square layouts until one is legal.
    Returns the grid with "." for white squares, or None if this attempt got stuck."""
    cells, stops = theme_cells(outer, middle)
    fixed = {x for cs in cells for x in cs}
    g = [["." for _ in range(N)] for _ in range(N)]
    for r, c in stops:
        g[r][c] = "#"
    free = [(r, c) for r in range(N) for c in range(N)
            if (r, c) not in fixed and (r, c) not in stops and (r * N + c) <= (N * N) // 2]
    for r, c in rng.sample(free, 18):
        g[r][c] = g[N - 1 - r][N - 1 - c] = "#"

    def cost(g):
        return len(problems(g, max_len, fixed)) * 10 + ugliness(g, max_black)

    cur = cost(g)
    temp = 3.0
    for i in range(steps):
        if cur == 0:
            return ["".join(row) for row in g]
        r, c = rng.choice(free)
        mr, mc = N - 1 - r, N - 1 - c
        new = "." if g[r][c] == "#" else "#"
        g[r][c] = g[mr][mc] = new
        nc = cost(g)
        if nc <= cur or rng.random() < pow(2.718, (cur - nc) / temp):
            cur = nc
        else:
            g[r][c] = g[mr][mc] = "." if new == "#" else "#"
        temp = max(0.05, temp * 0.9997)
    return None
