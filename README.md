# aim-higher

**A planning skill for AI coding agents. Before you plan, aim at the outcome above the task, and say how you will know it worked.**

Agents are good at doing exactly what was asked. That is often the problem:

- the reported crash is fixed, and the same cause still breaks two other commands;
- the new wording lands in the README, but not in the page metadata or the `--help` text;
- the guard blocks what it should, and also blocks harmless commands nobody tested;
- the analysis builds on the team's belief instead of checking it against the data.

`aim-higher` makes the agent write an 8-line plan header before it plans steps. It skips itself on small clear tasks. It is plain text with no vendor, tool or agent dependency; so far it has been measured on one model (below).

```
PLAN HEADER
1. Outcome: what must stay true after this is done, and how it is measured
2. Whole or symptom: is this request one case of a bigger problem?
3. Outside check: what, besides the agent's own judgment, shows it is right
4. Budget: time, steps or rounds before stopping to report
5. Must / stretch: what must ship; what is a stretch, and when to drop it
6. Not doing: what is out of scope
7. Already decided: choices not to reopen, copied word for word
8. Open: at most 3 questions for the requester, each with a recommended answer
```

For large or high-stakes work it can go one step deeper (pick at most two): what an expert in the field would do, re-checking a belief against the raw data, borrowing a technique from another field, or imagining the failure first.

## Does it help?

A first pilot: Claude Opus 5.5, five tasks, three runs per task and arm, 45 runs, $10.28 in total. Arm A has no skill; arm B has the skill and the prompt asks for it; arm B' has the skill installed and not mentioned. Full numbers: [`bench/runs/2026-10-30-opus-5-5-pilot/summary.md`](bench/runs/2026-10-30-opus-5-5-pilot/summary.md).

| | A: no skill | B: skill, asked for | B': skill installed only |
|---|---|---|---|
| Trap tasks passed | 9 / 12 | 12 / 12 | 12 / 12 |
| Cost per correct result (trap tasks) | $0.286 | $0.327 | $0.242 |
| Mean time per trap run | 88 s | 121 s | 89 s |
| Mean tokens per trap run | 228,609 | 352,342 | 248,823 |
| Typo task (C1) cost per run | $0.082 | $0.123 | $0.086 |

Against the rules fixed before the first run:

1. **Helps: met**, exactly at the threshold (B passes 25 points more often than A).
2. **Worth it: met.** B's cost per correct result is 1.14x A's (the limit is 1.3x).
3. **Cheap when not needed: not met.** Asking for the skill on a one-word typo fix cost 1.50x. With the skill only installed (B'), the same task cost 1.05x.
4. **Picked up by itself: not met.** B' loaded the skill in 3 of 12 trap runs, all on one task.
5. No tie.

What this shows and what it does not:

- **The whole difference is one task.** In T1 (a crash on a large log), all three runs without the skill fixed the reported command, noticed that two other commands had the same cause, and left them as separate tickets. All three runs with the skill fixed all three. That is the "whole or symptom" line at work. Whether fixing the other two is right depends on what the requester wanted; the hidden check assumes they wanted the tool to work on their log.
- **B' also fixed all three in T1 without ever loading the skill.** So the skill's text cannot explain B' there. The always-loaded description (about 220 tokens) or chance (three runs) might; this data cannot tell them apart.
- **The other three traps passed in every arm.** Opus 5.5 already avoids them, as the pre-registration said it might.
- **Rule 1 landed exactly on its threshold**, so one more failure with the skill or one more success without it would have flipped it. Separately, a code review before scoring found that the summary script's floating-point arithmetic could read some exact 25-point gaps (8/12 against 5/12) as 24.999 and fail them; the pilot's gap (12/12 against 9/12) is not one of them. The fix was hashed at 16:48 UTC, before the script first read pilot results ([`bench/FROZEN.sha256`](bench/FROZEN.sha256)).
- **The header is mostly invisible in the logs.** Opus 5.5's reasoning is hidden in the event stream, so "header written" counts only headers in visible text or files: B loaded the skill in 12 of 12 trap runs, and a visible header appears in 1.
- **Cost:** on trap tasks, B costs about 50% more per run than A and 14% more per correct result. B' costs 13% more per run and 15% less per correct result. Tokens follow the same pattern (B 1.54x A per run, B' 1.09x); most of each count is cached input re-read on every turn, so cost is the better guide.
- **Not significant yet.** With 9 of 12 against 12 of 12, a one-sided Fisher exact test gives p = 0.11. Three runs per cell cannot separate a real effect from chance.

So far: a pilot on one strong model with three runs per cell. It is consistent with the skill catching the "fixed the symptom, left the cause" miss at a modest cost. It does not show the skill is needed for the other three traps on this model, and asking for it on a trivial task wastes about half the cost again. Next: harder tasks for strong models, smaller models, and other agents.

The benchmark is in [`bench/`](bench/): five small tasks, four of them with a trap modelled on a miss that kept recurring in real agent work, each with an automatic hidden check. The decision rules were written down before the first run ([`bench/PREREGISTRATION.md`](bench/PREREGISTRATION.md)), and the files under test were hashed before it ([`bench/FROZEN.sha256`](bench/FROZEN.sha256)). You can rerun it with your own model.

## Install

**Claude Code (plugin):**

```
/plugin marketplace add WenyuChiou/aim-higher
/plugin install aim-higher@aim-higher
```

**Claude Code (plain skill):** copy `skills/aim-higher/` into `~/.claude/skills/` (all projects) or `.claude/skills/` (one project).

**Other agents that read `SKILL.md` skills** (for example Codex): copy `skills/aim-higher/` into that agent's skills folder; see its documentation for the location.

**Agents without skill support:** paste the body of [`skills/aim-higher/SKILL.md`](skills/aim-higher/SKILL.md) into the agent's instructions file (for example `AGENTS.md`) or system prompt.

Cost in Claude Code: about 220 tokens in every session (the skill's description), and about 2.4k tokens each time it is used (`claude plugin details`).

## Use it with other skills (all optional)

`aim-higher` is the step before the plan. It produces a header, not a design document, and needs nothing else. If you already use one of these, the header plugs in:

| You use | What the header gives it |
|---|---|
| a questioning skill such as `grill-me` | line 8, the open questions |
| superpowers `brainstorming` or `writing-plans`, or a spec kit | line 1 as the goal, lines 6 and 7 as constraints, line 3 as each step's acceptance check |
| a plan file that survives long sessions, such as planning-with-files | the header, at the top of the file |
| [agent-collab-skills](https://github.com/WenyuChiou/agent-collab-skills) (`agent-task-splitter`, `agent-debate`, `agent-acceptance-gate`) | lines 1, 3, 6 and 7 as each lane's goal, acceptance and limits; hard-to-undo line 8 questions for a debate; lines 1 and 3 for the final gate |
| several models or several AI agents | the header is written by your strongest model; research and steps can go to cheaper ones |

Nothing here needs a particular vendor, model or second agent.

## Credits

The altitude, depth and range ideas come from Felix Rieseberg, ["How to be more ambitious: a tutorial for humans with models"](https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/) (2026). Also drawn on: the premortem (Gary Klein), appetite and no-gos (Basecamp's Shape Up), committed versus aspirational goals (OKRs), the Heilmeier Catechism (DARPA), and the existing planning skills it is meant to sit beside, especially obra/superpowers and mattpocock's grilling skill. The wording is this project's own.

## License

MIT
