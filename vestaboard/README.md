# Vestaboard Messenger

A small script that sends your own messages to your Vestaboard. It uses only
Python's built-in tools, so there is nothing extra to install.

## 1. One-time setup

1. **Check you have Python 3.** Open Terminal (Mac) or Command Prompt (Windows) and run:
   ```
   python3 --version
   ```
   If you see a version number like `Python 3.12.1`, you're set. If not, install it from
   [python.org](https://www.python.org/downloads/).

2. **Get your Cloud API token.** In the Vestaboard app, go to **Settings → Developer**,
   turn on the **Cloud API**, and copy the token. (Vestaboard used to call this the
   "Read/Write API".)

3. **Save the key.** Create a file called `api_key.txt` in this `vestaboard` folder and
   paste the token into it (just the token, nothing else). This file is listed in
   `.gitignore`, so it won't be uploaded to GitHub.

## 2. Sending a message

From inside the `vestaboard` folder:

```
python3 send_message.py "Hello world"
```

The script shows a preview of the board in your terminal and then sends it.

**Just want to see how it will look?** Add `--preview` and nothing is sent:

```
python3 send_message.py "Dinner is at 7 tonight" --preview
```

**Start a new line** with `\n`:

```
python3 send_message.py "Happy Birthday\nSam!"
```

**Add colour tiles** with `{red}`, `{orange}`, `{yellow}`, `{green}`, `{blue}`,
`{violet}`, `{white}` or `{black}`:

```
python3 send_message.py "{red}{orange}{yellow} Welcome home {yellow}{orange}{red}"
```

## Sending a message from your phone or iPad

No setup needed. On GitHub, go to **Actions → Send a message → Run workflow**, type
your message (the same `\n` and `{red}` tricks work) and tap **Run workflow**. Tick
**Just preview it** to only see the board in the run's log without sending.

## Halloween countdown

Every day at **7:47am US Eastern time from October 1 to Halloween**, the Note counts down:

```
 🟧 4 DAYS 🟧
    UNTIL
🟧 HALLOWEEN 🟧
```

On Halloween itself it says **Happy Halloween!** and stays up until the riddle at
noon. The rest of the year, nothing happens.

**Try a day any time:** **Actions → Vestaboard → Run workflow**, choose **halloween**
and type a date like `10-28` (`10-31` is Halloween itself).

## On this day in history

Every day at **8:47am US Eastern time**, the Note shows something that happened on
that date, from Wikipedia's "On this day":

```
   🟪 1969 🟪
 SESAME STREET
   PREMIERES
```

The headlines are in `on_this_day.txt`, one per line, with the date, the year and
a short headline:

```
11-10 | 1969 | Sesame Street premieres
```

Keep each headline to about 28 characters so it fits on two lines. Dates with no
line are skipped, so nothing happens after the last date in the file (December 31
for now).

**Try a day any time:** **Actions → Vestaboard → Run workflow**, choose **on this day**
and type a date like `12-24`.

## Trying ideas on a virtual board

`virtual_board.py` runs a pretend Note in your web browser, so you can see how
something looks (flapping tiles and all) before it goes to the real board.

1. Start it, and leave it running:
   ```
   python3 virtual_board.py
   ```
2. Open **http://localhost:7000**. (In a Codespace, open the **Ports** tab and click
   the globe next to port 7000.)
3. Type a message into the box under the board, or put `VESTABOARD_VIRTUAL=1` in front of
   any script to send it to the virtual board instead of the real one:
   ```
   VESTABOARD_VIRTUAL=1 python3 send_message.py "{green} Welcome home {green}"
   VESTABOARD_VIRTUAL=1 python3 riddle.py --answer
   VESTABOARD_VIRTUAL=1 python3 christmas.py --date 12-16
   ```

The virtual board accepts exactly what the real one does, so anything that works
there will work on your Note. It doesn't need an API key, and the Sonos stays quiet.

## Good to know

- This is set up for a **Vestaboard Note: 3 lines × 15 characters** (45 in total). Messages are word-wrapped and centred
  automatically; the script tells you if one is too long.
- Letters are shown in capitals. Supported symbols: `! @ # $ ( ) - + & = ; : ' " % , . / ? °`
- Vestaboard limits how often you can post (roughly once every 15 seconds), and
  sending the exact same message twice in a row is refused.

## Schedules

Everything that goes up on its own is planned in **`schedule.py`**, in one list, in
US Eastern time:

| Time | What | When |
|---|---|---|
| 7:47am | 12 Days of Christmas, or the Halloween countdown | December 14–25, October 1–31 |
| 8:47am | On this day | Any date with a headline |
| 11:47am | Riddle, with the thinking jingle | Every day |
| 5:47pm | Riddle answer, with the drum roll | Every day |

**See what's planned:** `python3 schedule.py` shows today's plan, and
`python3 schedule.py --date 12-16` shows any other day.

**Why 13 minutes early:** GitHub is busiest on the hour and often starts scheduled
jobs late.

**When GitHub runs late:** if a run starts so late that it would cover up the next
message, or more than 3 hours late, it's skipped that day rather than showing up at
the wrong time. The run's log on GitHub says what happened.

**Send anything now:** **Actions → Vestaboard → Run workflow**, choose what to send,
and optionally type a date like `12-24` to pretend it's that day.

**Change a time:** edit the time in `SLOTS` near the top of `schedule.py`, then run
`python3 schedule.py --check`. It tells you which `cron` lines to put in
`.github/workflows/vestaboard.yml` (GitHub needs two for each time, one for summer
time and one for winter).

**Checked automatically:** whenever you change a riddle, headline or anything else
here, GitHub runs **Check the board** to make sure it all still fits. If something
doesn't, you'll see a red ✗ next to your change, and the log says which line to fix.

**Note:** GitHub pauses scheduled jobs if nothing in the repository changes for 60
days. It emails you first, and you can switch them back on from the Actions tab
(or just edit a riddle).

## Daily riddle

Every day at **11:47am US Eastern time** a riddle appears, and at **5:47pm** its answer.
The riddles are in `riddles.txt`, one per line, with a `|` between the riddle and
the answer, for example:

```
What has keys but can't open locks? | A piano
```

They come out in a random order with no repeats until every riddle has been used.
Keep each riddle to about 40 characters so it fits on the Note.

**Send one now:** on GitHub, go to **Actions → Vestaboard → Run workflow**, and
choose **riddle** or **riddle answer**.

## The 12 Days of Christmas

Every day at **7:47am US Eastern time from December 14 (day 1) to Christmas Day (day 12)**,
a Christmas song starts on the Sonos and then the Note shows the day's gift:

```
 🟥🟩 DAY 3 🟩🟥
 3 FRENCH HENS
```

Outside those 12 days, nothing happens.

**Choosing the songs:**
1. In the Sonos app, find each Christmas song on Amazon Music, tap **⋯** and choose
   **Add to Sonos Favorites**. Save single songs, not playlists, or the music won't stop.
2. On GitHub, run **Actions → Vestaboard → Run workflow** with
   **list Sonos favourites** to see their exact names in the log.
3. Edit `christmas.txt`: after each day's `|`, type the favourite's name (or just part of it,
   like `Jingle Bell Rock`).

**Try a day any time:** **Actions → Vestaboard → Run workflow**, choose **christmas**
and type a date like `12-16` (day 3).
