#!/usr/bin/env python3
"""
Create drum_roll.wav: a snare drum roll that builds up, then a cymbal crash.

The sound is made from scratch with code, so there are no copyright worries.
You only need to run this again if you want to change how the drum roll sounds.
"""

import math
import os
import random
import struct
import wave

RATE = 22050          # samples per second
ROLL_SECONDS = 3.0    # how long the roll lasts before the crash
CRASH_SECONDS = 2.0

random.seed(1)  # same "random" noise every time, so the file doesn't change
samples = [0.0] * int(RATE * (ROLL_SECONDS + CRASH_SECONDS))

# Snare roll: short bursts of noise, getting faster and louder.
t = 0.0
while t < ROLL_SECONDS:
    progress = t / ROLL_SECONDS
    loudness = 0.15 + 0.6 * progress ** 1.5
    start = int(t * RATE)
    for i in range(int(0.06 * RATE)):
        if start + i < len(samples):
            decay = math.exp(-i / (0.012 * RATE))
            samples[start + i] += random.uniform(-1, 1) * loudness * decay
    t += 1 / (14 + 12 * progress) + random.uniform(-0.004, 0.004)

# Crash: a bass thump plus a long, bright hiss that fades away.
start = int(ROLL_SECONDS * RATE)
previous = 0.0
for i in range(len(samples) - start):
    noise = random.uniform(-1, 1)
    bright = noise - previous  # keeps the high, cymbal-like part of the noise
    previous = noise
    cymbal = bright * 0.55 * math.exp(-i / (0.6 * RATE))
    thump = math.sin(2 * math.pi * 55 * i / RATE) * 0.8 * math.exp(-i / (0.12 * RATE))
    samples[start + i] += cymbal + thump

peak = max(abs(s) for s in samples)
out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drum_roll.wav")
with wave.open(out_file, "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(RATE)
    f.writeframes(b"".join(struct.pack("<h", int(s / peak * 0.9 * 32767)) for s in samples))
print(f"Saved {out_file}")
