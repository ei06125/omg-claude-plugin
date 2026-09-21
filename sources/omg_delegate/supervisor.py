"""The detached supervisor: run the agent, enforce the timeout, record how it ended, clean up.

It runs as `python -m omg_delegate.supervisor <run_dir>`, started by the harness, and outlives the call.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from . import records
from .sbx import Sbx


def main(run_dir: str) -> None:
    run_dir = Path(run_dir)
    spec = json.loads((run_dir / "run.json").read_text())
    task = sys.stdin.read()
    log = records.logger(Path(spec["state_dir"]))
    sbx = Sbx(spec["sbx"], dict(os.environ), log)
    try:
        record = supervise(run_dir, spec, task, sbx, log)
    except Exception as error:
        log.exception("supervisor failed for %s", run_dir.name)
        record = {
            "status": "failed",
            "reason": "supervisor_error",
            "error": str(error)[:200],
        }
        if not spec["keep"]:
            sbx.remove(spec["sandbox"])
    records.write_json(run_dir / "completion.json", record)


def supervise(run_dir: Path, spec: dict, task: str, sbx: Sbx, log) -> dict:
    before = snapshot(spec["rw_paths"])
    started = time.monotonic()
    command = [spec["sbx"], "exec"]
    if spec["workdir"]:
        command += ["-w", spec["workdir"]]
    for key, value in spec["agent_env"].items():
        command += ["-e", f"{key}={value}"]
    command += [spec["sandbox"], *spec["agent_argv"], task]
    status, code = run_agent(
        command,
        run_dir / "agent.log",
        spec["timeout_seconds"],
        sbx,
        spec["sandbox"],
        log,
    )
    after = snapshot(spec["rw_paths"])
    record = {
        "status": status,
        "exit_code": code,
        "duration_seconds": round(time.monotonic() - started, 1),
        "finished_at": records.now(),
        "changed_files": sorted(p for p, sig in after.items() if before.get(p) != sig),
        "deleted_files": sorted(before.keys() - after.keys()),
    }
    if spec["clone"]:
        record["clone"] = clone_result(spec["clone"])
    if not spec["keep"]:
        sbx.remove(spec["sandbox"])
    log.info("run %s ended: %s", run_dir.name, status)
    return record


def run_agent(
    command: list[str], log_path: Path, timeout: int, sbx: Sbx, sandbox: str, log
) -> tuple[str, int | None]:
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as out:
        proc = subprocess.Popen(
            command,
            stdout=out,
            stderr=subprocess.STDOUT,
            env=dict(os.environ),
            start_new_session=True,
        )
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            log.info("timeout after %s seconds in %s", timeout, sandbox)
            terminate(proc)
            sbx.stop(sandbox)
            return "timeout", None
    return ("completed" if code == 0 else "failed"), code


def terminate(proc: subprocess.Popen) -> None:
    os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()


def snapshot(paths: list[str]) -> dict[str, tuple[int, int]]:
    """Path to (mtime, size) for every file under the read-write volumes. Symlinks are not followed."""
    seen: dict[str, tuple[int, int]] = {}
    for root in paths:
        if os.path.isfile(root):
            stat = os.stat(root)
            seen[root] = (stat.st_mtime_ns, stat.st_size)
            continue
        for folder, _, files in os.walk(root, followlinks=False):
            for file in files:
                path = os.path.join(folder, file)
                if not os.path.islink(path):
                    stat = os.stat(path)
                    seen[path] = (stat.st_mtime_ns, stat.st_size)
    return seen


def clone_result(clone: dict) -> dict:
    """The branches the agent pushed back through the sandbox remote."""
    out = subprocess.run(
        ["git", "-C", clone["repository"], "ls-remote", "--heads", clone["remote"]],
        capture_output=True,
        text=True,
        check=False,
    )
    branches = [
        line.split("refs/heads/", 1)[1]
        for line in out.stdout.splitlines()
        if "refs/heads/" in line
    ]
    result = {"remote": clone["remote"], "branches": branches}
    if out.returncode:
        result["error"] = out.stderr.strip()[:200]
    return result


if __name__ == "__main__":
    main(sys.argv[1])
