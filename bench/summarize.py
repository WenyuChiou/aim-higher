#!/usr/bin/env python3
"""Summarize a benchmark output folder: tables plus the five decision rules."""

import json
import os
import sys
from fractions import Fraction

ARMS = ["A", "B", "Bp"]
CONTROL = {"C1"}


def load(out):
    rows = []
    with open(os.path.join(out, "scorecard.jsonl"), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
    return rows


def mean(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    return sum(vals) / len(vals) if vals else None


def total(vals):
    return sum(v for v in vals if isinstance(v, (int, float)))


def rate(rows, key):
    return (sum(1 for r in rows if r.get(key)) / len(rows)) if rows else None


def pct(x):
    return "n/a" if x is None else f"{100 * x:.0f}%"


def num(x, fmt="{:.2f}"):
    return "n/a" if x is None else fmt.format(x)


def cpc(rows):
    """Cost per correct result; None when no passes."""
    passes = sum(1 for r in rows if r.get("pass"))
    if passes == 0:
        return None
    return total([r.get("cost_usd") for r in rows]) / passes


def table(header, body):
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for b in body:
        lines.append("| " + " | ".join(str(c) for c in b) + " |")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: summarize.py <out-folder>")
    out = sys.argv[1]
    rows = load(out)
    if not rows:
        sys.exit("scorecard.jsonl is empty or missing")
    tasks = sorted({r["task"] for r in rows})
    arms = [a for a in ARMS if any(r["arm"] == a for r in rows)]
    sel = lambda t=None, a=None, trap=None: [
        r for r in rows
        if (t is None or r["task"] == t) and (a is None or r["arm"] == a)
        and (trap is None or ((r["task"] not in CONTROL) == trap))
    ]

    md = [f"# Benchmark summary: {os.path.basename(os.path.abspath(out))}", "",
          f"{len(rows)} runs. Model: {', '.join(sorted({str(r.get('model')) for r in rows}))}.", ""]
    bad = [r for r in rows if r.get("timed_out") or r.get("is_error") or r.get("exit_code") not in (0, None)]
    if bad:
        md += [f"{len(bad)} run(s) timed out, errored or exited non-zero; they count as FAIL: "
               + ", ".join(sorted(r["run_id"] for r in bad)), ""]

    md += ["## Per task and arm", ""]
    body = []
    for t in tasks:
        for a in arms:
            g = sel(t, a)
            if not g:
                continue
            body.append([t, a, len(g), pct(rate(g, "pass")),
                         num(mean([r.get("tokens") for r in g]), "{:.0f}"),
                         "$" + num(mean([r.get("cost_usd") for r in g]), "{:.3f}"),
                         num(mean([r.get("duration_s") for r in g]), "{:.0f}") + "s",
                         pct(rate(g, "header_written")), pct(rate(g, "skill_used"))])
    md.append(table(["task", "arm", "n", "pass rate", "mean tokens", "mean cost", "mean duration",
                     "header rate", "skill-used rate"], body))

    md += ["", "## Trap tasks pooled (all tasks except C1)", ""]
    body = []
    for a in arms:
        g = sel(a=a, trap=True)
        if not g:
            continue
        passes = sum(1 for r in g if r["pass"])
        c = cpc(g)
        body.append([a, len(g), passes, pct(passes / len(g)), "$" + num(total([r.get("cost_usd") for r in g]), "{:.3f}"),
                     "n/a" if c is None else "$" + f"{c:.3f}", pct(rate(g, "header_written"))])
    md.append(table(["arm", "runs", "passes", "pass rate", "total cost", "cost per correct", "header rate"], body))

    # ---- decision rules
    A, B, Bp = (sel(a=x, trap=True) for x in ("A", "B", "Bp"))
    cA, cB = sel("C1", "A"), sel("C1", "B")
    cBp = sel("C1", "Bp")
    verdicts = []

    def pr(rs):
        return sum(1 for r in rs if r["pass"]) / len(rs) if rs else None

    # rule 5 first (it qualifies 1 and 2)
    tie = False
    tie_txt = "needs trap runs for both A and B"
    if A and B:
        pa, pb = pr(A), pr(B)
        tie = (pa == pb == 1.0) or (pa == pb == 0.0)
        tie_txt = f"A pass {pct(pa)}, B pass {pct(pb)}"
    # rule 1
    if A and B:
        # exact fractions: 8/12 - 5/12 is 25 points, not 24.999...
        gap = Fraction(sum(r["pass"] for r in B), len(B)) - Fraction(sum(r["pass"] for r in A), len(A))
        diff = float(gap) * 100
        r1 = gap >= Fraction(1, 4)
        t1 = f"B - A = {diff:+.0f} points (needs >= +25)"
    else:
        r1, t1 = False, "no trap runs for A and B"
    # rule 2
    if A and B:
        ca, cb = cpc(A), cpc(B)
        if cb is None:
            r2 = False
        elif ca is None:
            r2 = True
        else:
            r2 = cb < ca or (r1 and cb <= 1.3 * ca)
        f = lambda c: "n/a" if c is None else f"${c:.3f}"
        ratio = f", ratio {cb / ca:.2f}" if (ca and cb is not None) else ""
        t2 = f"cost per correct: A {f(ca)}, B {f(cb)}{ratio} (needs B < A, or <= 1.3x A while rule 1 holds)"
    else:
        r2, t2 = False, "no trap runs for A and B"
    # rule 3
    if cA and cB:
        ma, mb = mean([r.get("cost_usd") for r in cA]), mean([r.get("cost_usd") for r in cB])
        allpass = all(r["pass"] for r in cB)
        ok = ma is not None and mb is not None and mb <= 1.10 * ma
        r3 = ok and allpass
        t3 = (f"C1 mean cost A ${num(ma, '{:.3f}')}, B ${num(mb, '{:.3f}')}"
              + (f", ratio {mb / ma:.2f}" if ma and mb is not None else "")
              + f"; B passes {sum(r['pass'] for r in cB)}/{len(cB)} (needs <= 1.10x and all pass)")
    else:
        r3, t3 = False, "no C1 runs for A and B"
    # rule 4
    if Bp and cBp:
        hr_t, hr_c = rate(Bp, "header_written"), rate(cBp, "header_written")
        r4 = hr_t >= 0.5 and hr_c == 0
        t4 = f"B' header rate: trap {pct(hr_t)} (needs >= 50%), C1 {pct(hr_c)} (needs 0%)"
    elif Bp:
        r4, t4 = False, f"no C1 runs for B' (trap header rate {pct(rate(Bp, 'header_written'))})"
    else:
        r4, t4 = False, "no trap runs for B'"

    def v(ok, applicable=True):
        if tie and applicable:
            return "TIE"
        return "MET" if ok else "NOT MET"

    verdicts = [
        ("1. Helps", v(r1), t1),
        ("2. Worth it", v(r2), t2),
        ("3. Cheap when not needed", v(r3, False), t3),
        ("4. Picked up by itself", v(r4, False), t4),
        ("5. A tie is a tie", "TIE" if tie else "NOT MET (no tie)", tie_txt),
    ]
    md += ["", "## Decision rules", ""]
    for name, verdict, txt in verdicts:
        md.append(f"- **{name}: {verdict}**. {txt}")
    if tie:
        md += ["", "No detectable difference; the tasks may be too easy or too hard for this model. Claim nothing."]

    text = "\n".join(md) + "\n"
    with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
