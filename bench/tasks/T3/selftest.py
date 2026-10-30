"""Self-test for T3: untouched must fail, reference must pass, trap must fail."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def build(tmp, name, overlay):
    dest = os.path.join(tmp, name)
    shutil.copytree(os.path.join(HERE, "repo"), dest, ignore=shutil.ignore_patterns("__pycache__"))
    if overlay:
        shutil.copytree(os.path.join(HERE, overlay), dest, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def check(path):
    res = subprocess.run([sys.executable, "-I", os.path.join(HERE, "check.py"), path],
                         capture_output=True, text=True, timeout=90)
    assert res.returncode == 0, res.stderr
    lines = [l for l in res.stdout.splitlines() if l.strip()]
    assert len(lines) == 1, res.stdout
    return json.loads(lines[0])


def main():
    tmp = tempfile.mkdtemp(prefix="t3self_")
    try:
        results = {}
        for name, overlay in (("untouched", None), ("reference", "reference"), ("trap", "trap")):
            results[name] = check(build(tmp, name, overlay))
        assert not results["untouched"]["pass"], results["untouched"]
        assert results["reference"]["pass"], results["reference"]
        assert not results["trap"]["pass"], results["trap"]
        failed = [k for k, v in results["trap"]["checks"].items() if not v]
        print("T3 selftest OK: untouched=fail reference=pass trap=fail (trap fails: %s)"
              % ", ".join(failed))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
