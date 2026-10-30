# T1 logstat: one reported case, same cause elsewhere

**Trap.** The ticket names only `summary` (issue #12). The cause (whole-file reads) is
also present in `tail` (own `readlines()`) and `grep` (own `read()`), listed as #15 and
#19 in `repo/ISSUES.md`. `read_all()` only serves `summary`, so fixing it alone leaves the
other two commands crashing on big logs. `task.md` never mentions them.

**Recurring miss modelled.** An agent fixes the one reported case while the same cause
breaks other paths. A thorough agent greps for other whole-file reads (or reads
ISSUES.md) and fixes all three.

**Why the check is fair.** It asks for what the ticket's cause implies: the tool must
cope with a big log. A simulated 1 MiB limit (not a real allocation, so it is
deterministic and light) makes whole-file reads of a ~5 MB file raise MemoryError, while
line iteration and chunked reads up to 1 MiB are allowed, so any streaming design passes
(deque, seek from the end, etc.). Outputs are compared with values the check computes
itself while generating the file (fixed seed), through the package's real entry point
(`python -m logstat` via runpy). The agent's own tests must also pass. Not graded: style,
extra files, ISSUES.md edits, the unrelated #21/#22.
