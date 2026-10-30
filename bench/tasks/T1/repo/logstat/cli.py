"""Command line interface."""

import argparse

from .grep import grep_lines
from .summary import summarize
from .tail import tail_lines


def build_parser():
    parser = argparse.ArgumentParser(
        prog="logstat", description="Small log file statistics tool."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("summary", help="count lines per level")
    p.add_argument("file")

    p = sub.add_parser("tail", help="print the last N lnes")
    p.add_argument("file")
    p.add_argument("n", type=int)

    p = sub.add_parser("grep", help="print matching lines with line numbers")
    p.add_argument("file")
    p.add_argument("pattern")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "summary":
        for level, count in summarize(args.file).items():
            print("%s %d" % (level, count))
    elif args.command == "tail":
        for line in tail_lines(args.file, args.n):
            print(line)
    elif args.command == "grep":
        for number, line in grep_lines(args.file, args.pattern):
            print("%d: %s" % (number, line))
    return 0
