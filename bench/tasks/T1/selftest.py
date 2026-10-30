"""Builds repo / repo+reference / repo+trap temp copies and checks the verdicts."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
IGN = shutil.ignore_patterns("__pycache__", "*.pyc")


def snapshot(d):
    out = {}
    for root, _, files in os.walk(d):
        for n in files:
            p = os.path.join(root, n)
            with open(p, "rb") as f:
                out[os.path.relpath(p, d)] = f.read()
    return out


def run_check(d):
    before = snapshot(d)
    p = subprocess.run([sys.executable, "-I", os.path.join(HERE, "check.py"), d],
                       capture_output=True, text=True, timeout=90)
    assert p.returncode == 0, p.stderr
    assert snapshot(d) == before, "check.py modified run_dir"
    return json.loads(p.stdout.strip().splitlines()[-1])


def main():
    tmp = tempfile.mkdtemp(prefix="t1self_")
    try:
        dirs = {}
        for name, overlay in (("untouched", None), ("reference", "reference"), ("trap", "trap")):
            d = os.path.join(tmp, name)
            shutil.copytree(os.path.join(HERE, "repo"), d, ignore=IGN)
            if overlay:
                shutil.copytree(os.path.join(HERE, overlay), d, ignore=IGN, dirs_exist_ok=True)
            dirs[name] = d
        res = {k: run_check(d) for k, d in dirs.items()}
        assert not res["untouched"]["pass"], res["untouched"]
        assert res["reference"]["pass"], res["reference"]
        assert not res["trap"]["pass"], res["trap"]
        print("T1 selftest OK: untouched=fail reference=pass trap=fail (trap failed: %s)"
              % ",".join(k for k, v in res["trap"]["checks"].items() if not v))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
