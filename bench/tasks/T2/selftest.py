"""Builds untouched / +reference / +trap copies, runs check.py on each, asserts fail/pass/fail."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def run(overlay):
    tmp = tempfile.mkdtemp(prefix="t2self_")
    try:
        d = os.path.join(tmp, "run")
        shutil.copytree(os.path.join(HERE, "repo"), d, ignore=shutil.ignore_patterns("__pycache__"))
        if overlay:
            shutil.copytree(os.path.join(HERE, overlay), d, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__"))
        p = subprocess.run([sys.executable, "-I", os.path.join(HERE, "check.py"), d],
                           capture_output=True, text=True, timeout=120)
        return json.loads(p.stdout.strip().splitlines()[-1])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    u, r, t = run(None), run("reference"), run("trap")
    n = lambda x: "%d/%d" % (sum(x["checks"].values()), len(x["checks"]))
    assert not u["pass"], "untouched should fail"
    assert r["pass"], "reference should pass: %s" % r["notes"]
    assert not t["pass"], "trap should fail"
    print("selftest OK: untouched=fail(%s) reference=pass(%s) trap=fail(%s)" % (n(u), n(r), n(t)))


if __name__ == "__main__":
    main()
