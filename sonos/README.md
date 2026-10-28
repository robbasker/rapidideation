# Sonos sounds

When the noon riddle goes up on the Vestaboard Note, your Sonos speaker plays a
"thinking" jingle. When the 6pm answer goes up, it plays a drum roll and cymbal crash first. It runs from GitHub through the Sonos cloud, so no
computer needs to be left on at home.

- `drum_roll.wav` and `thinking_jingle.wav` are the sounds. They were made by
  `make_drum_roll.py` and `make_thinking_jingle.py`, with no recordings involved.
- `sonos.py` talks to Sonos. `python3 sonos.py link` and `python3 sonos.py setup` are the one-time sign-in, and
  `python3 sonos.py drumroll` and `python3 sonos.py thinking` play the sounds.

## One-time setup

1. **Create a Sonos developer integration.** Sign in at
   [developer.sonos.com](https://developer.sonos.com) with your normal Sonos account. Create a new
   **Control Integration**, then add an **API key** to it. Set its **Redirect URI** to:
   ```
   https://github.com/robbasker/rapidideation
   ```
   Keep the **Key** and **Secret** it shows you.

2. **Sign in from iSH on your iPad.** Download the script, then print your sign-in link:
   ```
   python3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/robbasker/rapidideation/main/sonos/sonos.py', 'sonos.py')"
   python3 sonos.py link YOUR_KEY
   ```
   Open the link in Safari and sign in. You'll land on this GitHub repo; copy that page's
   full address (it contains `code=`). Then finish, keeping the single quotes around the address:
   ```
   python3 sonos.py setup YOUR_KEY YOUR_SECRET 'PASTE_THE_ADDRESS_HERE'
   ```
   The code in the address only works once and expires quickly, so do this straight away.
   A test drum roll plays (if you have one speaker) and you get four values.

3. **Save the four values as GitHub secrets**, in the same place as `VESTABOARD_API_KEY`:
   `SONOS_CLIENT_ID`, `SONOS_CLIENT_SECRET`, `SONOS_REFRESH_TOKEN` and `SONOS_PLAYER_ID`.

**Test it:** go to **Actions → Vestaboard → Run workflow** and choose **riddle answer**.

**Play a sound any time:** go to **Actions → Play a sound → Run workflow** and pick
**laugh** (a Halloween "mwa-ha-ha-ha-haaa", made by `make_evil_laugh.py`), **drumroll**
or **thinking**.

**Change the volume:** edit `VOLUME` near the top of `sonos.py` (0 to 100).

If a sound ever fails, the riddle or answer still goes up on the Note.
