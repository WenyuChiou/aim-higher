# Pre-registration: does aim-higher make agent work more effective?

Written before any benchmark run. Before the first run, the SHA-256 of the
skill file and of this file are recorded in `bench/FROZEN.sha256`; neither is
edited between runs. Any later skill version is re-tested on tasks it has not
been tuned on.

## Question

When a coding agent writes the aim-higher plan header before working, does it
finish more tasks correctly, and is the cost per correct result lower or
acceptably higher?

We care most about getting the work right the first time. Extra tokens or
minutes are acceptable when they buy correct results.

## Arms

| Arm | Skill installed | Prompt mentions the skill | What it measures |
|---|---|---|---|
| A | no | no | baseline |
| B | yes | yes ("Before planning, use the aim-higher skill.") | whether the skill's content helps when used |
| B' | yes | no | whether the agent picks the skill up by itself |

Everything else is identical: the same task prompt, model, tools and starting
files, and a fresh session for every run.

## Environment (pilot)

- Agent: Claude Code CLI 2.1.302, headless (`claude -p`), one fresh session per run.
- Model: Claude Opus 5.5 (`claude-opus-5-5`).
- Isolation from the author's own setup: `--setting-sources project`,
  `--strict-mcp-config`, `claudeMdExcludes` for every `CLAUDE.md`, `AGENTS.md`
  and `CLAUDE.local.md`, auto-memory off. A probe run confirmed that no
  personal instructions, personal skills, hooks or MCP servers load; only the
  CLI's built-in skills remain, and they are the same in every arm.
- Each run works in a fresh copy of the task's starting files, in a temporary
  folder outside this repository. The hidden checks and reference solutions
  are never copied in and are not in the run folder or any folder above it.
- The task prompt reaches the agent on standard input, followed by a fixed
  suffix (see `bench/run.py`): work alone, standard library only, do not
  commit, end with a short report.
- Repetitions: 3 per task per arm. 5 tasks x 3 arms x 3 = 45 runs.

## Tasks

Four tasks hide a trap modelled on a problem that recurred in the author's own
agent work (evidence in `bench/tasks/<id>/README.md`). One control task has no
trap. Each task has an automatic hidden check; no human or model judges pass or
fail.

| Id | Request given to the agent | Trap | Pass means |
|---|---|---|---|
| T1 | Fix one reported crash on large log files | Two other reported crashes share the same cause in other commands | all three commands work on a large file, with correct output |
| T2 | Add a guard that blocks force pushes | Many ordinary commands look similar and must stay allowed | every must-block case blocked and every must-allow case allowed |
| T3 | Change the product tagline everywhere users see it | Five places show it; old release notes must not be rewritten | new tagline in all five places, old one gone from them, release history unchanged |
| T4 | The team believes churn is an onboarding problem; plan and do the first analysis | The data say another factor drives churn | the stated main driver and onboarding effect match the data |
| C1 | Fix a one-word typo | none | typo fixed, nothing else changed |

## Measures

Recorded for every run:

- `pass`: the hidden check's verdict (primary).
- `tokens`: input + cache write + cache read + output tokens, from the CLI's own report.
- `cost_usd`: as reported by the CLI.
- `duration_s`, `turns`, `tool_calls`.
- `skill_used`: whether the run loaded the skill (from the event stream).
- `header_written`: whether the transcript contains `PLAN HEADER`.

Per task and arm: pass rate; mean tokens, cost and duration per run; and
**cost per correct result** = total cost of all runs / number of passing runs.

## Decision rules (fixed in advance)

1. **Helps** if, over the four trap tasks, arm B passes at least 25 percentage
   points more often than arm A.
2. **Worth it** if, over the four trap tasks, arm B's cost per correct result
   is lower than arm A's, or at most 30% higher while rule 1 holds.
3. **Cheap when not needed** if, on C1, arm B costs at most 10% more than arm A
   per run and still passes.
4. **Picked up by itself** if arm B' writes a header in at least half of the
   trap-task runs and in none of the C1 runs.
5. **A tie is a tie.** If both arms pass (or both fail) everything, we report
   "no detectable difference; the tasks may be too easy or too hard for this
   model", and claim nothing.

## Smoke test before freezing

Two runs with a small model (haiku) on C1 checked the pipeline end to end.
Arm B loaded the skill, wrote a one-line skip and passed, at about 1.6x the
cost of arm B', which did not load the skill and also passed. Rule 3 stays as
written; the C1 cost of B' versus A is reported alongside it, since an
installed skill that nobody invokes on a trivial task is the common case.
Nothing in the skill was changed after this test.

## Predictions recorded before running

- T2: no difference between A and B (a reviewer predicted that this class of
  miss is caught by tests and review, not by planning).
- Opus 5.5 is a strong model; some trap tasks may pass in arm A too, which
  would limit the measurable lift.

## Not claimed

- Results from one model, three repetitions and five small tasks are a pilot,
  not a general measurement.
- The author designed both the skill and the tasks. To limit that bias, the
  skill was drafted before the task files existed; the task files were then
  built by separate agents that never saw the skill; the skill's one later
  revision came from a survey of existing planning skills, not from the tasks;
  and none of the skill's examples use a task's subject. Tasks contributed by
  others are welcome.
