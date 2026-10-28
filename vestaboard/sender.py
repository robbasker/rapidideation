"""
Sending a board to the Vestaboard through its Cloud API, or to virtual_board.py
when VESTABOARD_VIRTUAL is set.
"""

import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://cloud.vestaboard.com/"
VIRTUAL_URL = "http://localhost:7000/"  # see virtual_board.py


def load_api_key():
    """Read the key from the VESTABOARD_API_KEY variable or the api_key.txt file."""
    key = os.environ.get("VESTABOARD_API_KEY")
    if key:
        return key.strip()
    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")
    if os.path.exists(key_file):
        with open(key_file) as f:
            return f.read().strip()
    return None


def send(board, api_key, url=API_URL):
    request = urllib.request.Request(
        url,
        data=json.dumps({"characters": board}).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Vestaboard-Token": api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.status, response.read().decode(errors="replace")


def send_to_board(board):
    """Send the board using the saved API key, explaining any problem in plain English."""
    if os.environ.get("VESTABOARD_VIRTUAL"):
        send_to_virtual_board(board)
        return

    api_key = load_api_key()
    if not api_key:
        sys.exit("No API key found. Put your key in vestaboard/api_key.txt (see README.md).")

    try:
        status, reply = send(board, api_key)
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            sys.exit("Vestaboard rejected the API key. Check that it's your Cloud API token.")
        if error.code == 409:
            print("That message is already on the board, so there was nothing to change.")
            return
        sys.exit(f"Vestaboard returned an error: {error.code} {error.reason}")
    except urllib.error.URLError as error:
        sys.exit(f"Couldn't reach Vestaboard: {error.reason}")
    print("Sent to your Vestaboard!")
    print(f"Vestaboard's reply ({status}): {reply}")


def send_to_virtual_board(board):
    """Send the board to virtual_board.py instead of the real Vestaboard."""
    try:
        send(board, "virtual", VIRTUAL_URL)
    except urllib.error.HTTPError as error:
        if error.code == 409:
            print("That message is already on the virtual board, so there was nothing to change.")
            return
        sys.exit(f"The virtual board returned an error: {error.code} {error.reason}")
    except urllib.error.URLError:
        sys.exit("Couldn't reach the virtual board. Start it with: python3 virtual_board.py")
    print(f"Sent to the virtual board at {VIRTUAL_URL}")
