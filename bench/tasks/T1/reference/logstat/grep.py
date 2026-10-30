"""The `grep` command: matching lines with 1-based line numbers."""

import re


def grep_lines(path, pattern):
    rx = re.compile(pattern)
    with open(path, "r", encoding="utf-8") as f:
        for number, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if rx.search(line):
                yield (number, line)
