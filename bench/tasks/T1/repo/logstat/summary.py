"""The `summary` command: count lines per level."""

from .reader import read_all

LEVELS = ("INFO", "WARN", "ERROR")


def summarize(path):
    counts = {level: 0 for level in LEVELS}
    for line in read_all(path):
        parts = line.split(None, 2)
        if len(parts) >= 2 and parts[1] in counts:
            counts[parts[1]] += 1
    return counts
