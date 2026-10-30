"""Shared file reading helpers."""


def read_all(path):
    """Return all lines of the file, without trailing newlines."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines()
