"""Deterministically generate repo/data/accounts.csv (seed fixed)."""
import csv, math, os, random

SEED = 20251030
N = 3000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repo", "data", "accounts.csv")


def poisson(rng, lam):
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def main():
    rng = random.Random(SEED)
    rows = []
    for i in range(1, N + 1):
        month = "2025-%02d" % rng.randint(1, 12)
        plan = rng.choices(["basic", "pro", "team"], [0.50, 0.30, 0.20])[0]
        seats = {"basic": rng.randint(1, 3), "pro": rng.randint(3, 10), "team": rng.randint(10, 50)}[plan]
        onb = rng.random() < {"basic": 0.45, "pro": 0.60, "team": 0.80}[plan]
        notice = rng.random() < 0.40
        p = 0.06 + (0.30 if notice else 0.0) - (0.015 if onb else 0.0)
        churned = rng.random() < p
        tickets = poisson(rng, 1.0) + (1 if churned and rng.random() < 0.06 else 0)
        yn = lambda b: "yes" if b else "no"
        rows.append([f"A{i:05d}", month, plan, seats, yn(onb), tickets, yn(notice), yn(churned)])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["account_id", "signup_month", "plan", "seats", "onboarding_completed",
                    "support_tickets_90d", "price_increase_notice", "churned"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
