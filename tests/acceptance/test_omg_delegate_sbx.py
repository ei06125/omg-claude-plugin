"""Criterion 19: the boundary against a real Docker sbx and a real backend. Local only, tagged @sbx.

A model is not deterministic, so the agent command is replaced by a probe script through the guardrail
configuration. The probe runs inside the real sandbox; the tests read what it printed and what reached the host.
"""

import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest
from omg_delegate.harness import delegate
from pytest_bdd import given, parsers, scenarios, then, when
from support.git_repo import Repo

scenarios("omg-delegate-sbx.feature")

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARDRAILS = REPO_ROOT / "configs" / "delegate" / "guardrails.json"
RUN_SECONDS = 300


def wait_for(predicate, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(1)
    return predicate()


@pytest.fixture
def world(tmp_path):
    state = {"tmp": tmp_path, "sandboxes": []}
    yield state
    for pid_file in (tmp_path / "state").glob("runs/*/supervisor.pid"):
        with contextlib.suppress(ProcessLookupError, ValueError, PermissionError):
            os.killpg(int(pid_file.read_text()), signal.SIGTERM)
    for name in state["sandboxes"]:
        subprocess.run(["sbx", "rm", "--force", name], capture_output=True, check=False)


def run_probe(world, probe, volumes, keep=False):
    config = json.loads(GUARDRAILS.read_text())
    config["agent_command"] = ["sh", "-c", probe]
    config["limits"]["timeout_seconds"] = {
        "default": RUN_SECONDS,
        "maximum": RUN_SECONDS,
    }
    (world["tmp"] / "guardrails.json").write_text(json.dumps(config))
    env = {
        **os.environ,
        "OMG_DELEGATE_CONFIG": str(world["tmp"] / "guardrails.json"),
        "OMG_DELEGATE_STATE_DIR": str(world["tmp"] / "state"),
    }
    request = {
        "task": "probe",
        "volumes": volumes,
        "backend": "ollama",
        "model": "gemma4:12b",
        "keep": keep,
    }
    world["response"] = delegate(request, env=env)
    assert world["response"]["status"] == "started", world["response"]
    world["sandboxes"].append(world["response"]["sandbox"])
    world["run_dir"] = Path(world["response"]["run_dir"])
    completion = world["run_dir"] / "completion.json"
    assert wait_for(completion.exists, RUN_SECONDS), (
        f"the run did not end: {world['run_dir']}"
    )
    world["completion"] = json.loads(completion.read_text())
    world["log"] = (world["run_dir"] / "agent.log").read_text()


def printed(world, key):
    match = re.search(rf"^{key}=(\S*)$", world["log"], re.MULTILINE)
    assert match, f"the probe printed no {key}; log:\n{world['log']}"
    return match.group(1)


@given(
    parsers.re(
        r'a real sbx and a running "(?P<backend>[^"]+)" backend serving "(?P<model>[^"]+)"'
    ),
)
def given_real_environment(world, backend, model):
    assert shutil.which("sbx"), "sbx is not installed"
    with urllib.request.urlopen("http://127.0.0.1:11434/v1/models", timeout=5) as reply:
        ids = [m["id"] for m in json.load(reply)["data"]]
    assert model in ids, f"{backend} does not serve {model}: {ids}"
    check = subprocess.run(
        ["sbx", "policy", "check", "network", "--json", "example.com:443"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert not json.loads(check.stdout)["allowed"], (
        "the global sbx policy allows everything; run `sbx policy init deny-all`"
    )


@given("a synthetic read-only volume and a synthetic read-write volume")
def given_two_volumes(world):
    world["ro"], world["rw"] = world["tmp"] / "ro", world["tmp"] / "rw"
    for folder in (world["ro"], world["rw"]):
        folder.mkdir()
        (folder / "seed.txt").write_text("seed\n")


@given("a synthetic read-write volume")
def given_rw_volume(world):
    world["rw"] = world["tmp"] / "rw"
    world["rw"].mkdir()
    (world["rw"] / "seed.txt").write_text("seed\n")


@given("a synthetic git repository")
def given_repo(world):
    world["repo"] = Repo(world["tmp"] / "repo")
    world["repo"].write("README.md", "repo\n")
    world["repo"].commit("initial")
    world["head"] = world["repo"].git("rev-parse", "HEAD")


@when("I delegate a probe that writes to both volumes")
def when_probe_writes(world):
    ro, rw = world["ro"], world["rw"]
    probe = f"touch {ro}/probe.txt 2>/dev/null; echo ro_write_rc=$?; touch {rw}/probe.txt; echo rw_write_rc=$?"
    run_probe(
        world,
        probe,
        [{"host_path": str(rw), "mode": "rw"}, {"host_path": str(ro), "mode": "ro"}],
    )


@when("I delegate a probe that requests an unlisted host and the backend")
def when_probe_requests(world):
    probe = (
        'echo unlisted_http=$(curl -s -m 15 -o /dev/null -w "%{http_code}" https://example.com); '
        'echo backend_http=$(curl -s -m 15 -o /dev/null -w "%{http_code}" http://host.docker.internal:11434/api/version)'
    )
    run_probe(world, probe, [{"host_path": str(world["rw"]), "mode": "rw"}])


@when("I delegate a probe that commits a file in the clone")
def when_probe_commits(world):
    probe = (
        "git config user.email probe@example.invalid; git config user.name probe; "
        "echo hello > probe.txt; git add probe.txt; git commit -q -m 'probe commit'; echo commit_rc=$?"
    )
    run_probe(
        world,
        probe,
        [{"host_path": str(world["repo"].path), "mode": "clone"}],
        keep=True,
    )


@then("the write to the read-only volume failed")
def then_ro_failed(world):
    assert printed(world, "ro_write_rc") != "0"
    assert not (world["ro"] / "probe.txt").exists()


@then("the write to the read-write volume succeeded")
def then_rw_succeeded(world):
    assert printed(world, "rw_write_rc") == "0"
    assert (world["rw"] / "probe.txt").exists()


@then("the unlisted host was blocked")
def then_unlisted_blocked(world):
    assert printed(world, "unlisted_http") == "403"


@then("the backend answered")
def then_backend_answered(world):
    assert printed(world, "backend_http") == "200"


@then("the repository has the sandbox remote with that commit")
def then_clone_commit(world):
    clone = world["completion"]["clone"]
    assert clone["branches"], f"no branch came back through {clone['remote']}: {clone}"
    repo = world["repo"]
    repo.git("fetch", "-q", clone["remote"], clone["branches"][0])
    assert repo.git("log", "-1", "--format=%s", "FETCH_HEAD") == "probe commit"


@then("the working tree of the repository is unchanged")
def then_tree_unchanged(world):
    repo = world["repo"]
    assert repo.git("rev-parse", "HEAD") == world["head"]
    assert repo.git("status", "--porcelain") == ""
