"""The delegate entrypoint. It validates, prepares and proves the sandbox, starts a supervisor and returns.

The call is fire and forget: the agent runs under a detached supervisor, and the result appears where the work
lands (mounted files, a clone's branch) plus a completion record in the run directory.
"""

import json
import os
import subprocess
import sys
import uuid
from dataclasses import asdict
from pathlib import Path

from . import backends, boundary, records, render
from .config import Config
from .models import Refusal, Request, Run, Volume
from .network import forbidden_allow, rules
from .sbx import Sbx, SbxError
from .validate import parse
from .volumes import check_volumes

PACKAGE_PARENT = str(Path(__file__).resolve().parents[1])


def delegate(request: dict, env: dict | None = None) -> dict:
    env = dict(os.environ if env is None else env)
    home = Path(env.get("HOME") or Path.home())
    config = Config.load(env, home)
    directory = records.private_dir(records.state_dir(env, home))
    log = records.logger(directory)
    run_id = uuid.uuid4().hex[:12]
    log.info("call %s", run_id)
    applied: dict = {}
    try:
        response = _start(request, env, config, directory, run_id, log, applied)
    except Refusal as refusal:
        log.info("call %s refused: %s", run_id, refusal.reason)
        response = refusal.as_response(run_id)
    records.audit(directory, _audit_line(run_id, request, response, applied))
    return response


def _start(request, env, config, directory, run_id, log, applied) -> dict:
    req = parse(request, config)
    if message := check_volumes(req.volumes, config):
        raise Refusal("forbidden_volume", message)
    for policy in req.network:
        if policy.action == "allow" and (
            message := forbidden_allow(policy.host, config, req.backend)
        ):
            raise Refusal("forbidden_network", message)
    backends.require(config, req.backend, req.model)
    sbx = Sbx(env.get("OMG_DELEGATE_SBX", "sbx"), env, log)
    name = req.name or f"omg-delegate-{run_id}"
    volumes = [Volume(os.path.realpath(v.host_path), v.mode) for v in req.volumes]
    try:
        if name in sbx.sandboxes():
            raise Refusal(
                "sandbox_exists",
                f"a sandbox named {name!r} already exists; it was left untouched",
            )
        run_dir = records.private_dir(directory / "runs" / run_id)
        _write_request(run_dir, run_id, req, volumes)
        planned = _prepare_sandbox(sbx, name, req, volumes, config, applied)
    except SbxError as error:
        raise Refusal("sandbox_failed", str(error)) from error
    log.info("call %s: sandbox %s verified", run_id, name)
    run = _agent_run(sbx, name, req, volumes, config, directory)
    records.write_json(run_dir / "run.json", asdict(run))
    records.write_json(
        run_dir / "applied.json",
        {
            "sandbox": name,
            "image": config.image,
            "cpus": config.cpus,
            "memory_mib": config.memory_mib,
            "volumes": [asdict(v) for v in volumes],
            "network": applied["network"],
            "agent": {
                "model": f"{req.backend}/{config.served_id(req.backend, req.model)}",
                "workdir": run.workdir,
            },
            "clone": run.clone,
        },
    )
    _spawn(run_dir, req.task, env)
    log.info("call %s: supervisor started", run_id)
    return {
        "status": "started",
        "run_id": run_id,
        "sandbox": name,
        "backend": req.backend,
        "model": req.model,
        "run_dir": str(run_dir),
        "volumes": [asdict(v) for v in volumes],
        "network": [{"action": "allow", "host": h} for h in planned.allow]
        + [{"action": "deny", "host": h} for h in planned.deny],
        "results": {"rw_paths": run.rw_paths, "clone": run.clone},
    }


def _write_request(
    run_dir: Path, run_id: str, req: Request, volumes: list[Volume]
) -> None:
    records.write_json(
        run_dir / "request.json",
        {
            "run_id": run_id,
            "time": records.now(),
            "backend": req.backend,
            "model": req.model,
            "volumes": [asdict(v) for v in volumes],
            "network": [asdict(p) for p in req.network],
            "commands": req.commands,
            "timeout_seconds": req.timeout_seconds,
            "name": req.name,
            "keep": req.keep,
            "task_sha256": records.task_hash(req.task),
        },
    )


def _prepare_sandbox(
    sbx: Sbx,
    name: str,
    req: Request,
    volumes: list[Volume],
    config: Config,
    applied: dict,
):
    """Create the sandbox, shape its network and prove the boundary. Remove it again if anything fails."""
    try:
        sbx.create(name, volumes, config.image, config.cpus, config.memory_mib)
    except SbxError:
        sbx.remove(name)
        raise
    try:
        planned = rules(req.network, req.backend, sbx.kit_hosts(name), config)
        applied["network"] = {"allow": planned.allow, "deny": planned.deny}
        sbx.deny(name, planned.deny)
        sbx.allow(name, planned.allow)
        failure = boundary.verify(sbx, name, config, planned)
        if failure:
            raise Refusal("boundary_check_failed", failure, sandbox=name)
    except SbxError as error:
        sbx.remove(name)
        raise Refusal("sandbox_failed", str(error), sandbox=name) from error
    except Refusal:
        sbx.remove(name)
        raise
    return planned


def _agent_run(
    sbx: Sbx,
    name: str,
    req: Request,
    volumes: list[Volume],
    config: Config,
    directory: Path,
) -> Run:
    endpoint = config.backends[req.backend].endpoint
    model_id = config.served_id(req.backend, req.model)
    is_clone = volumes[0].mode == "clone"
    workdir = None if is_clone else volumes[0].host_path
    argv = ["opencode", "run", "--pure", "-m", f"{req.backend}/{model_id}"]
    if workdir:
        argv += ["--dir", workdir]
    if config.agent_command:
        argv = list(
            config.agent_command
        )  # a probe for the real-sandbox check; only the server's configuration sets it
    agent_config = render.agent_config(
        req.backend, model_id, endpoint, volumes, req.commands
    )
    return Run(
        sbx=sbx.executable,
        sandbox=name,
        agent_argv=argv,
        agent_env={"OPENCODE_CONFIG_CONTENT": json.dumps(agent_config)},
        workdir=workdir,
        timeout_seconds=req.timeout_seconds,
        keep=req.keep,
        rw_paths=[v.host_path for v in volumes if v.mode == "rw"],
        clone={"repository": volumes[0].host_path, "remote": f"sandbox-{name}"}
        if is_clone
        else None,
        state_dir=str(directory),
    )


def _spawn(run_dir: Path, task: str, env: dict) -> None:
    """Start the supervisor detached. The task goes through stdin so it is never written to disk."""
    child_env = {
        **env,
        "PYTHONPATH": os.pathsep.join(
            filter(None, [PACKAGE_PARENT, env.get("PYTHONPATH")])
        ),
    }
    with open(run_dir / "supervisor.err", "ab") as errors:
        proc = subprocess.Popen(
            [sys.executable, "-m", "omg_delegate.supervisor", str(run_dir)],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=errors,
            env=child_env,
            start_new_session=True,
        )
    records.write_private(run_dir / "supervisor.pid", str(proc.pid))
    proc.stdin.write(task.encode())
    proc.stdin.close()


def _audit_line(run_id: str, request: object, response: dict, applied: dict) -> dict:
    asked = request if isinstance(request, dict) else {}
    volumes = asked.get("volumes")
    line = {
        "run_id": run_id,
        "time": records.now(),
        "backend": asked.get("backend"),
        "model": asked.get("model"),
        "volumes": [
            {"host_path": v.get("host_path"), "mode": v.get("mode")}
            for v in (volumes if isinstance(volumes, list) else [])
            if isinstance(v, dict)
        ],
        "network": applied.get("network", asked.get("network", [])),
        "outcome": response["status"],
    }
    if response["status"] == "refused":
        line["reason"] = response["reason"]
    return line
