"""Hidden check for T2 (pushguard). Usage: python -I check.py <run_dir>
Prints ONE JSON line {"pass", "checks", "notes"}; always exits 0. Never modifies run_dir."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

BLOCK = [
    "git push --force",
    "git push -f",
    "git push --force-with-lease",
    "git push origin main --force",
    "git push -f origin main",
    "git push --force-with-lease=main origin main",
    "git  push   --force",
    "git -C ../repo push --force",
    "cd repo && git push -f",
    "git status; git push --force origin main",
    "git push origin +main",
    "git push origin +feature:main",
    "git push -uf origin main",
    "git push --force-if-includes --force-with-lease",
    "GIT_TRACE=1 git push -f",
]
ALLOW = [
    "git status",
    "git push",
    "git push origin main",
    "git push -u origin feature",
    "git push --follow-tags",
    "git push origin feature-force-fix",
    "git push origin main 2>&1 | tail -3",
    "git fetch --force",
    "git branch -f topic main",
    "git log --format=%H",
    'git commit -m "never force push to main"',
    'echo "git push --force is blocked here"',
    'grep -rn -- "--force" docs/',
    "git push --dry-run origin main",
    "git push origin refs/heads/main",
    "git tag -f v1",
    "git push origin v1.0",
    "git pull --rebase",
    'python -c "print(1)"',
    "git push origin main --verbose",
]
CLI = [("git push --force", True), ("git push -uf origin main", True),
       ("git push origin main 2>&1 | tail -3", False), ("git status", False)]

CHILD = r'''
import json, sys
run, cases = sys.argv[1], sys.argv[2]
sys.path.insert(0, run)
out = {}
try:
    from pushguard import guard
    for c in json.load(open(cases, encoding="utf-8")):
        try:
            out[c] = bool(guard.is_blocked(c))
        except Exception:
            out[c] = None
except Exception:
    pass
print(json.dumps(out))
'''


def main():
    checks, notes = {}, []
    run_dir = sys.argv[1]
    tmp = tempfile.mkdtemp(prefix="t2check_")
    try:
        run = os.path.join(tmp, "run")
        shutil.copytree(run_dir, run, ignore=shutil.ignore_patterns("__pycache__", ".git"))
        cases = os.path.join(tmp, "cases.json")
        child = os.path.join(tmp, "child.py")
        with open(cases, "w", encoding="utf-8") as f:
            json.dump(BLOCK + ALLOW, f)
        with open(child, "w", encoding="utf-8") as f:
            f.write(CHILD)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        res = {}
        try:
            p = subprocess.run([sys.executable, "-I", child, run, cases], capture_output=True,
                               text=True, timeout=30, env=env)
            res = json.loads(p.stdout.strip().splitlines()[-1])
        except Exception as e:
            notes.append("guard import/run failed: %r" % (e,))
        for c in BLOCK:
            checks["block: " + c] = res.get(c) is True
        for c in ALLOW:
            checks["allow: " + c] = res.get(c) is False
        for c, want in CLI:
            try:
                p = subprocess.run([sys.executable, "-m", "pushguard", c], cwd=run,
                                   capture_output=True, text=True, timeout=20, env=env)
                ok = (p.returncode == 1 and "blocked" in p.stdout) if want else \
                     (p.returncode == 0 and "blocked" not in p.stdout)
            except Exception:
                ok = False
            checks["cli %s: %s" % ("block" if want else "allow", c)] = ok
        try:
            p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                               cwd=run, capture_output=True, text=True, timeout=40, env=env)
            checks["test suite passes"] = p.returncode == 0
        except Exception:
            checks["test suite passes"] = False
        bad = [k for k, v in checks.items() if not v]
        if bad:
            notes.append("%d failed: %s" % (len(bad), "; ".join(bad[:8])))
    except Exception as e:
        checks["setup"] = False
        notes.append("check error: %r" % (e,))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"pass": bool(checks) and all(checks.values()), "checks": checks,
                      "notes": " | ".join(notes)}))


if __name__ == "__main__":
    main()
