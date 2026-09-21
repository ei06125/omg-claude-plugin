"""Run directories, the audit line and the tool log. All of it lives outside every mounted volume."""

import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path


def state_dir(env: dict, home: Path) -> Path:
    if env.get("OMG_DELEGATE_STATE_DIR"):
        return Path(env["OMG_DELEGATE_STATE_DIR"])
    base = Path(env.get("XDG_STATE_HOME") or home / ".local" / "state")
    return base / "omg" / "delegate"


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def write_private(path: Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(text)


def write_json(path: Path, data: dict) -> None:
    write_private(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def append_private(path: Path, line: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a") as handle:
        handle.write(line + "\n")


def audit(directory: Path, line: dict) -> None:
    """One append-only line per call. It never holds the task text or the agent output."""
    append_private(directory / "audit.jsonl", json.dumps(line, sort_keys=True))


def task_hash(task: str) -> str:
    return hashlib.sha256(task.encode()).hexdigest()


def logger(directory: Path) -> logging.Logger:
    log = logging.getLogger(f"omg_delegate:{directory}")
    if not log.handlers:
        handler = logging.FileHandler(directory / "tool.log")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(handler)
        log.setLevel(logging.INFO)
        log.propagate = False
        os.chmod(directory / "tool.log", 0o600)
    return log
