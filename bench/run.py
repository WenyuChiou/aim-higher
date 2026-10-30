#!/usr/bin/env python3
"""A/B benchmark runner: run a coding agent headless on each (task, arm, rep),
then run the task's hidden check. Python 3 standard library only."""

import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time

BENCH_DIR = os.path.dirname(os.path.abspath(__file__))

SUFFIX = (
    "You are working alone in this folder and nobody will answer questions, "
    "so make reasonable choices and finish the task. Use only the Python "
    "standard library; do not install packages. Do not commit. When you are "
    "done, end with a short report: what you changed and how you checked it."
)
B_PREFIX = "Before planning, use the aim-higher skill.\n\n"
SETTINGS_JSON = json.dumps(
    {
        "claudeMdExcludes": ["**/CLAUDE.md", "**/AGENTS.md", "**/CLAUDE.local.md"],
        "autoMemoryEnabled": False,
    }
)
STDOUT_CAP = 20 * 1024 * 1024
STDERR_CAP = 1024 * 1024
DIFF_CAP = 2 * 1024 * 1024
IS_WIN = os.name == "nt"

_score_lock = threading.Lock()


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def sha256_file(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="aim-higher A/B benchmark runner")
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--arms", default="A,B,Bp")
    p.add_argument("--tasks", default="T1,T2,T3,T4,C1")
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--concurrency", type=int, default=3)
    p.add_argument("--timeout", type=int, default=1500, help="seconds per run")
    p.add_argument("--out", default=None)
    p.add_argument("--tasks-dir", default=os.path.join(BENCH_DIR, "tasks"))
    p.add_argument(
        "--skill-dir",
        default=os.path.normpath(os.path.join(BENCH_DIR, "..", "skills", "aim-higher")),
    )
    p.add_argument("--agent-cmd", default="claude")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--seed", type=int, default=7)
    a = p.parse_args(argv)
    if a.out is None:
        stamp = utc_now().strftime("%Y%m%d-%H%M")
        a.out = os.path.join(BENCH_DIR, "runs", f"{stamp}-{a.model}")
    a.out = os.path.abspath(a.out)
    a.tasks_dir = os.path.abspath(a.tasks_dir)
    a.skill_dir = os.path.abspath(a.skill_dir)
    return a


# ---------------------------------------------------------------- processes

def kill_tree(proc):
    try:
        if IS_WIN:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            import signal
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def pump(stream, path, cap):
    """Copy stream to path, writing at most cap bytes; keep draining after."""
    written = 0
    with open(path, "wb") as f:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            if written < cap:
                part = chunk[: cap - written]
                f.write(part)
                written += len(part)


def run_agent(cmd, cwd, env, raw_path, err_path, timeout, prompt):
    """Returns (exit_code, timed_out). The prompt goes in on stdin, which
    survives multi-line text on every platform (argv through a .cmd shim
    does not)."""
    kwargs = {}
    if not IS_WIN:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs,
    )
    t1 = threading.Thread(target=pump, args=(proc.stdout, raw_path, STDOUT_CAP), daemon=True)
    t2 = threading.Thread(target=pump, args=(proc.stderr, err_path, STDERR_CAP), daemon=True)
    t1.start()
    t2.start()
    try:
        proc.stdin.write(prompt.encode("utf-8"))
        proc.stdin.close()
    except OSError:
        pass
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_tree(proc)
        try:
            proc.wait(timeout=30)
        except Exception:
            pass
    t1.join(timeout=30)
    t2.join(timeout=30)
    return proc.returncode, timed_out


def git(args, cwd, check=True):
    r = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false"] + args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.decode('utf-8', 'replace')[:500]}")
    return r.stdout.decode("utf-8", "replace")


# ------------------------------------------------------------ stream parsing

def parse_stream(path):
    res = {
        "tokens": None,
        "cost_usd": None,
        "turns": None,
        "duration_s": None,
        "final_report": "",
        "is_error": None,
        "tool_calls": 0,
        "skill_used": False,
        "header_written": False,
    }
    last_result = None
    try:
        f = open(path, "r", encoding="utf-8", errors="replace")
    except OSError:
        return res
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if not isinstance(ev, dict):
                continue
            t = ev.get("type")
            if t == "result":
                last_result = ev
            elif t == "assistant":
                msg = ev.get("message")
                content = msg.get("content") if isinstance(msg, dict) else ev.get("content")
                if not isinstance(content, list):
                    continue
                for blk in content:
                    if not isinstance(blk, dict):
                        continue
                    bt = blk.get("type")
                    if bt == "tool_use":
                        res["tool_calls"] += 1
                        inp = json.dumps(blk.get("input", ""))
                        if blk.get("name") == "Skill" and "aim-higher" in inp:
                            res["skill_used"] = True
                        if "PLAN HEADER" in inp:
                            res["header_written"] = True
                    elif bt == "text":
                        if "PLAN HEADER" in str(blk.get("text", "")):
                            res["header_written"] = True
    if last_result:
        u = last_result.get("usage") or {}
        try:
            res["tokens"] = sum(
                int(u.get(k) or 0)
                for k in ("input_tokens", "cache_creation_input_tokens",
                          "cache_read_input_tokens", "output_tokens")
            )
        except (TypeError, ValueError):
            pass
        res["cost_usd"] = last_result.get("total_cost_usd")
        res["turns"] = last_result.get("num_turns")
        if isinstance(last_result.get("duration_ms"), (int, float)):
            res["duration_s"] = round(last_result["duration_ms"] / 1000.0, 3)
        res["final_report"] = str(last_result.get("result") or "")[:2000]
        res["is_error"] = bool(last_result.get("is_error", False))
    return res


# ------------------------------------------------------------------ one run

def write_fake_stream(path, arm):
    events = []
    if arm == "B":
        events.append({
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "PLAN HEADER\nGoal: dry run"}]},
        })
    events.append({
        "type": "result",
        "usage": {"input_tokens": 10, "cache_creation_input_tokens": 100,
                  "cache_read_input_tokens": 1000, "output_tokens": 50},
        "total_cost_usd": 0.01,
        "num_turns": 2,
        "duration_ms": 1234,
        "result": "done",
    })
    with open(path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")


def build_prompt(task_dir, arm):
    with open(os.path.join(task_dir, "task.md"), "r", encoding="utf-8") as f:
        text = f.read()
    prompt = text + "\n\n" + SUFFIX
    if arm == "B":
        prompt = B_PREFIX + prompt
    return prompt


def prepare_work(args, task, arm, work):
    task_dir = os.path.join(args.tasks_dir, task)
    if os.path.exists(work):
        # stale dir from an interrupted run: move aside, never delete
        shutil.move(work, work + ".stale-" + utc_now().strftime("%H%M%S%f"))
    os.makedirs(os.path.dirname(work), exist_ok=True)
    shutil.copytree(os.path.join(task_dir, "repo"), work)
    if arm in ("B", "Bp"):
        shutil.copytree(args.skill_dir, os.path.join(work, ".claude", "skills", "aim-higher"))
    git(["init", "-q"], work)
    git(["config", "user.name", "bench"], work)
    git(["config", "user.email", "bench@example.invalid"], work)
    git(["add", "-A"], work)
    git(["commit", "-q", "-m", "start"], work)


def run_check(args, task, work):
    check = os.path.join(args.tasks_dir, task, "check.py")
    try:
        r = subprocess.run(
            [sys.executable, "-I", check, work],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return False, {}, "check timed out"
    except Exception as e:
        return False, {}, f"check failed to run: {e}"
    out = r.stdout.decode("utf-8", "replace")
    for line in reversed(out.strip().splitlines()):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if isinstance(d, dict) and "pass" in d:
            return bool(d.get("pass")), d.get("checks", {}), str(d.get("notes", ""))
    err = r.stderr.decode("utf-8", "replace")[-500:]
    return False, {}, f"check output unparsable (exit {r.returncode}): {out[-300:]} {err}"


def execute_run(args, task, arm, rep, work_root):
    run_id = f"{task}-{arm}-r{rep}"
    started = utc_now()
    t0 = time.time()
    work = os.path.join(work_root, run_id)
    raw_dir = os.path.join(args.out, "raw")
    raw_path = os.path.join(raw_dir, run_id + ".jsonl")
    err_path = os.path.join(raw_dir, run_id + ".err")
    exit_code, timed_out, setup_error = None, False, None
    try:
        prepare_work(args, task, arm, work)
        if args.dry_run:
            ref = os.path.join(args.tasks_dir, task, "reference")
            if os.path.isdir(ref):
                shutil.copytree(ref, work, dirs_exist_ok=True)
            write_fake_stream(raw_path, arm)
            open(err_path, "w").close()
            exit_code = 0
        else:
            prompt = build_prompt(os.path.join(args.tasks_dir, task), arm)
            exe = shutil.which(args.agent_cmd) or args.agent_cmd
            cmd = [exe, "-p", "--model", args.model,
                   "--setting-sources", "project", "--strict-mcp-config",
                   "--no-session-persistence", "--settings", SETTINGS_JSON,
                   "--output-format", "stream-json", "--verbose",
                   "--permission-mode", "bypassPermissions"]
            env = dict(os.environ)
            env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
            exit_code, timed_out = run_agent(cmd, work, env, raw_path, err_path, args.timeout, prompt)
    except Exception as e:
        setup_error = f"{type(e).__name__}: {e}"
        for pth in (raw_path, err_path):
            if not os.path.exists(pth):
                open(pth, "w").close()

    wall = time.time() - t0
    parsed = parse_stream(raw_path)

    # diff of the agent's work
    try:
        diff = git(["diff"], work, check=False)
        status = git(["status", "--porcelain"], work, check=False)
        untracked = [l for l in status.splitlines() if l.startswith("??")]
        body = diff + "\n# untracked files and status (git status --porcelain)\n" + "\n".join(status.splitlines()) + "\n"
        body = body.encode("utf-8", "replace")[:DIFF_CAP]
        os.makedirs(os.path.join(args.out, "diffs"), exist_ok=True)
        with open(os.path.join(args.out, "diffs", run_id + ".diff"), "wb") as f:
            f.write(body)
    except Exception:
        pass

    if setup_error:
        passed, checks, notes = False, {}, "setup error: " + setup_error
    else:
        passed, checks, notes = run_check(args, task, work)
    if timed_out:
        notes = ("TIMED OUT; " + notes).strip()

    row = {
        "run_id": run_id,
        "task": task,
        "arm": arm,
        "rep": rep,
        "model": args.model,
        "pass": passed,
        "checks": checks,
        "notes": notes,
        "tokens": parsed["tokens"],
        "cost_usd": parsed["cost_usd"],
        "duration_s": parsed["duration_s"] if parsed["duration_s"] is not None else round(wall, 3),
        "turns": parsed["turns"],
        "tool_calls": parsed["tool_calls"],
        "skill_used": parsed["skill_used"],
        "header_written": parsed["header_written"],
        "exit_code": exit_code,
        "timed_out": timed_out,
        "is_error": parsed["is_error"],
        "final_report": parsed["final_report"],
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with _score_lock:
        with open(os.path.join(args.out, "scorecard.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    return row


# --------------------------------------------------------------------- main

def main(argv=None):
    args = parse_args(argv)
    tasks = [t for t in args.tasks.split(",") if t]
    arms = [a for a in args.arms.split(",") if a]
    for a in arms:
        if a not in ("A", "B", "Bp"):
            sys.exit(f"unknown arm: {a}")
    os.makedirs(os.path.join(args.out, "raw"), exist_ok=True)
    os.makedirs(os.path.join(args.out, "diffs"), exist_ok=True)

    for t in tasks:
        if not os.path.isdir(os.path.join(args.tasks_dir, t)):
            sys.exit(f"task folder not found: {os.path.join(args.tasks_dir, t)}")
    if any(a in ("B", "Bp") for a in arms) and not os.path.isdir(args.skill_dir):
        sys.exit(f"skill dir not found: {args.skill_dir}")

    cli_version = None
    if not args.dry_run:
        try:
            exe = shutil.which(args.agent_cmd) or args.agent_cmd
            r = subprocess.run([exe, "--version"], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=60)
            cli_version = r.stdout.decode("utf-8", "replace").strip()
        except Exception as e:
            cli_version = f"unknown ({e})"
    cfg_path = os.path.join(args.out, "run_config.json")
    if not os.path.exists(cfg_path):
        cfg = {
            "args": vars(args),
            "cli_version": cli_version,
            "skill_md_sha256": sha256_file(os.path.join(args.skill_dir, "SKILL.md")),
            "preregistration_sha256": sha256_file(os.path.join(BENCH_DIR, "PREREGISTRATION.md")),
            "created_at": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

    triples = [(t, a, r) for t in tasks for a in arms for r in range(1, args.reps + 1)]
    random.Random(args.seed).shuffle(triples)

    done = set()
    sc = os.path.join(args.out, "scorecard.jsonl")
    if os.path.exists(sc):
        with open(sc, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["run_id"])
                except (ValueError, KeyError, TypeError):
                    pass
    todo = [x for x in triples if f"{x[0]}-{x[1]}-r{x[2]}" not in done]
    print(f"{len(triples)} runs planned, {len(done & {f'{t}-{a}-r{r}' for t, a, r in triples})} already done, {len(todo)} to run")

    # Work dirs live outside this repo so an agent cannot wander up into the
    # hidden checks and reference solutions under bench/tasks/.
    work_root = os.path.join(tempfile.gettempdir(), "aim-higher-bench-work",
                             os.path.basename(args.out.rstrip("/\\")))
    total = len(todo)
    counter = [0]

    def job(x):
        return execute_run(args, x[0], x[1], x[2], work_root)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as ex:
        futs = {ex.submit(job, x): x for x in todo}
        for fut in concurrent.futures.as_completed(futs):
            x = futs[fut]
            counter[0] += 1
            try:
                row = fut.result()
                cost = row["cost_usd"]
                print(f"[{counter[0]}/{total}] {row['run_id']} "
                      f"{'PASS' if row['pass'] else 'FAIL'} "
                      f"cost={cost if cost is not None else 'n/a'} "
                      f"dur={row['duration_s']}s timed_out={row['timed_out']}", flush=True)
            except Exception as e:
                print(f"[{counter[0]}/{total}] {x[0]}-{x[1]}-r{x[2]} ERROR {e}", flush=True)
    print(f"done. scorecard: {sc}")


if __name__ == "__main__":
    main()
