import re


def is_blocked(command: str) -> bool:
    """Return True if this shell command line must not run."""
    if "git" in command and "push" in command:
        if "force" in command or re.search(r"\s-\w*f", command):
            return True
    return False
