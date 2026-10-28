#!/usr/bin/env python3
"""
Send a custom message to your Vestaboard.

Examples:
    python3 send_message.py "Hello world"
    python3 send_message.py "Dinner at 7" --preview
    python3 send_message.py "{green} Welcome home {green}"

Only uses Python's built-in libraries, so there is nothing to install.
"""

import argparse
import sys

from board import build_board, preview
from sender import send_to_board


def main():
    parser = argparse.ArgumentParser(description="Send a message to your Vestaboard.")
    parser.add_argument("message", help='The message to show, e.g. "Hello world"')
    parser.add_argument("--preview", action="store_true",
                        help="Only show what the board would look like; don't send it")
    args = parser.parse_args()

    try:
        board = build_board(args.message.replace("\\n", "\n"))
    except ValueError as error:
        sys.exit(f"Sorry: {error}")

    preview(board)
    if not args.preview:
        send_to_board(board)


if __name__ == "__main__":
    main()
