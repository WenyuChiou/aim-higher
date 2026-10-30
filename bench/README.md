# Benchmark: does the aim-higher skill help?

An A/B test. For each task, arm and repetition, a coding agent runs headless in
a fresh copy of the task's starting files, then a hidden check says pass or
fail. Arms, measures and decision rules are fixed in `PREREGISTRATION.md`; do
not edit it between runs.

## Prerequisites

- Python 3 (standard library only) and git on the PATH.
- Claude Code CLI installed and logged in (`claude --version` works).
- Real runs cost money. Do a dry run first.

## Commands

Run from the repo root (`aim-higher/`).

```
# 1. Dry run: no agent call, no cost. Copies each task's reference solution
#    in place, so every check should pass and the pipeline is exercised.
python bench/run.py --dry-run --reps 1 --out bench/runs/dry

# 2. The pilot: 5 tasks x 3 arms x 3 reps = 45 real runs.
python bench/run.py

# 3. Summarize (also writes summary.md in the run folder).
python bench/summarize.py bench/runs/<folder>
```

Useful flags: `--tasks T1,C1`, `--arms A,B`, `--reps 1`, `--concurrency 3`,
`--timeout 1500` (seconds per run), `--model`, `--out`, `--seed`.
Re-running the same command with the same `--out` resumes: runs already in
`scorecard.jsonl` are skipped.

## Files

- `run.py` - the runner.
- `summarize.py` - tables and the five decision rules.
- `PREREGISTRATION.md` - the plan, written before any run.
- `tasks/<ID>/` - one folder per task (see below).
- `runs/<stamp>-<model>/` - output of one run set: `scorecard.jsonl` (one line
  per run), `raw/` (agent event stream and stderr), `diffs/` (what the agent
  changed), `run_config.json` (arguments, CLI version, SHA-256 of `SKILL.md`
  and `PREREGISTRATION.md`), `summary.md`.
- `<system temp>/aim-higher-bench-work/<run folder>/<run_id>/` - the working
  copy each agent used, outside this repository so an agent cannot reach the
  hidden checks. Kept for inspection, never deleted by the runner. Safe to
  remove by hand.

## Arms

- A: no skill, plain prompt.
- B: skill installed, prompt starts with "Before planning, use the aim-higher skill."
- Bp: skill installed, prompt does not mention it.

## Isolation

Each agent starts in a new git repo containing only the task's `repo/` files
(plus the skill under `.claude/skills/aim-higher/` for B and Bp). It is started
with `--setting-sources project`, `--strict-mcp-config`, `--no-session-persistence`,
`claudeMdExcludes` for every `CLAUDE.md`, `AGENTS.md` and `CLAUDE.local.md`,
auto-memory off, and `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`. The hidden checks and
reference solutions stay in `tasks/` and are never copied into the work folder.

To verify isolation, make a throwaway folder, `cd` into it, and run:

```
claude -p "List every CLAUDE.md, AGENTS.md, memory file, personal skill, hook and MCP server you were given. Say 'none' for each that is absent." \
  --setting-sources project --strict-mcp-config --no-session-persistence \
  --settings '{"claudeMdExcludes":["**/CLAUDE.md","**/AGENTS.md","**/CLAUDE.local.md"],"autoMemoryEnabled":false}'
```

Expect "none" for all of them (the CLI's built-in skills are fine; they are the
same in every arm). If anything personal shows up, stop and fix before running.

## Add a task

Create `tasks/<ID>/` with:

- `task.md` - the request, exactly as the agent should see it (the runner adds
  a fixed closing paragraph).
- `repo/` - the starting files.
- `check.py` - run as `python -I check.py <run_dir>`; prints one JSON line
  `{"pass": true|false, "checks": {...}, "notes": "..."}`. It must not need
  network or packages.
- `reference/` - a correct solution: only the files that differ from `repo/`,
  at the same relative paths.

Then run `python bench/run.py --dry-run --tasks <ID> --reps 1 --out bench/runs/dry`.
The check must pass on the reference and fail on the untouched `repo/`. Treat
any task ID other than `C1` as a trap task in the summary; `C1` is the control.
