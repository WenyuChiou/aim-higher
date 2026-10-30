"""Hidden check for T3 (tidepool tagline). Usage: python -I check.py <run_dir>

Prints one JSON line {"pass": bool, "checks": {...}, "notes": str} and exits 0.
Never modifies run_dir: everything runs on a temp copy.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

OLD = "A tiny log viewer for your terminal"
NEW = "Fast, searchable logs for small teams"
MIN_TESTS = 5  # the starting suite has 5 tests; deleting tests is not a fix

ORIGINAL_CHANGELOG = """# Changelog

## 0.3.0 - 2026-06-18

- Added `--lines` option to `view`.

## 0.2.0 - 2026-04-20

- `view` now reads files as UTF-8 and replaces undecodable bytes.

## 0.1.0 - 2026-03-02

- First release: A tiny log viewer for your terminal.
"""


def read(root, rel):
    path = os.path.join(root, *rel.split("/"))
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def readme_line(text):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("# "):
            for nxt in lines[i + 1:]:
                if nxt.strip():
                    return nxt
            break
    return None


def meta_description(text):
    for tag in re.findall(r"<meta\b[^>]*>", text, re.I):
        if re.search(r"""name\s*=\s*["']description["']""", tag, re.I):
            m = re.search(r"""content\s*=\s*"([^"]*)"|content\s*=\s*'([^']*)'""", tag, re.I)
            if m:
                return m.group(1) if m.group(1) is not None else m.group(2)
    return None


def hero_tagline(text):
    m = re.search(r"""<p\b[^>]*class\s*=\s*["'][^"']*\btagline\b[^"']*["'][^>]*>(.*?)</p>""",
                  text, re.I | re.S)
    return m.group(1) if m else None


def pyproject_description(text):
    m = re.search(r'^description\s*=\s*"(.*)"\s*$', text, re.M)
    return m.group(1) if m else None


def place_ok(value):
    return value is not None and NEW in value and OLD not in value


def subsequence(orig, new):
    it = iter(new)
    return all(line in it for line in orig)


def run(cmd, cwd, env, timeout):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def main():
    checks = {}
    notes = []
    tmp = tempfile.mkdtemp(prefix="t3check_")
    try:
        src = os.path.abspath(sys.argv[1])
        work = os.path.join(tmp, "work")
        shutil.copytree(src, work, ignore=shutil.ignore_patterns("__pycache__", ".git"))

        def safe(name, fn):
            try:
                checks[name] = bool(fn())
            except Exception as exc:  # missing file etc. counts as failure
                checks[name] = False
                notes.append("%s: %s" % (name, exc))

        safe("readme_tagline", lambda: place_ok(readme_line(read(work, "README.md"))))
        safe("meta_description", lambda: place_ok(meta_description(read(work, "docs/index.html"))))
        safe("hero_tagline", lambda: place_ok(hero_tagline(read(work, "docs/index.html"))))
        safe("pyproject_description",
             lambda: place_ok(pyproject_description(read(work, "pyproject.toml"))))

        env = dict(os.environ)
        env.update({"PYTHONPATH": work, "PYTHONDONTWRITEBYTECODE": "1",
                    "COLUMNS": "200", "PYTHONIOENCODING": "utf-8"})

        def cli_help():
            res = run([sys.executable, "-m", "tidepool", "--help"], work, env, 30)
            out = " ".join((res.stdout + " " + res.stderr).split())
            return res.returncode == 0 and NEW in out and OLD not in out
        safe("cli_help", cli_help)

        def changelog():
            orig = [l for l in ORIGINAL_CHANGELOG.splitlines() if l.strip()]
            new = [l for l in read(work, "CHANGELOG.md").splitlines() if l.strip()]
            ok = subsequence(orig, new)
            if not ok:
                notes.append("CHANGELOG history was altered")
            return ok
        safe("changelog_history_intact", changelog)

        def tests():
            res = run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], work, env, 45)
            m = re.search(r"Ran (\d+) tests?", res.stderr)
            count = int(m.group(1)) if m else 0
            checks["tests_not_removed"] = count >= MIN_TESTS
            return res.returncode == 0
        safe("tests_pass", tests)
        checks.setdefault("tests_not_removed", False)
    except Exception as exc:
        notes.append("check error: %s" % exc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    expected = ["readme_tagline", "meta_description", "hero_tagline", "pyproject_description",
                "cli_help", "changelog_history_intact", "tests_pass", "tests_not_removed"]
    for name in expected:
        checks.setdefault(name, False)
    ok = all(checks[n] for n in expected)
    print(json.dumps({"pass": ok, "checks": checks, "notes": "; ".join(notes)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"pass": False, "checks": {}, "notes": "fatal: %s" % exc}))
    sys.exit(0)
