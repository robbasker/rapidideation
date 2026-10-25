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

2. **Get your Read/Write API key.** In the Vestaboard app, go to **Settings → Developer**,
   turn on the **Read/Write API**, and copy the key.

3. **Save the key.** Create a file called `api_key.txt` in this `vestaboard` folder and
   paste the key into it (just the key, nothing else). This file is listed in
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

## Good to know

- The board is **6 lines × 22 characters**. Messages are word-wrapped and centred
  automatically; the script tells you if one is too long.
- Letters are shown in capitals. Supported symbols: `! @ # $ ( ) - + & = ; : ' " % , . / ? °`
- Vestaboard limits how often you can post (roughly once every 15 seconds), and
  sending the exact same message twice in a row is refused.
