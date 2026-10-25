# Sonos drum roll

When the 6pm riddle answer goes up on the Vestaboard Note, your Sonos speaker plays a
drum roll and cymbal crash first. It runs from GitHub through the Sonos cloud, so no
computer needs to be left on at home.

- `drum_roll.wav` is the sound. It was made by `make_drum_roll.py`, with no recordings involved.
- `sonos.py` talks to Sonos. `python3 sonos.py setup` is the one-time sign-in, and
  `python3 sonos.py drumroll` plays the drum roll.

## One-time setup

1. **Create a Sonos developer integration.** Sign in at
   [developer.sonos.com](https://developer.sonos.com) with your normal Sonos account. Create a new
   **Control Integration**, then add an **API key** to it. Set its **Redirect URI** to:
   ```
   https://github.com/robbasker/rapidideation
   ```
   Keep the **Key** and **Secret** it shows you.

2. **Sign in from iSH on your iPad:**
   ```
   apk add curl
   curl -O https://raw.githubusercontent.com/robbasker/rapidideation/main/sonos/sonos.py
   python3 sonos.py setup
   ```
   Follow the steps on screen. At the end, a test drum roll plays and you get four values.

3. **Save the four values as GitHub secrets**, in the same place as `VESTABOARD_API_KEY`:
   `SONOS_CLIENT_ID`, `SONOS_CLIENT_SECRET`, `SONOS_REFRESH_TOKEN` and `SONOS_PLAYER_ID`.

**Test it:** go to **Actions → Daily riddle → Run workflow** and choose **answer**.

**Change the volume:** edit `DRUM_ROLL_VOLUME` near the top of `sonos.py` (0 to 100).

If the drum roll ever fails, the riddle answer still goes up on the Note.
