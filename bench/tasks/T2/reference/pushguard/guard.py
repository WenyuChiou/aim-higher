import re
import shlex

_OPERATORS = {";", ";;", "&&", "||", "|", "|&", "&", "(", ")"}
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# git global options that consume the next argument when written separately
_GLOBAL_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace",
                    "--exec-path", "--super-prefix", "--config-env"}


def _segments(command):
    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lex.whitespace_split = True
    lex.whitespace = " \t\r"
    lex.commenters = ""
    seg = []
    for tok in lex:
        if tok in _OPERATORS or tok == "\n":
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def _push_args(seg):
    """Return the arguments after `git push`, or None if seg is not a push."""
    i = 0
    while i < len(seg) and _ASSIGN.match(seg[i]):
        i += 1
    if i >= len(seg) or seg[i].replace("\\", "/").rsplit("/", 1)[-1] not in ("git", "git.exe"):
        return None
    i += 1
    while i < len(seg) and seg[i].startswith("-"):
        i += 2 if seg[i] in _GLOBAL_WITH_ARG else 1
    if i < len(seg) and seg[i] == "push":
        return seg[i + 1:]
    return None


def _forces(args):
    for a in args:
        if a == "--":
            continue
        if a == "--force" or a == "-f":
            return True
        if a == "--force-with-lease" or a.startswith("--force-with-lease="):
            return True
        if a.startswith("-") and not a.startswith("--") and "f" in a[1:]:
            return True
        if a.startswith("+"):
            return True
    return False


def is_blocked(command: str) -> bool:
    """Return True if this shell command line must not run."""
    try:
        segs = list(_segments(command))
    except ValueError:
        segs = [command.split()]
    for seg in segs:
        args = _push_args(seg)
        if args is not None and _forces(args):
            return True
    return False
