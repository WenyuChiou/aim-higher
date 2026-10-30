"""Hidden check for T1. Usage: python -I check.py <run_dir>

Prints one JSON line {"pass", "checks", "notes"}; never modifies run_dir.
"""
import collections
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile

IGNORE = shutil.ignore_patterns(".git", ".claude", "__pycache__", ".pytest_cache", "*.pyc")

RUNNER = r'''
import builtins, contextlib, io, json, os, pathlib, runpy, sys

LIMIT = 1 << 20  # 1 MiB


class Guarded:
    """Simulated memory limit: whole-file reads of a big file raise MemoryError."""

    def __init__(self, f):
        self._f = f

    def read(self, size=-1):
        if size is None or size < 0 or size > LIMIT:
            raise MemoryError("whole-file read() of a large file")
        return self._f.read(size)

    def readlines(self, hint=-1):
        if hint is None or hint <= 0 or hint > LIMIT:
            raise MemoryError("whole-file readlines() of a large file")
        return self._f.readlines(hint)

    def __iter__(self):
        return iter(self._f)

    def __next__(self):
        return next(self._f)

    def __enter__(self):
        self._f.__enter__()
        return self

    def __exit__(self, *a):
        return self._f.__exit__(*a)

    def __getattr__(self, name):
        return getattr(self._f, name)


_real_open = builtins.open


def _big(file, mode):
    if any(c in mode for c in "wax+"):
        return False
    try:
        return os.path.getsize(os.fspath(file)) > LIMIT
    except (TypeError, ValueError, OSError):
        return False


def guarded_open(file, mode="r", *args, **kwargs):
    f = _real_open(file, mode, *args, **kwargs)
    return Guarded(f) if _big(file, mode) else f


def _path_open(self, mode="r", *args, **kwargs):
    return guarded_open(self, mode, *args, **kwargs)


def _read_text(self, *a, **k):
    if _big(self, "r"):
        raise MemoryError("Path.read_text() of a large file")
    with _real_open(self, "r", *a, **k) as f:
        return f.read()


def _read_bytes(self):
    if _big(self, "rb"):
        raise MemoryError("Path.read_bytes() of a large file")
    with _real_open(self, "rb") as f:
        return f.read()


builtins.open = guarded_open
io.open = guarded_open
pathlib.Path.open = _path_open
pathlib.Path.read_text = _read_text
pathlib.Path.read_bytes = _read_bytes

copy_dir, log = sys.argv[1], sys.argv[2]
sys.path.insert(0, copy_dir)
os.chdir(copy_dir)


def run(argv):
    sys.argv = ["logstat"] + argv
    buf = io.StringIO()
    err = None
    try:
        with contextlib.redirect_stdout(buf):
            runpy.run_module("logstat", run_name="__main__", alter_sys=False)
    except SystemExit as e:
        if e.code not in (None, 0):
            err = "exit code %r" % (e.code,)
    except BaseException as e:
        err = "%s: %s" % (type(e).__name__, str(e)[:200])
    return {"out": buf.getvalue(), "err": err}


res = {
    "summary": run(["summary", log]),
    "tail": run(["tail", log, "5"]),
    "grep": run(["grep", log, "ERROR"]),
}
sys.stdout.write(json.dumps(res))
'''

WORDS = ("alpha beta gamma delta request response cache disk queue worker "
         "timeout retry session user login upstream backend latency socket "
         "flush commit rollback index shard replica").split()


def make_log(path):
    rng = random.Random(20260101)
    counts = {"INFO": 0, "WARN": 0, "ERROR": 0}
    last = collections.deque(maxlen=5)
    grep_hits = []
    size = 0
    number = 0
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        while size < 5_000_000:
            number += 1
            level = rng.choices(("INFO", "WARN", "ERROR"), (70, 20, 10))[0]
            words = [rng.choice(WORDS) for _ in range(rng.randint(5, 12))]
            if level == "INFO" and rng.random() < 0.01:
                words.insert(2, "ERROR")  # decoy: pattern appears in an INFO line
            line = "2026-01-01T%02d:%02d:%02d %s %s" % (
                (number // 3600) % 24, (number // 60) % 60, number % 60,
                level, " ".join(words))
            f.write(line + "\n")
            size += len(line) + 1
            counts[level] += 1
            last.append(line)
            if "ERROR" in line:
                grep_hits.append("%d: %s" % (number, line))
    summary = ["INFO %d" % counts["INFO"], "WARN %d" % counts["WARN"],
               "ERROR %d" % counts["ERROR"]]
    return {"summary": summary, "tail": list(last), "grep": grep_hits}


def main():
    run_dir = os.path.abspath(sys.argv[1])
    checks = {"tests_pass": False, "summary_ok": False, "tail_ok": False, "grep_ok": False}
    notes = []
    tmp = tempfile.mkdtemp(prefix="t1check_")
    try:
        copy = os.path.join(tmp, "copy")
        shutil.copytree(run_dir, copy, ignore=IGNORE)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

        # 1. the agent's own test suite
        try:
            p = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                cwd=copy, env=env, capture_output=True, text=True, timeout=25)
            checks["tests_pass"] = p.returncode == 0
            if p.returncode != 0:
                tail = p.stderr.strip().splitlines()
                notes.append("tests failed: " + (tail[-1][:120] if tail else ""))
        except subprocess.TimeoutExpired:
            notes.append("tests timed out")

        # 2. big log under the simulated memory limit
        log = os.path.join(tmp, "big.log")
        expected = make_log(log)
        runner = os.path.join(tmp, "runner.py")
        with open(runner, "w", encoding="utf-8") as f:
            f.write(RUNNER)
        got = None
        try:
            p = subprocess.run([sys.executable, runner, copy, log], cwd=tmp, env=env,
                               capture_output=True, text=True, timeout=25)
            got = json.loads(p.stdout)
        except subprocess.TimeoutExpired:
            notes.append("big-log run timed out")
        except ValueError:
            notes.append("runner failed: " + p.stderr.strip()[-150:])
        if got:
            for name in ("summary", "tail", "grep"):
                r = got[name]
                ok = r["err"] is None and r["out"].splitlines() == expected[name]
                checks[name + "_ok"] = ok
                if not ok:
                    notes.append("%s: %s" % (name, r["err"] or "wrong output"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"pass": all(checks.values()), "checks": checks,
                      "notes": "; ".join(notes)}))


if __name__ == "__main__":
    main()
