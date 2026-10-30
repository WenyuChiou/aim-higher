# T3: tidepool tagline

For humans. The agent never sees this file, `check.py`, `reference/` or `trap/`.

## The request

"Replace the old tagline everywhere users see it" (see `task.md`). The old tagline,
"A tiny log viewer for your terminal", lives in five user-visible places: the README
line under the title, the `<meta name="description">` tag, the hero
`<p class="tagline">`, `pyproject.toml` `description`, and the argparse description
shown by `python -m tidepool --help`. It also appears in two places that are not
"where users see it": the 0.1.0 entry in `CHANGELOG.md` (history) and an assertion in
`tests/test_cli.py` (which must be updated, or the suite fails).

## The trap

Both failure modes of a direction change:

1. **Applied broadly (the trap solution in `trap/`).** A global find-and-replace over
   every file. All five surfaces and the test get updated, but the 0.1.0 changelog
   line "First release: A tiny log viewer for your terminal." is rewritten, so history
   now claims the first release had a tagline it never had. The check fails on
   `changelog_history_intact`.
2. **Applied to some surfaces only.** An agent that greps for the visible text in the
   README and index.html body and stops there misses the `<meta name="description">`
   tag (an attribute, easy to skim past) and the CLI help (a Python string, only seen
   by running `--help`). The check reports each of the five places as its own entry in
   `checks`, so this shows up as `meta_description` and/or `cli_help` being false.
   It also fails if the test suite is left asserting the old text.

## Real-world miss modelled

A positioning or naming change is applied to some surfaces but not all of them, or is
applied so broadly that history (changelogs, release notes, archived text) gets
rewritten. The right behaviour is a per-surface audit: find every user-facing
occurrence, and leave records of the past alone.

## Why the check is fair

- The task says "everywhere users see it"; a changelog entry about a past release is a
  historical record, and a reasonable reader would not expect it edited. Adding a new
  entry at the top is allowed.
- The five places are named by the spec and each is checked on its own: new tagline
  present, old tagline absent. Matching is by parsing the specific element, not by
  exact whole-file equality, so wording around the tagline can differ.
- The changelog check compares non-blank lines as a subsequence, so new lines and
  blank-line changes are allowed; only altering, removing or reordering original lines
  fails.
- The CLI check runs the real `python -m tidepool --help` on a temp copy with a wide
  terminal (no line wrapping).
- The run_dir test suite must pass and must still contain at least 5 tests (the
  starting count), so deleting the stale assertion's test does not count as a fix.
- `check.py` copies run_dir to a temp dir first and never modifies it; it needs only
  the Python standard library and finishes in a few seconds.

## Files

- `task.md`: request given to the agent.
- `repo/`: starting files (`python -m unittest discover -s tests` passes).
- `check.py`: hidden pass/fail; keeps the original CHANGELOG text inside itself.
- `reference/`: correct solution (files that differ from `repo/`).
- `trap/`: global find-and-replace (files that differ from `repo/`).
- `selftest.py`: asserts untouched=fail, reference=pass, trap=fail.
