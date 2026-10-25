#!/usr/bin/env python3
"""
Create thinking_jingle.wav: a tick-tock clock under a playful marimba tune that
ends on a rising, questioning note. Played when the noon riddle goes up.

The sound is made from scratch with code, so there are no copyright worries.
You only need to run this again if you want to change how the jingle sounds.
"""

import math
import os
import struct
import wave

RATE = 22050   # samples per second
BEAT = 0.3     # seconds per beat

# The tune, as (note, beats). None is a rest. It wanders, then ends on a question.
TUNE = [
    ("E5", 1), ("G5", 1), ("A5", 1), ("G5", 1),
    ("E5", 1), ("D5", 1), ("E5", 2),
    ("A5", 1), ("C6", 1), ("D6", 1), ("C6", 1),
    ("A5", 1), ("G5", 1), (None, 1), ("G5", 0.5), ("A5", 0.5),
    ("D6", 3),
]
NOTE_NUMBERS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def frequency(note):
    """Turn a note name like 'A5' into its pitch in Hz."""
    number = NOTE_NUMBERS[note[0]] + 12 * (int(note[1]) + 1)
    return 440 * 2 ** ((number - 69) / 12)


total_beats = sum(beats for _, beats in TUNE)
samples = [0.0] * int(RATE * (total_beats * BEAT + 0.8))

# Tick-tock: short wooden clicks, alternating high and low, twice per beat.
for k in range(int(total_beats * 2)):
    start = int(k * BEAT / 2 * RATE)
    pitch = 1800 if k % 2 == 0 else 1300
    for i in range(int(0.03 * RATE)):
        samples[start + i] += math.sin(2 * math.pi * pitch * i / RATE) * 0.25 * math.exp(-i / (0.004 * RATE))

# Marimba-like tune: a soft tone that fades quickly, with a hint of a higher overtone.
t = 0.0
for note, beats in TUNE:
    if note:
        f = frequency(note)
        start = int(t * RATE)
        ring = min(beats * BEAT + 0.4, 1.5)
        for i in range(int(ring * RATE)):
            x = i / RATE
            tone = math.sin(2 * math.pi * f * x) + 0.25 * math.sin(2 * math.pi * 4 * f * x) * math.exp(-x / 0.03)
            samples[start + i] += tone * 0.5 * math.exp(-x / (0.35 if beats < 3 else 0.6))
    t += beats * BEAT

peak = max(abs(s) for s in samples)
out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thinking_jingle.wav")
with wave.open(out_file, "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(RATE)
    f.writeframes(b"".join(struct.pack("<h", int(s / peak * 0.9 * 32767)) for s in samples))
print(f"Saved {out_file}")
