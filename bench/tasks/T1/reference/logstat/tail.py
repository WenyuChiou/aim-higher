"""The `tail` command: last N lines."""

from collections import deque


def tail_lines(path, n):
    if n <= 0:
        return []
    last = deque(maxlen=n)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            last.append(line.rstrip("\r\n"))
    return list(last)
