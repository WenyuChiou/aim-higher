"""The `tail` command: last N lines."""


def tail_lines(path, n):
    if n <= 0:
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.rstrip("\r\n") for line in lines[-n:]]
