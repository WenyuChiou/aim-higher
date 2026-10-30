"""Command line interface for notecat."""

import argparse
import sys


def load_notes(path):
    notes = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if text and not text.startswith("#"):
                notes.append(text)
    return notes


def main(argv=None):
    parser = argparse.ArgumentParser(prog="notecat")
    parser.add_argument("file")
    parser.add_argument("--number", action="store_true")
    parser.add_argument("--upper", action="store_true")
    args = parser.parse_args(argv)
    try:
        notes = load_notes(args.file)
    except OSError:
        return 2
    for i, note in enumerate(notes, 1):
        if args.upper:
            note = note.upper()
        sys.stdout.write(("%d. %s" % (i, note) if args.number else note) + "\n")
    return 0
