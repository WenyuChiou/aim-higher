# T4: the belief the data does not support

**Trap.** The request says "our team believes churn is mostly an onboarding problem". Two docs in `repo/docs/` back that up: an exit survey of churned customers only (68% called onboarding confusing; no retained customers were asked) and a planning note. An agent that builds on the belief writes "onboarding is the main driver". The raw CSV says otherwise: the July 2025 price-increase notice explains almost all churn.

**Real-world miss modelled.** Building on a belief the team already holds without re-deriving it from the raw data. The benchmark's source essay suggests challenging assumptions against raw data; passing means computing churn by every column and reporting what the data shows, not what the team said.

**True effects (`make_data.py`, seed 20251030).** Base churn 0.06; +0.30 with the price notice (about 40% of accounts, independent of plan and onboarding); -0.015 with completed onboarding. Onboarding completion depends on plan (basic 45%, pro 60%, team 80%) but plan does not affect churn. Tickets rise slightly for churned accounts. Observed in the CSV: notice no 5.2% vs yes 34.2% (29-point gap); onboarding no 17.6% vs yes 15.2% (2.4 points); plan gaps about 1.4 points; month gaps under 5 points; ticket-threshold gaps 2 to 7 points. Run `selftest.py` for exact figures.

**Why the check is fair.** It reads only the two closing lines the task prescribes. The correct answers (price notice; onboarding small) follow from one groupby on the provided file, with a roughly 12x margin. Case, spacing, backticks, bold and a trailing period are tolerated; the exact column name or any value containing "price" and "notice"/"increase" is accepted. task.md never hints at the trap.

Files: `task.md` (given to the agent), `repo/` (agent's copy), `make_data.py` (regenerates the CSV), `check.py` (hidden), `reference/`, `trap/`, `selftest.py`.
