# Making the daily puzzle (instructions for Claude)

A scheduled Claude Code routine follows these steps every evening to make the next day's
Ricky's Crossword. You are the constructor and editor: you choose the theme, judge the
fill and write the clues. `make_puzzle.py` does the grid work. Work in
`rickys-crossword/generator`.

## 1. Check what's needed

```
python3 make_puzzle.py next
```

This prints tomorrow's date (UTC), whether a puzzle already exists, recent theme titles
and the allowed theme letter counts. If the puzzle already exists, stop: there's nothing
to do. (The first run downloads two word lists, about 10 MB, from GitHub.)

## 2. Choose a theme

Write 6 theme ideas to `/tmp/ideas.json`, most enjoyable first, from different subject
areas, and unlike the recent themes:

```json
[{"title": "Food for Thought", "link": "People described as foods",
  "answers": ["Smart cookie", "Big cheese", "Couch potato"]}]
```

- Each idea is three answers that share a hidden link the solver works out: puns, hidden
  words, a common category, a twist on phrases, wordplay and so on. A seasonal or
  date-related idea is welcome.
- Each answer is a well-known word or phrase that stands on its own.
- The letter counts (ignoring spaces and punctuation) must be one of the allowed sets
  (first, middle, last), and the first and last counts are always equal. Count the
  letters of every answer carefully, one by one, before writing the file.

## 3. Fill the grid

```
python3 make_puzzle.py grid --ideas /tmp/ideas.json
```

This takes up to 9 minutes. It tries the ideas in order and prints the grid and every
entry. `*` marks theme answers, and `?` marks entries with low word-list scores. The `?`
is only a hint: many marked entries are fine, and some unmarked ones aren't.

## 4. Edit the fill

Read every non-theme entry as a newspaper editor would. Reject entries that are
offensive or unpleasant, made-up or wrong, ugly abbreviations, awkward partial phrases,
random roman numerals, or names so obscure that most keen solvers wouldn't know them.
Ordinary crossword fare (EPEE, ALOE, ORE and the like) is fine. Then replace the rejects:

```
python3 make_puzzle.py polish --avoid WORD,WORD,WORD
```

Review the new grid and repeat up to three times. Words stay avoided between rounds. A
puzzle with one or two slightly weak entries is acceptable; don't loop forever. If a
rejected word is offensive, also add it to `blocklist.txt` so it's never used again.

## 5. Write the clues

Write `/tmp/clues.json` with one clue for every entry in the final listing:

```json
{"title": "...", "explanation": "...",
 "clues": [{"number": 1, "direction": "A", "clue": "..."}]}
```

- Hard, end-of-week difficulty: misdirection, double meanings, and question marks on
  playful or punny clues. Mix in straight but knowing definitions so it's fair.
- Use fill-in-the-blank clues sparingly.
- The three theme answers get clues that hint at the shared link without giving it away.
- Every clue must be accurate and must not contain its answer or a form of it.
- Signal abbreviations, partial phrases and multi-word answers in the usual way ("Abbr.",
  "for short", "2 wds.").
- The title is short and witty. The explanation is one or two sentences, shown when the
  solver finishes.

Then save it:

```
python3 make_puzzle.py finish --clues /tmp/clues.json
```

If it reports missing or leaking clues, fix the file and run `finish` again.

## 6. Publish

Commit only `rickys-crossword/puzzles/` (and `generator/blocklist.txt` if you changed
it) straight to `main`, with a message like "Add Ricky's Crossword for 2026-11-09", and
push to `origin main`. If the push is rejected because `main` moved on, run
`git pull --rebase origin main` and push again. Don't open a pull request.

Finish with a short summary: the date, title, theme answers, and any entries you weren't
happy with.
