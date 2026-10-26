#!/usr/bin/env python3
"""
Create evil_laugh.wav: a deep Halloween "Mwa-ha-ha-ha-haaa!" with a spooky echo.

The voice is made from scratch with code (a buzzing "voice box" shaped into vowel
sounds), so there are no recordings and no copyright worries. You only need to run
this again if you want to change how the laugh sounds.
"""

import math
import os
import random
import struct
import wave

RATE = 22050  # samples per second

random.seed(13)  # same "random" breath every time, so the file doesn't change

# Vowel shapes: the three main resonances of the mouth (Hz) for each sound.
VOWELS = {
    "m": (250, 1000, 2200),   # lips closed: a muffled hum
    "w": (320, 800, 2200),    # "oo"
    "a": (750, 1150, 2500),   # "ah"
}

# The laugh, one piece at a time: (sound, seconds, start pitch, end pitch, loudness).
# Pitch is in Hz; around 100 is a deep voice. "h" is breath with no voice.
PIECES = [("m", 0.18, 85, 95, 0.35), ("w", 0.08, 95, 120, 0.8), ("a", 0.38, 120, 105, 1.0),
          ("h", 0.10, 0, 0, 0.25)]
for n, pitch in enumerate([150, 145, 138, 130, 122]):
    PIECES += [("a", 0.15, pitch, pitch - 6, 0.95 - n * 0.04), ("h", 0.07, 0, 0, 0.3)]
PIECES += [("h", 0.12, 0, 0, 0.35), ("a", 1.3, 135, 75, 1.0)]


def resonator(freq, width):
    """A filter that rings at one frequency, like one resonance of the mouth."""
    c = -math.exp(-2 * math.pi * width / RATE)
    b = 2 * math.exp(-math.pi * width / RATE) * math.cos(2 * math.pi * freq / RATE)
    return 1 - b - c, b, c


def speak():
    samples = []
    shape = VOWELS["m"]
    filters = [[0.0, 0.0] for _ in range(3)]
    phase = 0.0
    for sound, seconds, start_pitch, end_pitch, loudness in PIECES:
        count = int(seconds * RATE)
        target = VOWELS.get(sound, shape)  # breath keeps the mouth shape it had
        for i in range(count):
            progress = i / count
            # Glide the mouth shape smoothly towards the new vowel.
            shape = tuple(s + (t - s) * 0.004 for s, t in zip(shape, target))

            if sound == "h":
                source = random.uniform(-1, 1) * 0.5
            else:
                pitch = start_pitch + (end_pitch - start_pitch) * progress
                pitch *= 1 + 0.03 * math.sin(2 * math.pi * 5.5 * i / RATE)  # slight wobble
                phase = (phase + pitch / RATE) % 1.0
                buzz = 1 - 2 * phase  # a buzzy sawtooth, like vocal cords
                source = buzz + random.uniform(-1, 1) * 0.08
                if sound == "m":
                    source *= 0.6

            # Fade each piece in and out so the syllables are separate.
            fade = min(1.0, i / (0.02 * RATE), (count - i) / (0.03 * RATE))
            value = source * loudness * fade

            # Shape the buzz into a vowel with three resonances in a row.
            for (a, b, c), state in zip([resonator(f, w) for f, w in zip(shape, (90, 110, 160))],
                                        filters):
                y = a * value + b * state[0] + c * state[1]
                state[1], state[0] = state[0], y
                value = y
            samples.append(value)
    return samples


samples = speak()

# A spooky castle echo: quieter copies of the laugh, arriving later.
samples += [0.0] * int(1.5 * RATE)
for delay, level in [(0.13, 0.45), (0.29, 0.3), (0.47, 0.2), (0.71, 0.12)]:
    offset = int(delay * RATE)
    for i in range(len(samples) - 1, offset - 1, -1):
        samples[i] += samples[i - offset] * level

peak = max(abs(s) for s in samples)
out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evil_laugh.wav")
with wave.open(out_file, "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(RATE)
    f.writeframes(b"".join(struct.pack("<h", int(s / peak * 0.9 * 32767)) for s in samples))
print(f"Saved {out_file}")
