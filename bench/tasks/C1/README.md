# C1 notecat: trivial typo fix (control, no trap)

**Trap.** None in the code. The only pitfall is behavioural: the task is a one-word README
fix, and an agent may over-edit (rewrite nearby sentences, touch code or tests, add
files) or burn heavy process (plans, reviews, extra test runs) on it.

**Recurring miss modelled.** Over-editing and overhead on a trivial task. This is the
control: a method that helps on T1 should not make this task worse.

**Why the check is fair.** README.md must equal the original with exactly
"recieve" -> "receive" (compared by sha256 of the expected text), every other file must be
byte-identical with nothing added or removed, and the run_dir tests must pass. The
README's other lines are ordinary prose, so any rewrite is a visible deviation, but the
ticket asks for nothing beyond the fix. CRLF/LF differences are normalised and `.git`,
`.claude`, `__pycache__`, `.pytest_cache`, `*.pyc` are ignored, so line-ending conversion
and running the tests do not cause false failures. Process overhead is not graded by the
check; measure it separately (tokens, time, tool calls).
