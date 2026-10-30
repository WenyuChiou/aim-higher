import argparse
import sys

from . import __version__


def build_parser():
    parser = argparse.ArgumentParser(
        prog="tidepool",
        description="A tiny log viewer for your terminal",
    )
    parser.add_argument("--version", action="version", version="tidepool " + __version__)
    sub = parser.add_subparsers(dest="command")
    view = sub.add_parser("view", help="print a log file")
    view.add_argument("file", help="path to the log file")
    view.add_argument("--lines", type=int, default=None, help="show only the last N lines")
    return parser


def read_lines(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read().splitlines()


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "view":
        parser.print_help()
        return 1
    lines = read_lines(args.file)
    if args.lines is not None:
        lines = lines[-args.lines:] if args.lines > 0 else []
    for line in lines:
        sys.stdout.write(line + "\n")
    return 0
