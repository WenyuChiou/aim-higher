"""The `grep` command: matching lines with 1-based line numbers."""

import re


def grep_lines(path, pattern):
    rx = re.compile(pattern)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return [
        (number, line)
        for number, line in enumerate(text.splitlines(), 1)
        if rx.search(line)
    ]
