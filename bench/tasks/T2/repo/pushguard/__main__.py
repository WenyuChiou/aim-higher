import sys

from .guard import is_blocked


def main(argv):
    command = argv[1] if len(argv) == 2 else " ".join(argv[1:])
    if is_blocked(command):
        print("blocked")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
