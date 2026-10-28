#!/usr/bin/env python3
"""
A pretend Vestaboard Note that runs on your computer, for trying ideas out before
they go to the real board.

    python3 virtual_board.py              start it, then open http://localhost:7000
    python3 virtual_board.py --port 8080  use a different port

While it's running, send any script to it instead of the real board by putting
VESTABOARD_VIRTUAL=1 in front:

    VESTABOARD_VIRTUAL=1 python3 riddle.py
    VESTABOARD_VIRTUAL=1 python3 send_message.py "Hello world"

You can also type messages straight into the box under the board.

It accepts the same {"characters": [...]} message as the Vestaboard Cloud API, so
anything that works here will work on the real board.

Only uses Python's built-in libraries, so there is nothing to install.
"""

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from board import CODE_TO_CHAR, COLOR_CODES, COLS, ROWS, build_board

DEFAULT_PORT = 7000

state = {"board": build_board("Virtual\nVestaboard"), "version": 1}
state_lock = threading.Lock()


def valid_board(board):
    """True if the board is a ROWS x COLS grid of tile codes the Note understands."""
    return (
        isinstance(board, list)
        and len(board) == ROWS
        and all(isinstance(row, list) and len(row) == COLS for row in board)
        and all(isinstance(code, int) and (code in CODE_TO_CHAR or code in COLOR_CODES.values())
                for row in board for code in row)
    )


def show(board):
    """Put a board on the screen. Returns False if it's already showing, like the real board."""
    with state_lock:
        if board == state["board"]:
            return False
        state["board"] = board
        state["version"] += 1
        return True


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="application/json"):
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return None

    def do_GET(self):
        if self.path == "/":
            self.reply(200, PAGE, "text/html; charset=utf-8")
        elif self.path == "/board":
            with state_lock:
                self.reply(200, state)
        else:
            self.reply(404, {"error": "Not found"})

    def do_POST(self):
        body = self.read_json()
        if not isinstance(body, dict):
            self.reply(400, {"error": "That wasn't valid JSON."})
            return

        if self.path == "/":
            # The same message the Vestaboard Cloud API takes.
            board = body.get("characters")
            if not valid_board(board):
                self.reply(400, {"error": f"'characters' must be {ROWS} rows of {COLS} tile codes."})
                return
        elif self.path == "/message":
            # Plain text from the box on the page, wrapped just like send_message.py does it.
            try:
                board = build_board(str(body.get("text", "")).replace("\\n", "\n"))
            except ValueError as error:
                self.reply(400, {"error": str(error)})
                return
        else:
            self.reply(404, {"error": "Not found"})
            return

        if not show(board):
            self.reply(409, {"error": "That message is already on the board."})
            return
        self.reply(200, {"status": "ok", "characters": board})

    def log_message(self, format, *args):
        pass


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Virtual Vestaboard</title>
<style>
  :root {
    --page: #e9e6e1; --frame: #111; --tile: #1b1b1b; --ink: #f3f1ec;
    --muted: #6b6760; --error: #b3261e;
    --red: #d7372f; --orange: #f08a24; --yellow: #f4c534; --green: #2f9e57;
    --blue: #2a6fdb; --violet: #7c4dbd; --white: #f3f1ec; --black: #000;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 100vh; background: var(--page); color: #222;
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 28px; padding: 24px 16px;
  }
  .board {
    background: var(--frame); padding: clamp(10px, 2.5vw, 26px);
    border-radius: 6px; box-shadow: 0 20px 50px rgba(0,0,0,.35);
    display: grid; grid-template-columns: repeat(COLS_COUNT, 1fr);
    gap: clamp(2px, .5vw, 5px); width: min(100%, 900px);
  }
  .tile {
    aspect-ratio: 1 / 1.25; background: var(--tile); border-radius: 3px;
    display: flex; align-items: center; justify-content: center; position: relative;
    color: var(--ink); font-weight: 600; font-size: clamp(12px, 3.6vw, 38px);
    font-family: "Helvetica Neue", Arial, sans-serif;
  }
  .tile::after {  /* the split across the middle of a flap */
    content: ""; position: absolute; left: 0; right: 0; top: 50%;
    height: 1px; background: rgba(0,0,0,.6);
  }
  .tile.flip { animation: flip .12s linear; }
  @keyframes flip { 50% { transform: scaleY(.1); } }
  form { display: flex; gap: 8px; width: min(100%, 900px); flex-wrap: wrap; }
  textarea {
    flex: 1 1 300px; font: inherit; font-size: 16px; padding: 10px 12px;
    border: 1px solid #bbb; border-radius: 6px; resize: vertical; min-height: 66px;
  }
  button {
    font: inherit; font-size: 16px; padding: 10px 20px; border: 0; border-radius: 6px;
    background: #222; color: #fff; cursor: pointer;
  }
  .help { width: min(100%, 900px); color: var(--muted); font-size: 14px; margin: -16px 0 0; }
  .status { min-height: 1.2em; }
  .status.error { color: var(--error); }
</style>
</head>
<body>
  <div class="board" id="board"></div>
  <form id="form">
    <textarea id="text" placeholder="Type a message. Press Enter to send, Shift+Enter for a new line. Colours: {red} {green} ..."></textarea>
    <button>Send</button>
  </form>
  <p class="help"><span class="status" id="status">Scripts can send here with VESTABOARD_VIRTUAL=1 in front.</span></p>
<script>
const ROWS = ROWS_COUNT, COLS = COLS_COUNT;
const CHARS = CHAR_MAP;
const COLORS = COLOR_MAP;
const FLAP_ORDER = " ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$()-+&=;:'\\"%,./?°";

const boardEl = document.getElementById("board");
const tiles = [];
for (let i = 0; i < ROWS * COLS; i++) {
  const t = document.createElement("div");
  t.className = "tile";
  boardEl.appendChild(t);
  tiles.push({ el: t, code: 0, timer: null });
}

function paint(tile, code) {
  const color = COLORS[code];
  tile.el.style.background = color ? `var(--${color})` : "";
  tile.el.textContent = color ? "" : (CHARS[code] ?? "");
}

// Flip a tile through a few flaps before landing, like the real board.
function flipTo(tile, code, delay) {
  if (tile.code === code) return;
  tile.code = code;
  clearTimeout(tile.timer);
  let steps = 4 + Math.floor(Math.random() * 6);
  const step = () => {
    tile.el.classList.remove("flip");
    void tile.el.offsetWidth;
    tile.el.classList.add("flip");
    if (steps-- > 0) {
      const ch = FLAP_ORDER[Math.floor(Math.random() * FLAP_ORDER.length)];
      tile.el.style.background = "";
      tile.el.textContent = ch;
      tile.timer = setTimeout(step, 70);
    } else {
      paint(tile, code);
    }
  };
  tile.timer = setTimeout(step, delay);
}

let version = 0;
async function refresh() {
  try {
    const res = await fetch("/board");
    const data = await res.json();
    if (data.version !== version) {
      const first = version === 0;
      version = data.version;
      data.board.flat().forEach((code, i) => {
        if (first) { tiles[i].code = code; paint(tiles[i], code); }
        else flipTo(tiles[i], code, (i % COLS) * 25);
      });
    }
  } catch (e) { /* the server is restarting; try again shortly */ }
}
refresh();
setInterval(refresh, 1000);

const form = document.getElementById("form");
const text = document.getElementById("text");
const status = document.getElementById("status");
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const res = await fetch("/message", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: text.value }),
  });
  const data = await res.json();
  status.className = "status" + (res.ok ? "" : " error");
  status.textContent = res.ok ? `${text.value.length} characters, fits on the board.` : data.error;
  refresh();
});
text.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
});
</script>
</body>
</html>
"""

PAGE = (PAGE_TEMPLATE
        .replace("ROWS_COUNT", str(ROWS))
        .replace("COLS_COUNT", str(COLS))
        .replace("CHAR_MAP", json.dumps(CODE_TO_CHAR, ensure_ascii=False))
        .replace("COLOR_MAP", json.dumps({code: name for name, code in COLOR_CODES.items()})))


def main():
    parser = argparse.ArgumentParser(description="Run a pretend Vestaboard Note in your browser.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to use (default {DEFAULT_PORT})")
    args = parser.parse_args()

    server = ThreadingHTTPServer(("localhost", args.port), Handler)
    print(f"Virtual Vestaboard running at http://localhost:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
