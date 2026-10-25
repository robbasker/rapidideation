#!/usr/bin/env python3
"""
Play sounds on your Sonos speaker through the Sonos cloud.

    python3 sonos.py link KEY                    print the Sonos sign-in link
    python3 sonos.py setup KEY SECRET 'ADDRESS'  finish signing in; tells you what to save on GitHub
    python3 sonos.py drumroll                    play the drum roll
    python3 sonos.py thinking                    play the thinking jingle

Only uses Python's built-in libraries, so there is nothing to install.
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

LOGIN_URL = "https://api.sonos.com/login/v3/oauth"
TOKEN_URL = "https://api.sonos.com/login/v3/oauth/access"
CONTROL_URL = "https://api.ws.sonos.com/control/api/v1"
REDIRECT_URI = "https://github.com/robbasker/rapidideation"
# The sound files are served by jsDelivr from one fixed version of this repository.
# (Using "@main" instead can serve an out-of-date copy for up to 12 hours.)
# If you change or add a sound, update this to the newest commit ID that includes it.
SOUNDS_VERSION = "3761deb41576e67e51ca6ba2cf10b4d022ff0586"
SOUNDS_URL = f"https://cdn.jsdelivr.net/gh/robbasker/rapidideation@{SOUNDS_VERSION}/sonos/"
DRUM_ROLL_URL = SOUNDS_URL + "drum_roll.wav"
VOLUME = 70  # 0 to 100

# The sounds you can play, by command name: (description, file address)
SOUNDS = {
    "drumroll": ("Drum roll", DRUM_ROLL_URL),
    "thinking": ("Thinking jingle", SOUNDS_URL + "thinking_jingle.wav"),
}


def request(url, data=None, headers=None, method=None):
    """Send a request to Sonos and return the reply as a dictionary."""
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            body = response.read()
    except urllib.error.HTTPError as error:
        sys.exit(f"Sonos returned an error: {error.code} {error.reason}\n{error.read().decode(errors='replace')}")
    except urllib.error.URLError as error:
        sys.exit(f"Couldn't reach Sonos: {error.reason}")
    return json.loads(body) if body else {}


def get_tokens(client_id, client_secret, form):
    """Swap a sign-in code (or a refresh token) for an access token."""
    login = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    return request(
        TOKEN_URL,
        data=urllib.parse.urlencode(form).encode(),
        headers={
            "Authorization": f"Basic {login}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )


def control(access_token, path, body=None):
    """Call the Sonos Control API."""
    headers = {"Authorization": f"Bearer {access_token}"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    return request(CONTROL_URL + path, data=data, headers=headers, method="POST" if data else "GET")


def play_clip(access_token, player_id, url, volume, name="Drum roll"):
    """Play a sound file on one speaker, over the top of anything already playing."""
    return control(access_token, f"/players/{player_id}/audioClip", {
        "name": name,
        "appId": "com.github.robbasker.vestaboard",
        "streamUrl": url,
        "volume": volume,
        "priority": "HIGH",
    })


def check_sound_file(url):
    """Make sure the speaker will be able to download the sound, and say so in the log."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=15) as response:
            print(f"Sound file OK: {response.headers.get('Content-Type')}, "
                  f"{response.headers.get('Content-Length')} bytes")
    except urllib.error.HTTPError as error:
        sys.exit(f"The speaker couldn't download the sound file ({error.code} {error.reason}): {url}")
    except urllib.error.URLError as error:
        sys.exit(f"Couldn't reach the sound file ({error.reason}): {url}")


def play_sound(command):
    name, url = SOUNDS[command]
    check_sound_file(url)
    settings = {}
    for setting in ("SONOS_CLIENT_ID", "SONOS_CLIENT_SECRET", "SONOS_REFRESH_TOKEN", "SONOS_PLAYER_ID"):
        settings[setting] = (os.environ.get(setting) or "").strip()
        if not settings[setting]:
            sys.exit(f"{setting} isn't set, so there's no sound. See sonos/README.md.")
    tokens = get_tokens(settings["SONOS_CLIENT_ID"], settings["SONOS_CLIENT_SECRET"], {
        "grant_type": "refresh_token",
        "refresh_token": settings["SONOS_REFRESH_TOKEN"],
    })
    reply = play_clip(tokens["access_token"], settings["SONOS_PLAYER_ID"], url, VOLUME, name)
    print(f"{name} sent to Sonos. Sonos's reply: {json.dumps(reply)}")


def ask(prompt):
    """Keep asking until something is typed in."""
    while True:
        answer = input(prompt).strip()
        if answer:
            return answer
        print("That was blank, please try again.")


def sign_in_link(client_id):
    return LOGIN_URL + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "state": "vestaboard",
        "scope": "playback-control-all",
        "redirect_uri": REDIRECT_URI,
    })


def setup(client_id=None, client_secret=None, landed=None):
    print("Sonos setup. You'll need the Key and Secret from your Sonos developer integration.\n")
    client_id = client_id or ask("Paste the Key: ")
    client_secret = client_secret or ask("Paste the Secret: ")

    if not landed:
        print("\n1. Copy this link into Safari and sign in with your Sonos account:\n")
        print(sign_in_link(client_id))
        print("\n2. When it's done, you'll land on a GitHub page. Copy that page's full")
        print("   address from Safari's address bar (it contains 'code=').\n")
        landed = ask("Paste the address here: ")
    if "code=" in landed:
        code = urllib.parse.parse_qs(urllib.parse.urlparse(landed).query).get("code", [None])[0]
    else:
        code = landed.strip()
    if not code:
        sys.exit("That address doesn't contain a code. Please try the setup again.")

    tokens = get_tokens(client_id, client_secret, {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    })
    access_token = tokens["access_token"]

    speakers = []
    for household in control(access_token, "/households").get("households", []):
        groups = control(access_token, f"/households/{household['id']}/groups")
        speakers += [p for p in groups.get("players", []) if "AUDIO_CLIP" in p.get("capabilities", [])]
    if not speakers:
        sys.exit("None of your Sonos speakers can play sound clips, sorry.")

    if len(speakers) == 1:
        speaker = speakers[0]
        print(f"\nPlaying a test drum roll on {speaker['name']}...")
        play_clip(access_token, speaker["id"], DRUM_ROLL_URL, VOLUME)
        player_id = speaker["id"]
    else:
        print("\nSpeakers that can play the drum roll, and the ID to save for each:\n")
        for speaker in speakers:
            print(f"  {speaker['name']}:  {speaker['id']}")
        player_id = "(the ID of the speaker you want, from the list above)"

    print("\nAll done! Add these four secrets on GitHub (same place as VESTABOARD_API_KEY):\n")
    print(f"  SONOS_CLIENT_ID       {client_id}")
    print(f"  SONOS_CLIENT_SECRET   {client_secret}")
    print(f"  SONOS_REFRESH_TOKEN   {tokens['refresh_token']}")
    print(f"  SONOS_PLAYER_ID       {player_id}")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "setup":
        setup(*sys.argv[2:5])
    elif command == "link" and len(sys.argv) > 2:
        print(sign_in_link(sys.argv[2]))
    elif command in SOUNDS:
        play_sound(command)
    else:
        sys.exit(__doc__)
