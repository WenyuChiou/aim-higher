"""Shared file reading helpers."""


def read_all(path):
    """Yield the lines of the file one at a time, without trailing newlines."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\r\n")
