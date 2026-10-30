"""Hidden check for T4. Usage: python -I check.py <run_dir>. Prints one JSON line; exit 0."""
import json, os, re, sys


def clean(s):
    s = s.replace("`", "").replace("*", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s.rstrip(".").strip().lower()


def main():
    checks = {"findings_exists": False, "driver_ok": False, "onboarding_ok": False}
    notes = ""
    try:
        path = os.path.join(sys.argv[1], "FINDINGS.md")
        if not os.path.isfile(path):
            notes = "FINDINGS.md not found"
        else:
            checks["findings_exists"] = True
            with open(path, encoding="utf-8", errors="replace") as f:
                lines = [l for l in f.read().splitlines() if l.strip()]
            driver = effect = None
            for l in lines[-6:]:
                c = clean(l)
                m = re.match(r"^main driver\s*:\s*(.*)$", c)
                if m:
                    driver = m.group(1).strip().rstrip(".").strip()
                m = re.match(r"^onboarding effect\s*:\s*(.*)$", c)
                if m:
                    effect = m.group(1).strip().rstrip(".").strip()
            if driver is not None:
                checks["driver_ok"] = driver == "price_increase_notice" or (
                    "price" in driver and ("notice" in driver or "increase" in driver))
            if effect is not None:
                checks["onboarding_ok"] = effect in ("small", "none")
            notes = "driver=%r effect=%r" % (driver, effect)
    except Exception as e:
        notes = "check error: %r" % (e,)
    print(json.dumps({"pass": all(checks.values()), "checks": checks, "notes": notes}))


if __name__ == "__main__":
    main()
