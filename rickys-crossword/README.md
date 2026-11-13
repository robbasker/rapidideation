# Ricky's Crossword

A new 15 × 15 crossword for Ricky every day, in the style of a daily newspaper puzzle,
always at the same link: https://robbasker.github.io/rapidideation/rickys-crossword/

Each puzzle is hard, end-of-week difficulty, with a fresh theme: three long answers
share a hidden link, which is explained when you finish. The ‹ › arrows next to the
date go to earlier puzzles.

## Playing

| Key | What it does |
|---|---|
| Letters | Fill the square and move on to the next empty one |
| ← → ↑ ↓ | Move around the grid (an arrow across the current direction turns it) |
| Space, or click the same square again | Switch between Across and Down |
| Tab / Shift-Tab, or Enter | Next or previous clue |
| Backspace | Delete |
| . (full stop) | Pencil on or off |

- **Pencil:** letters you're unsure of show in grey.
- **Check:** marks wrong letters in a square, word or the whole puzzle with a red slash.
  Correct letters turn blue and stay locked. Autocheck checks each letter as you type it.
- **Reveal:** fills in a square, word or the whole puzzle. Revealed squares get a blue
  corner.
- **Clear:** wipes incomplete words, the current word, or the whole puzzle. "Puzzle &
  timer" also resets the clock.
- **Timer:** pauses when you press pause or switch to another tab.
- **Saving:** the puzzle remembers your letters and time if you close it partway through.
- Phones and tablets get an on-screen keyboard, so the device's own keyboard never
  covers the grid.

## Seeing who's playing

The page can send a few anonymous events to [GoatCounter](https://www.goatcounter.com),
a free, privacy-friendly counter, so you can check from anywhere whether the puzzles
are being played. Each event names the puzzle's date:

| Event | When it's sent |
|---|---|
| Opened 2026-11-14 | The puzzle is opened (once per visit) |
| Finished 2026-11-14 in 12:34 | It's completed, with the time. ", with reveals" is added if any squares were revealed |
| Revealed a square / word / the whole puzzle on 2026-11-14 | Reveal is used (each kind once per visit) |
| Left 2026-11-14 unfinished (40% filled, 8:15) | The page is closed or switched away from with letters in but not finished (once per visit) |

To switch it on:

1. Sign up at goatcounter.com and choose a code name (for example `rickys-crossword`).
   Your dashboard is then at `https://<code name>.goatcounter.com`.
2. In `index.html`, put that code name in `const GOATCOUNTER = "";`.
3. On your own phone and computer, open the crossword once with `?notrack` on the end of
   the link, so your own visits aren't counted. `?track` turns counting back on.

The events appear under "Pages" on the dashboard. A visit that's left unfinished and
later finished shows up as both.

## How the daily puzzle is made

Every evening a scheduled Claude Code routine makes the next day's puzzle and commits it
to `puzzles/YYYY-MM-DD.json` on `main`. It runs on a Claude subscription, so there's no
API key or API bill. The page shows the puzzle for the solver's own date (or the newest
one if that isn't out yet); `?date=YYYY-MM-DD` opens a particular one.

The routine follows `generator/DAILY.md`:

1. Claude picks a theme: three answers that share a hidden link, with lengths that fit
   one of the grid shapes in `generator/patterns.json`.
2. `make_puzzle.py grid` fits the theme into a shape and fills the rest with words from
   two public crossword word lists (`generator/filler.py`). It then keeps replacing
   weak (low-scoring) words with better ones.
3. Claude reads the fill like an editor, and `make_puzzle.py polish` replaces anything
   it rejects.
4. Claude writes the clues, a title and the theme explanation, and
   `make_puzzle.py finish` checks them and saves the puzzle.

To change how puzzles are made (difficulty, clue style), edit `generator/DAILY.md`. The
routine reads it fresh every run.

### Running it yourself

You can make a puzzle by hand in a Claude Code session: ask it to follow
`rickys-crossword/generator/DAILY.md` (add "for 2026-12-25" to pick the date, and pass
`--date` to every step).

- To stop a word ever appearing, add it to `generator/blocklist.txt`.
- `python3 build_patterns.py` rebuilds the grid shapes (takes about 20 minutes).
- To fix a clue by hand, edit that day's JSON file in `puzzles/`.
- To see the page locally, serve the folder (for example `python3 -m http.server`)
  rather than opening `index.html` directly, because it loads the puzzle files.
