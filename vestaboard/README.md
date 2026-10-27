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

Every day at **8am US Eastern time from October 1 to Halloween**, the Note counts down:

```
 🟧 4 DAYS 🟧
    UNTIL
🟧 HALLOWEEN 🟧
```

On Halloween itself it says **Happy Halloween!** and stays up until the riddle at
noon. The rest of the year, nothing happens.

**Try a day any time:** **Actions → Halloween countdown → Run workflow**, and type how
many days to go (0 is Halloween).

## On this day in history

Every day at **9am US Eastern time**, the Note shows something that happened on
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

**Try a day any time:** **Actions → On this day → Run workflow**, and type a date
like `12-24`.

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
   VESTABOARD_VIRTUAL=1 python3 christmas.py --day 3
   ```

The virtual board accepts exactly what the real one does, so anything that works
there will work on your Note. It doesn't need an API key. (`christmas.py` still
plays its song on the real Sonos.)

## Good to know

- This is set up for a **Vestaboard Note: 3 lines × 15 characters** (45 in total). Messages are word-wrapped and centred
  automatically; the script tells you if one is too long.
- Letters are shown in capitals. Supported symbols: `! @ # $ ( ) - + & = ; : ' " % , . / ? °`
- Vestaboard limits how often you can post (roughly once every 15 seconds), and
  sending the exact same message twice in a row is refused.

## Daily love messages

**Switched off for now** (so the Halloween countdown stays up all morning). You can
still send one with the button below. To switch it back on, follow the note at the
top of `.github/workflows/love-message.yml`.

When it's on, every morning at **9am US Eastern time**, GitHub sends a line from a Robert Burns
poem to the board. Your iPad doesn't need to be switched on. The messages are in
`love_messages.txt`, one per line, and come out in a random order with no repeats
until every message has been used.

**Add or change messages:** edit `love_messages.txt` on GitHub (tap the file, then
the pencil icon). Keep each one to a line; it's wrapped onto the board automatically.

**Change the time:** in `.github/workflows/love-message.yml`, the two `cron` lines
are in UTC. For an hour earlier, change `47 12` → `47 11` and `47 13` → `47 12`, and make the
same changes in the two `if` lines further down.

**Why 13 minutes early:** each job is set for 13 minutes before the hour (8:47am for the
love message, 11:47am for the riddle, 5:47pm for the answer, 7:47am for Christmas and
the Halloween countdown, 8:47am for On this day),
because GitHub is busiest on the hour and often starts scheduled jobs late.

**Send one now:** on GitHub, go to **Actions → Daily love message → Run workflow**.

**Note:** GitHub pauses scheduled jobs if nothing in the repository changes for 60
days. It emails you first, and you can switch it back on from the Actions tab
(or just edit a message).

## Daily riddle

Every day at **12pm US Eastern time** a riddle appears, and at **6pm** its answer.
The riddles are in `riddles.txt`, one per line, with a `|` between the riddle and
the answer, for example:

```
What has keys but can't open locks? | A piano
```

They come out in a random order with no repeats until every riddle has been used.
Keep each riddle to about 40 characters so it fits on the Note.

**Send one now:** on GitHub, go to **Actions → Daily riddle → Run workflow**, and
choose **riddle** or **answer**.

## The 12 Days of Christmas

Every day at **8am US Eastern time from December 14 (day 1) to Christmas Day (day 12)**,
a Christmas song starts on the Sonos and then the Note shows the day's gift:

```
 🟥🟩 DAY 3 🟩🟥
 3 FRENCH HENS
```

Outside those 12 days, nothing happens.

**Choosing the songs:**
1. In the Sonos app, find each Christmas song on Amazon Music, tap **⋯** and choose
   **Add to Sonos Favorites**. Save single songs, not playlists, or the music won't stop.
2. On GitHub, run **Actions → 12 Days of Christmas → Run workflow** with
   **list Sonos favourites** to see their exact names in the log.
3. Edit `christmas.txt`: after each day's `|`, type the favourite's name (or just part of it,
   like `Jingle Bell Rock`).

**Try a day any time:** **Actions → 12 Days of Christmas → Run workflow**, choose
**send a day** and the day number.
