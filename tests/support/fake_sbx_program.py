#!/usr/bin/env python3
"""A stand-in for the sbx CLI. It records every call and simulates only what the delegate harness uses.

It cannot prove how Docker sbx behaves; it lets tests drive the real harness code, including its subprocess
handling, without Docker. Output shapes mirror sbx v0.43 (`ls --json`, `policy ls --json`, `policy check --json`).
State lives in a JSON file named by FAKE_SBX_STATE; calls are appended to `calls.jsonl` beside it.
"""

import fcntl
import json
import os
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

STATE = Path(os.environ["FAKE_SBX_STATE"])
CALLS = STATE.with_name("calls.jsonl")
LOCK = STATE.with_name("state.lock")


@contextmanager
def locked():
    with open(LOCK, "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def load():
    return json.loads(STATE.read_text())


def save(state):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(STATE)


def record(**event):
    event["ts"] = time.time()
    with open(CALLS, "a") as handle:
        handle.write(json.dumps(event) + "\n")


def matches(pattern, target):
    host, _, port = target.partition(":")
    port = port or "443"
    pat_host, _, pat_port = pattern.partition(":")
    if pat_port and pat_port != port:
        return False
    if pat_host == "**":
        return True
    if pat_host.startswith("**.") or pat_host.startswith("*."):
        return host.endswith(pat_host.lstrip("*"))
    return host == pat_host


def allowed(state, sandbox, target):
    faults = state.get("faults", [])
    if "denies_backend" in faults and target in state["backend_endpoints"]:
        return False
    if "allows_unlisted" in faults and target == state["canary"]:
        return True
    if "wrong_decision" in faults and target == "pypi.org:443":
        return False
    rules = state["sandboxes"].get(sandbox, {}).get("rules", [])
    hit = lambda decision: any(  # noqa: E731
        r["decision"] == decision and any(matches(p, target) for p in r["resources"])
        for r in rules
    )
    if hit("deny"):
        return False
    if hit("allow"):
        return True
    return state.get("global_default") == "allow-all"


def cmd_ls(args, state):
    print(
        json.dumps(
            {
                "sandboxes": [
                    {
                        "name": name,
                        "agent": "opencode",
                        "status": "running",
                        "workspaces": [m["path"] for m in sb["mounts"]],
                    }
                    for name, sb in state["sandboxes"].items()
                ]
            }
        )
    )


def git(*args, cwd=None):
    subprocess.run(
        ["git", "-c", "user.name=fake", "-c", "user.email=fake@example.invalid", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def cmd_create(args, state):
    rest = args[1:]  # the first positional is the agent name
    paths, opts, i = [], {}, 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--clone":
            opts["clone"] = True
        elif arg in ("--name", "-t", "--cpus", "-m", "--skills"):
            opts[arg] = rest[i + 1]
            i += 1
        elif arg.startswith("-"):
            sys.exit(f"fake sbx: unknown create flag {arg}")
        else:
            paths.append(arg)
        i += 1
    name = opts["--name"]
    if name in state["sandboxes"]:
        sys.exit(f"fake sbx: sandbox {name} already exists")
    mounts = []
    for entry in paths:
        path, _, mode = (
            entry.partition(":") if entry.endswith(":ro") else (entry, "", "rw")
        )
        mounts.append({"path": path, "mode": mode or "rw"})
    rules = []
    if state.get("kit_allow"):
        rules.append(
            {
                "name": f"kit:{name}",
                "decision": "allow",
                "resources": state["kit_allow"],
                "kit": True,
            }
        )
    state["sandboxes"][name] = {
        "mounts": mounts,
        "clone": bool(opts.get("clone")),
        "image": opts.get("-t"),
        "cpus": opts.get("--cpus"),
        "memory": opts.get("-m"),
        "skills": opts.get("--skills"),
        "rules": rules,
    }
    if opts.get("clone"):
        bare = Path(state["clone_dir"]) / f"{name}.git"
        subprocess.run(
            ["git", "init", "-q", "--bare", str(bare)], check=True, capture_output=True
        )
        git("remote", "add", f"sandbox-{name}", str(bare), cwd=mounts[0]["path"])
    print(f"Created sandbox {name}")


def cmd_policy(args, state):
    verb = args[0]
    if verb == "ls":
        sandbox = args[1]
        rules = state["sandboxes"].get(sandbox, {}).get("rules", [])
        print(
            json.dumps(
                {
                    "rules": [
                        {
                            "id": f"rule-{n}",
                            "name": r["name"],
                            "applies_to": f"sandbox:{sandbox}",
                            "resource_type": "network",
                            "decision": r["decision"],
                            "resources": r["resources"],
                            "layer": "local",
                            "editable": not r.get("kit", False),
                        }
                        for n, r in enumerate(rules)
                    ]
                }
            )
        )
    elif verb in ("allow", "deny"):
        sandbox = args[args.index("--sandbox") + 1]
        resources = args[-1].split(",")
        state["sandboxes"][sandbox]["rules"].append(
            {"name": "local", "decision": verb, "resources": resources}
        )
    elif verb == "check":
        sandbox = args[args.index("--sandbox") + 1]
        target = args[-1]
        verdict = allowed(state, sandbox, target)
        print(json.dumps({"allowed": verdict, "target": target}))
        if not verdict:
            sys.exit(
                1
            )  # real sbx exits 1 for a denied target, with the JSON still on stdout
    else:
        sys.exit(f"fake sbx: unsupported policy verb {verb}")


def cmd_exec(args, state):
    envs, workdir, i = [], None, 0
    while args[i].startswith("-"):
        if args[i] == "-e":
            envs.append(args[i + 1])
        elif args[i] == "-w":
            workdir = args[i + 1]
        i += 2
    name, command = args[i], args[i + 1 :]
    if command[0] != "opencode":
        sys.exit(f"fake sbx: exec of {command[0]} is not simulated")
    agent_run(state, name, dict(kv.split("=", 1) for kv in envs), command, workdir)


def agent_run(state, name, env, command, workdir):
    agent = state.get("agent", {})
    running = STATE.with_name("agent.running")

    def stop(signum, frame):
        record(event="agent_stopped", sandbox=name)
        running.unlink(missing_ok=True)
        sys.exit(143)

    signal.signal(signal.SIGTERM, stop)
    record(event="agent_started", sandbox=name, env=env, argv=command, workdir=workdir)
    running.write_text(name)
    print(agent.get("prints", ""), flush=True)
    for created in agent.get("creates", []):
        Path(created["path"]).write_text(created.get("content", "x"))
    if agent.get("commit"):
        bare = Path(state["clone_dir"]) / f"{name}.git"
        work = Path(state["clone_dir"]) / f"{name}-work"
        work.mkdir(exist_ok=True)
        git("init", "-q", "-b", "work", cwd=work)
        (work / "agent.txt").write_text("from the agent")
        git("add", "-A", cwd=work)
        git("commit", "-q", "-m", "agent work", cwd=work)
        git("push", "-q", str(bare), f"work:refs/heads/sandbox/{name}", cwd=work)
    if agent.get("hang") == "forever":
        while True:
            time.sleep(0.05)
    if agent.get("hang") == "release":
        while not Path(state["release_file"]).exists():
            time.sleep(0.05)
    running.unlink(missing_ok=True)
    record(event="agent_finished", sandbox=name, code=agent.get("exit", 0))
    sys.exit(agent.get("exit", 0))


def cmd_remove(args, state):
    name = args[-1]
    state["sandboxes"].pop(name, None)


def main(argv):
    command, args = argv[0], argv[1:]
    record(event="call", command=command, args=args)
    if command == "exec":
        with locked():
            state = load()
        cmd_exec(args, state)
        return
    handlers = {
        "ls": cmd_ls,
        "create": cmd_create,
        "policy": cmd_policy,
        "rm": cmd_remove,
        "stop": lambda a, s: None,
    }
    with locked():
        state = load()
        handlers[command](args, state)
        save(state)


if __name__ == "__main__":
    main(sys.argv[1:])
