---
name: aim-higher
description: >-
  Use before starting non-trivial work: a new project, a plan with several
  steps or days, the next version's scope, a research phase, a fix whose cause
  may reach beyond the one reported case, a change that touches several places,
  or work that several people or agents will share. Also use when someone asks
  to think bigger, aim higher or see the big picture. Writes an 8-line plan
  header first: the outcome that must stay true and how to measure it, whether
  the request is one symptom of a bigger problem, an outside check, a budget,
  must-do versus stretch items, what is out of scope, what is already decided,
  and what is still open. Skip it for small, clear tasks.
---

# Aim higher

Most plans aim at the exact task that was asked for ("fix crash #12"). Many
misses start there: the same cause comes back next week through another door,
a change lands in one place but not in the other three, or nobody can show the
result is right. Before you plan steps, write a short header that aims the work
at the outcome above the task and says how the result will be checked.

It is the step before the plan. It produces a header, not a design document or
a spec; whatever planning method you use next starts from it. It works with
any model and any setup, and needs no other skill, no helpers and no
particular tools.

## Step 1. Decide whether to use it

Skip it when both are true:

- the request says exactly what to change, and the change is small (one file,
  a few lines);
- a wrong guess would be cheap to notice and undo.

Then write one line, `Plan header: skipped (small, clear task)`, and do the
task. In every other case continue. If unsure, write the header: it takes a
minute.

## Step 2. Look before you write

Read the request, the files it touches and any data it mentions. Search for
related places: the same error, the same function, the same wording, the same
setting. Anything you can look up is a fact to find, not a question to ask.

## Step 3. Write the header

Write these 8 lines, one or two sentences each. Every line must be specific to
this work. If a line has nothing specific to say, write `none`; never fill it
with general advice. Placeholders such as "TBD", "as appropriate", "ensure
quality" or "test thoroughly" do not count as an answer.

```
PLAN HEADER
1. Outcome: <what must stay true after this is done> - measured by <how>
2. Whole or symptom: <is this request one case of a bigger problem? name it, or "whole">
3. Outside check: <what, besides your own judgment, will show it is right; prefer something you can run>
4. Budget: <time, steps or rounds before you stop and report>
5. Must / stretch: must: <...>; stretch: <...> (drop it if <condition>)
6. Not doing: <what is out of scope, including things that look related>
7. Already decided: <choices made by the requester or by earlier work, copied word for word; do not reopen them>
8. Open: <questions only the requester can answer, at most 3, each with your recommended answer, worded so that "yes" accepts it>
```

How a weak line and a strong line differ:

| Line | Weak | Strong |
|---|---|---|
| 1 Outcome | "Make the export faster." | "Every customer's invoice export finishes in under 30 seconds, measured on a copy of the largest account." |
| 2 Whole or symptom | "This is urgent." | "Symptom: the export, the monthly report and the API all load every invoice at once; fix the loading, not only the export." |
| 3 Outside check | "I will review it carefully." | "A timing script on the largest account, plus the existing test suite." |
| 4 Budget | "As long as it takes." | "Half a day; if the check is not green by then, stop and report." |
| 5 Must / stretch | "Do everything." | "Must: batched loading on all three paths. Stretch: under 10 seconds (drop it if it needs a database change)." |
| 6 Not doing | (left out) | "Not changing the export file format; not touching billing rules." |
| 7 Already decided | (left out although the requester said it) | "No new dependencies; keep the public API." |
| 8 Open | "Any feedback?" | "Keep very large exports as downloads for now, and not email them? Recommended: yes." |

## Step 4. Go deeper only when it pays (optional)

For large or high-stakes work, pick at most two of these and add one line each
under the header. If you cannot name something specific, skip it.

- **Expert method.** What would the best practitioner in this field do that the
  request does not ask for? From which raw material would they start, and with
  which method or tool?
- **Recheck a belief.** Is something taken as true here (in the request, the
  docs, the team's story)? Re-derive it from the raw data before building on it.
- **Borrow a field.** Rewrite the task as a verb ("get busy people to decide in
  30 minutes" rather than "make a slide deck"). Name one other field that does
  that verb well and the specific technique it would use.
- **Fail first.** Imagine it shipped and failed. Name the most likely cause,
  the check that would catch it before shipping, and the evidence that would
  make you change the plan.

## Step 5. Use the header

- Put it at the top of the plan, issue, pull request or brief.
- Ask the line 8 questions before the work that depends on them; keep doing
  the work that does not. If the requester already said to go ahead, or nobody
  can answer (an unattended run), take your recommended answers and list them
  in your report.
- Then plan the steps with whatever method you normally use. Every step should
  serve line 1 and use line 3 as its acceptance check.
- If you hand parts of the work to helpers or other agents, give each one lines
  1, 3, 6 and 7. When a helper reports back, ask for the check's actual output,
  not just "done".
- Before you call it done, run the line 3 check, compare the result with line
  1, and report must and stretch items honestly. A missed stretch item is fine;
  say that it was missed.

## Using it with other tools (all optional)

Each of these works on its own. If you have them, the header plugs in:

| If your setup has | Give it |
|---|---|
| a clarifying-questions step or skill (for example `grill-me`) | line 8 |
| a design or step-by-step planning skill (for example superpowers `brainstorming` or `writing-plans`, or a spec kit) | the whole header: line 1 as the goal, lines 6 and 7 as constraints, line 3 as each step's acceptance |
| a plan file that survives long sessions (for example planning-with-files) | the header, at the top of that file |
| a planner that splits work across agents (for example `agent-task-splitter` from agent-collab-skills) | lines 1, 3, 6 and 7 as each lane's goal, acceptance and limits |
| a debate or second-opinion step | any line 8 question that is hard to undo |
| an acceptance or review gate | lines 1 and 3 to check against |
| several models, or other AI agents (for example a second coding agent) | write the header with your strongest model, since it is judgment; Step 4 research and the planned steps can go to cheaper models or other agents, each with lines 1, 3, 6 and 7 |

Without any of these, do every step yourself, in order. Nothing in this skill
requires a particular vendor, model, agent or tool.

## Credits

The altitude, depth and range ideas come from Felix Rieseberg, "How to be more
ambitious: a tutorial for humans with models" (2026). Also drawn on: the
premortem (Gary Klein), appetite and no-gos (Basecamp's Shape Up), committed
versus aspirational goals (OKRs) and the Heilmeier Catechism (DARPA). The
wording here is this project's own.
