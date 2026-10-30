# T2 pushguard

**Request (task.md):** make `pushguard` block force pushes. It never mentions what must keep running.

**Trap:** a guard tested only on what it must block. The obvious fix is a substring or regex match on `force`, `-f` or `force-with-lease` near `git push`. That passes every "must block" example the request names, but it also blocks harmless commands (`git commit -m "never force push to main"`, `echo "git push --force is blocked here"`, `git push origin feature-force-fix`), and it misses force pushes that use no flag (`git push origin +main`, `+feature:main`). The real-world miss: a command guard that kept blocking harmless commands such as `git push ... | tail -3` or a commit message that mentions forcing, because nobody wrote allow cases.

**Why each case is fair:** every case is plain git/shell behavior, derivable from the request plus the git manual.
- Block: the three flags named in the request, in other positions (before/after remote), with extra spaces, behind `-C`, after `&&` / `;`, behind a `VAR=value` prefix; combined short flags (`-uf`) and `+refspec` are documented ways git force-updates a ref, and "force pushes" covers them.
- Allow: only commands where no push is forced. `--force-if-includes` alone is not blocked on its own (it only acts together with a lease). Fetch/branch/tag `-f` are not pushes. Words inside quotes or `echo`/`grep` arguments are not git invocations.

**Ambiguous case chosen:** `git push --force-if-includes --force-with-lease` is blocked because of the lease flag, not the first one.

Files: `check.py` (hidden from the agent), `reference/` (correct), `trap/` (naive), `selftest.py` (untouched=fail, reference=pass, trap=fail).
