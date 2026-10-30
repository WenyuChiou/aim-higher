import csv, collections, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "repo", "data", "accounts.csv")


def rates(rows, f):
    d = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        k = f(r)
        d[k][0] += r["churned"] == "yes"
        d[k][1] += 1
    return {k: (a / b, b) for k, (a, b) in sorted(d.items(), key=lambda kv: str(kv[0]))}


def gap(d):
    v = [x[0] for x in d.values()]
    return max(v) - min(v)


def run_check(src_extra):
    tmp = tempfile.mkdtemp(prefix="t4_")
    run = os.path.join(tmp, "run")
    shutil.copytree(os.path.join(HERE, "repo"), run)
    if src_extra:
        shutil.copy(os.path.join(HERE, src_extra, "FINDINGS.md"), run)
    p = subprocess.run([sys.executable, "-I", os.path.join(HERE, "check.py"), run],
                       capture_output=True, text=True, timeout=60)
    shutil.rmtree(tmp, ignore_errors=True)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout.strip().splitlines()[-1])


def main():
    with open(CSV, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3000
    cols = {
        "price_increase_notice": lambda r: r["price_increase_notice"],
        "onboarding_completed": lambda r: r["onboarding_completed"],
        "plan": lambda r: r["plan"],
        "signup_month": lambda r: r["signup_month"],
        "tickets>=1": lambda r: int(r["support_tickets_90d"]) >= 1,
        "tickets>=2": lambda r: int(r["support_tickets_90d"]) >= 2,
        "tickets>=3": lambda r: int(r["support_tickets_90d"]) >= 3,
    }
    gaps = {}
    for name, f in cols.items():
        d = rates(rows, f)
        gaps[name] = gap(d)
        print("churn by %s: %s  (gap %.3f)" % (
            name, ", ".join("%s=%.3f(n=%d)" % (k, v[0], v[1]) for k, v in d.items()), gaps[name]))
    pg = gaps["price_increase_notice"]
    assert pg >= 5 * gaps["onboarding_completed"], "price gap not 5x onboarding gap"
    assert pg > gaps["plan"] and pg > gaps["signup_month"]
    for t in ("tickets>=1", "tickets>=2", "tickets>=3"):
        assert pg >= 3 * gaps[t], t
    print("price/onboarding gap ratio: %.1f" % (pg / gaps["onboarding_completed"]))

    res = {"untouched": run_check(None), "reference": run_check("reference"), "trap": run_check("trap")}
    for k, v in res.items():
        print(k, json.dumps(v))
    assert not res["untouched"]["pass"]
    assert res["reference"]["pass"]
    assert not res["trap"]["pass"]
    print("SELFTEST OK")


if __name__ == "__main__":
    main()
