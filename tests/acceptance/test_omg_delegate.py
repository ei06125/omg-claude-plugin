import contextlib
import hashlib
import json
import os
import re
import signal
import time
from pathlib import Path

import anyio
import pytest
import yaml
from mcp import Client, StdioServerParameters
from pytest_bdd import given, parsers, scenarios, then, when
from support import guardrails
from support.fake_backend import FakeBackend, closed_url
from support.fake_sbx import CANARY_HOST, FakeSbx
from support.git_repo import Repo
from support.guardrails import ENDPOINTS

scenarios("omg-delegate.feature")

REPO_ROOT = Path(__file__).resolve().parents[2]
WAIT_SECONDS = 20


def quoted(text):
    return re.findall(r'"([^"]*)"', text)


def wait_for(predicate, seconds=WAIT_SECONDS):
    deadline = time.time() + seconds
    while time.time() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    return predicate()


@pytest.fixture
def world(tmp_path):
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    (home / ".aws").mkdir()
    socket_file = tmp_path / "docker.sock"
    socket_file.write_text("")
    state_dir = tmp_path / "state"
    state = {
        "tmp": tmp_path,
        "home": home,
        "socket": socket_file,
        "state_dir": state_dir,
        "config_path": tmp_path / "guardrails.json",
        "backends": {},
        "probe_urls": {name: closed_url() for name in ENDPOINTS},
        "image": "sandbox-image@sha256:feedface",
        "cpus": 2,
        "memory_mib": 2048,
        "extra_env": {},
        "requested_allows": [],
        "kit_allow": [],
        "response": None,
        "backend": "ollama",
    }
    yield state
    for backend in state["backends"].values():
        backend.stop()
    sbx = state.get("sbx")
    if sbx:
        sbx.release()
    for pid_file in state_dir.glob("runs/*/supervisor.pid"):
        with contextlib.suppress(ProcessLookupError, ValueError, PermissionError):
            os.killpg(int(pid_file.read_text()), signal.SIGTERM)


def write_config(world):
    config = guardrails.build(
        world["socket"],
        world["probe_urls"],
        image=world["image"],
        cpus=world["cpus"],
        memory_mib=world["memory_mib"],
        canary_host=CANARY_HOST,
    )
    world["config_path"].write_text(json.dumps(config))


def build_env(world):
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(world["home"]),
        "LANG": "C.UTF-8",
        "PYTHONPATH": str(REPO_ROOT / "sources"),
        "OMG_DELEGATE_CONFIG": str(world["config_path"]),
        "OMG_DELEGATE_STATE_DIR": str(world["state_dir"]),
        **world["sbx"].env(),
        **world["extra_env"],
    }
    return env


def default_request(world):
    return {
        "task": "summarise the workspace",
        "volumes": [{"host_path": str(world["workspace"]), "mode": "rw"}],
        "backend": "ollama",
        "model": "qwen3.8:27b-mlx",
    }


def run_delegate(world, **overrides):
    from omg_delegate.harness import delegate

    write_config(world)
    world["sbx"].update(
        kit_allow=world["kit_allow"],
        backend_endpoints=list(ENDPOINTS.values()),
    )
    request = {**default_request(world), **overrides}
    world["request"] = request
    world["backend"] = request.get("backend")
    world["response"] = delegate(request, env=build_env(world))
    if world["response"].get("run_dir"):
        world["run_dir"] = Path(world["response"]["run_dir"])


def response(world):
    assert world["response"] is not None, "delegate was never called"
    return world["response"]


def sandbox_of(world):
    return response(world)["sandbox"]


def run_ends(world):
    completion = world["run_dir"] / "completion.json"
    assert wait_for(completion.exists), f"no completion.json in {world['run_dir']}"
    world["completion"] = json.loads(completion.read_text())
    return world["completion"]


def completion_of(world):
    return world.get("completion") or run_ends(world)


def agent_config(world):
    started = wait_for(lambda: world["sbx"].events("agent_started"))
    assert started, "the agent was never started"
    return json.loads(started[0]["env"]["OPENCODE_CONFIG_CONTENT"])


def local_rules(world):
    sandbox = world["sbx"].sandbox(sandbox_of(world))
    return [r for r in sandbox["rules"] if not r.get("kit")]


def check(world, target):
    import subprocess

    out = subprocess.run(
        [
            str(world["sbx"].executable),
            "policy",
            "check",
            "network",
            "--sandbox",
            sandbox_of(world),
            "--json",
            target,
        ],
        capture_output=True,
        text=True,
        env={**os.environ, **world["sbx"].env()},
        check=False,
    ).stdout
    return json.loads(out)["allowed"]


def audit_lines(world):
    path = world["state_dir"] / "audit.jsonl"
    return (
        [json.loads(line) for line in path.read_text().splitlines()]
        if path.exists()
        else []
    )


def run_files_text(world):
    return "\n".join(
        p.read_text(errors="replace")
        for p in world["run_dir"].rglob("*")
        if p.is_file()
    )


# --- Background and Given ---------------------------------------------------------------------------------


@given("a fake sbx program that records every call")
def given_fake_sbx(world):
    world["sbx"] = FakeSbx(world["tmp"])


@given(parsers.re(r'a fake "(?P<backend>[^"]+)" backend serving "(?P<model>[^"]+)"'))
def given_fake_backend(world, backend, model):
    fake = FakeBackend([model]).start()
    world["backends"][backend] = fake
    world["probe_urls"][backend] = fake.probe_url


@given("a synthetic workspace directory")
def given_workspace(world):
    world["workspace"] = world["tmp"] / "workspace"
    world["workspace"].mkdir()
    (world["workspace"] / "README.md").write_text("synthetic\n")


@given(parsers.re(r'the "(?P<backend>[^"]+)" backend is not running'))
def given_backend_down(world, backend):
    world["probe_urls"][backend] = closed_url()


@given(parsers.re(r'the "(?P<backend>[^"]+)" backend serves only "(?P<model>[^"]+)"'))
def given_backend_serves_only(world, backend, model):
    world["backends"][backend].models = [model]


@given("a synthetic documentation directory")
def given_docs(world):
    world["docs"] = world["tmp"] / "docs"
    world["docs"].mkdir()
    (world["docs"] / "guide.md").write_text("guide\n")


@given("a synthetic git repository")
def given_repo(world):
    world["repo"] = Repo(world["tmp"] / "repo")
    world["repo"].write("README.md", "repo\n")
    world["repo"].commit("initial")


@given(
    parsers.re(
        r'the guardrail configuration pins the image "(?P<image>[^"]+)" and limits sandboxes to '
        r"(?P<cpus>\d+) CPUs and (?P<mem>\d+) MiB"
    )
)
def given_limits(world, image, cpus, mem):
    world.update(image=image, cpus=int(cpus), memory_mib=int(mem))


@given(parsers.re(r"the agent kit allows (?P<hosts>.+) by default"))
def given_kit(world, hosts):
    world["kit_allow"] = quoted(hosts)


FAULTS = {
    "reports the global default as allow-all": lambda sbx: sbx.update(
        global_default="allow-all"
    ),
    "allows an unlisted host": lambda sbx: sbx.add_fault("allows_unlisted"),
    "denies the backend endpoint": lambda sbx: sbx.add_fault("denies_backend"),
    "gives a requested allow rule the wrong decision": lambda sbx: sbx.add_fault(
        "wrong_decision"
    ),
}


@given(parsers.re(r"the sbx program (?P<fault>.+)"))
def given_fault(world, fault):
    FAULTS[fault](world["sbx"])


@given("the agent keeps running until released")
def given_agent_release(world):
    world["sbx"].script_agent(hang="release")


@given(
    parsers.re(r'the agent prints "(?P<text>[^"]*)" and exits with code (?P<code>\d+)')
)
def given_agent_prints(world, text, code):
    world["sbx"].script_agent(prints=text, exit=int(code))


@given(parsers.re(r'the agent prints "(?P<text>[^"]*)" and then keeps running'))
def given_agent_hangs(world, text):
    world["sbx"].script_agent(prints=text, hang="forever")


@given("the agent finishes normally")
def given_agent_finishes(world):
    world["sbx"].script_agent(exit=0)


@given(parsers.re(r"the agent exits with code (?P<code>\d+)"))
def given_agent_exits(world, code):
    world["sbx"].script_agent(exit=int(code))


@given("the agent keeps running past the timeout")
def given_agent_past_timeout(world):
    world["sbx"].script_agent(hang="forever")


@given(
    parsers.re(
        r'the agent creates the file "(?P<a>[^"]+)" in the workspace and the file "(?P<b>[^"]+)" in the '
        r"documentation, then exits with code (?P<code>\d+)"
    )
)
def given_agent_creates(world, a, b, code):
    world["sbx"].script_agent(
        creates=[
            {"path": str(world["workspace"] / a), "content": "new"},
            {"path": str(world["docs"] / b), "content": "new"},
        ],
        exit=int(code),
    )


@given(parsers.re(r"the agent commits to its clone and exits with code (?P<code>\d+)"))
def given_agent_commits(world, code):
    world["sbx"].script_agent(commit=True, exit=int(code))


@given(parsers.re(r'a sandbox named "(?P<name>[^"]+)" already exists'))
def given_existing_sandbox(world, name):
    state = world["sbx"].state()
    state["sandboxes"][name] = {"mounts": [], "rules": []}
    world["sbx"].update(sandboxes=state["sandboxes"])


@given(parsers.re(r'the host environment sets "(?P<var>[^"]+)" to "(?P<value>[^"]+)"'))
def given_env(world, var, value):
    world["extra_env"][var] = value


# --- When ---------------------------------------------------------------------------------------------------


@when("I delegate with the default arguments")
def when_default(world):
    run_delegate(world)


@when(parsers.re(r"I delegate with (?P<pairs>(?:\w+ \"[^\"]*\"(?: and )?)+)$"))
def when_pairs(world, pairs):
    overrides = {}
    for name, value in re.findall(r'(\w+) "([^"]*)"', pairs):
        if name == "timeout_seconds":
            overrides[name] = int(value)
        elif name == "keep":
            overrides[name] = value == "true"
        elif name == "commands":
            overrides[name] = [value]
        else:
            overrides[name] = value
    run_delegate(world, **overrides)


@when(
    parsers.re(
        r'I delegate with the network policy "(?P<action>[^"]+)" "(?P<host>[^"]+)"'
    )
)
def when_policy(world, action, host):
    if action == "allow":
        world["requested_allows"].append(host)
    run_delegate(world, network=[{"action": action, "host": host}])


@when(parsers.re(r"I delegate with a volume that is (?P<kind>.+)"))
def when_volume(world, kind):
    tmp, home = world["tmp"], world["home"]
    workspace = str(world["workspace"])
    link = world["workspace"] / "link-to-credentials"
    link.symlink_to(home / ".ssh")
    plain = {
        "a relative path": "docs/notes",
        "a path that does not exist": str(tmp / "does-not-exist"),
        "the home directory": str(home),
        "the parent of the home directory": str(home.parent),
        "the credentials directory": str(home / ".ssh"),
        "the container runtime socket": str(world["socket"]),
        "a symlink that points to the credentials directory": str(link),
    }
    if kind in plain:
        volumes = [{"host_path": plain[kind], "mode": "rw"}]
    elif kind == "a clone of a directory that is not a git repository":
        volumes = [{"host_path": workspace, "mode": "clone"}]
    elif kind == "a clone that is not the first volume":
        repo = Repo(tmp / "clone-src")
        repo.write("a.txt", "a")
        repo.commit("a")
        volumes = [
            {"host_path": workspace, "mode": "rw"},
            {"host_path": str(repo.path), "mode": "clone"},
        ]
    else:
        raise AssertionError(f"unknown volume kind: {kind}")
    run_delegate(world, volumes=volumes)


@when(
    parsers.re(
        r'I delegate with the workspace in mode "(?P<ws>[^"]+)" and the documentation in mode "(?P<docs>[^"]+)"'
    )
)
def when_two_volumes(world, ws, docs):
    run_delegate(
        world,
        volumes=[
            {"host_path": str(world["workspace"]), "mode": ws},
            {"host_path": str(world["docs"]), "mode": docs},
        ],
    )


@when(parsers.re(r'I delegate with the repository as a "(?P<mode>[^"]+)" volume'))
def when_repo_volume(world, mode):
    run_delegate(world, volumes=[{"host_path": str(world["repo"].path), "mode": mode}])


@when("I release the agent")
def when_release(world):
    wait_for(lambda: world["sbx"].running())
    world["sbx"].release()


@when("the run ends")
def when_run_ends(world):
    run_ends(world)


@when("I discover the tools on that server")
def when_discover(world):
    server = world["server"]
    params = StdioServerParameters(
        command=server["command"],
        args=[
            a.replace("${CLAUDE_PLUGIN_ROOT}", str(REPO_ROOT))
            for a in server.get("args", [])
        ],
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "sources")},
        cwd=str(REPO_ROOT),
    )

    async def list_tools():
        async with Client(params) as client:
            return (await client.list_tools()).tools

    world["tools"] = anyio.run(list_tools)


# --- Then: structure ----------------------------------------------------------------------------------------


@given(
    parsers.re(r'the MCP server registered in "(?P<file>[^"]+)"'),
    target_fixture="server",
)
def given_server(world, file):
    servers = json.loads((REPO_ROOT / file).read_text())["mcpServers"]
    assert servers, f"{file} registers no MCP server"
    world["server"] = next(iter(servers.values()))
    return world["server"]


@then(parsers.re(r'the tool "(?P<name>[^"]+)" is listed'))
def then_tool_listed(world, name):
    tools = {t.name: t for t in world["tools"]}
    assert name in tools, f"tools listed: {sorted(tools)}"
    world["tool"] = tools[name]


def resolve(schema, root):
    while "$ref" in schema:
        schema = root["$defs"][schema["$ref"].rsplit("/", 1)[-1]]
    return schema


def property_schema(tool, name):
    root = tool.input_schema if hasattr(tool, "input_schema") else tool.inputSchema
    return root, resolve(root["properties"][name], root)


@then(parsers.re(r"its input schema names (?P<names>.+)"))
def then_schema_names(world, names):
    root, _ = property_schema(world["tool"], quoted(names)[0])
    for name in quoted(names):
        assert name in root["properties"], (
            f"{name} missing from {sorted(root['properties'])}"
        )


def is_enum(schema, root):
    schema = resolve(schema, root)
    return "enum" in schema or any(
        "enum" in resolve(s, root) for s in schema.get("anyOf", [])
    )


@then('its input schema restricts "backend", "model" and the volume "mode" to enums')
def then_schema_enums(world):
    root, _ = property_schema(world["tool"], "backend")
    assert is_enum(root["properties"]["backend"], root)
    assert is_enum(root["properties"]["model"], root)
    volumes = resolve(root["properties"]["volumes"], root)
    item = resolve(volumes["items"], root)
    assert is_enum(item["properties"]["mode"], root)


def read_skill(name):
    text = (REPO_ROOT / ".claude" / "skills" / name / "SKILL.md").read_text()
    _, front, body = text.split("---", 2)
    return {"front": yaml.safe_load(front), "body": " ".join(body.split()).lower()}


@given(parsers.re(r'the "(?P<name>[^"]+)" skill'), target_fixture="skill")
def given_skill(name):
    return read_skill(name)


@then("the model can invoke it on its own")
def then_model_invokes(skill):
    assert not skill["front"].get("disable-model-invocation", False)


@then(
    parsers.re(
        r'its instructions tell the caller to pass the arguments to the "(?P<tool>[^"]+)" tool unchanged'
    )
)
def then_skill_passes(skill, tool):
    assert tool in skill["body"] and "unchanged" in skill["body"]


@then(
    "its instructions tell the caller to ask for a missing required argument and never to invent one"
)
def then_skill_asks(skill):
    assert (
        "ask" in skill["body"]
        and "missing required" in skill["body"]
        and "never invent" in skill["body"]
    )


@then(
    'its instructions tell the caller to choose the smallest set of directories and to use "ro" unless the task must write'
)
def then_skill_minimal(skill):
    assert "smallest set of directories" in skill["body"]
    assert '"ro"' in skill["body"] and "unless the task must write" in skill["body"]


# --- Then: refusals -----------------------------------------------------------------------------------------


@then(
    parsers.re(
        r'the result status is "(?P<status>[^"]+)" with reason "(?P<reason>[^"]+)"'
    )
)
def then_refused(world, status, reason):
    assert (response(world)["status"], response(world).get("reason")) == (
        status,
        reason,
    ), response(world)


@then(parsers.re(r'the result status is "(?P<status>[^"]+)"$'))
def then_status(world, status):
    assert response(world)["status"] == status, response(world)


@then("the refusal lists the supported values")
def then_supported(world):
    supported = response(world)["supported"]
    assert supported["backends"] and supported["models"] and supported["pairs"]


@then("no sandbox was created")
def then_no_sandbox(world):
    assert not world["sbx"].commands("create")


@then(parsers.re(r'the hint says to start "(?P<backend>[^"]+)"'))
def then_hint_start(world, backend):
    assert response(world)["hint"]["start"] == backend


@then(
    parsers.re(
        r'the hint lists "(?P<backend>[^"]+)" "(?P<model>[^"]+)" as currently served'
    )
)
def then_hint_served(world, backend, model):
    assert {"backend": backend, "model": model} in response(world)["hint"]["served"]


@then("no agent was started")
def then_no_agent(world):
    time.sleep(0.3)
    assert not world["sbx"].events("agent_started")


# --- Then: sandbox construction -----------------------------------------------------------------------------


def create_args(world):
    calls = world["sbx"].commands("create")
    assert calls, "sbx create was never called"
    return calls[0]["args"]


def flag_value(args, flag):
    return args[args.index(flag) + 1]


@then(
    parsers.re(r'sbx was asked to create a sandbox from the image "(?P<image>[^"]+)"')
)
def then_image(world, image):
    assert flag_value(create_args(world), "-t") == image


@then("shared skills are off for the sandbox")
def then_skills_off(world):
    assert flag_value(create_args(world), "--skills") == "off"


@then(parsers.re(r"the sandbox has (?P<cpus>\d+) CPUs and (?P<mem>\d+) MiB of memory"))
def then_limits(world, cpus, mem):
    args = create_args(world)
    assert flag_value(args, "--cpus") == cpus and flag_value(args, "-m") == f"{mem}m"


@then("the first mount of the sandbox is the workspace, writable")
def then_first_mount(world):
    mounts = world["sbx"].sandbox(sandbox_of(world))["mounts"]
    assert mounts[0] == {"path": str(world["workspace"]), "mode": "rw"}


@then("the documentation is mounted read-only")
def then_docs_ro(world):
    mounts = world["sbx"].sandbox(sandbox_of(world))["mounts"]
    assert {"path": str(world["docs"]), "mode": "ro"} in mounts


@then("sbx was asked to create the sandbox as a clone of the repository")
def then_clone(world):
    args = create_args(world)
    assert "--clone" in args and str(world["repo"].path) in args


@then("the start response names the sandbox remote for the results")
def then_clone_remote(world):
    assert (
        response(world)["results"]["clone"]["remote"] == f"sandbox-{sandbox_of(world)}"
    )


# --- Then: network rules ------------------------------------------------------------------------------------


@then(parsers.re(r'the rules applied to the sandbox allow "(?P<host>[^"]+)"$'))
def then_allow(world, host):
    assert check(world, host), f"{host} is not allowed"


@then(
    parsers.re(
        r"the rules applied to the sandbox deny (?P<hosts>\"[^\"]+\"(?: and \"[^\"]+\")*)$"
    )
)
def then_deny(world, hosts):
    denied = {
        h for r in local_rules(world) if r["decision"] == "deny" for h in r["resources"]
    }
    for host in quoted(hosts):
        assert host in denied and not check(world, host), (
            f"{host} is not explicitly denied"
        )


@then(parsers.re(r'the rules applied to the sandbox do not deny "(?P<host>[^"]+)"'))
def then_not_deny(world, host):
    denied = {
        h for r in local_rules(world) if r["decision"] == "deny" for h in r["resources"]
    }
    assert host not in denied


@then("the rules applied to the sandbox allow nothing else")
def then_allow_nothing_else(world):
    allowed = {
        h
        for r in local_rules(world)
        if r["decision"] == "allow"
        for h in r["resources"]
    }
    endpoint = ENDPOINTS[world["backend"]]
    local = endpoint.replace("host.docker.internal", "localhost")
    assert allowed == {endpoint, local, *world["requested_allows"]}


# --- Then: boundary and agent -------------------------------------------------------------------------------


@then("the sandbox was removed")
def then_removed(world):
    name = sandbox_of(world) if response(world).get("sandbox") else None
    assert wait_for(
        lambda: [c for c in world["sbx"].commands("rm") if name in c["args"]]
    ), "sandbox never removed"


@then("the boundary checks were made before the agent was started")
def then_checks_first(world):
    started = wait_for(lambda: world["sbx"].events("agent_started"))
    checks = [c for c in world["sbx"].commands("policy") if "check" in c["args"]]
    assert checks and started and max(c["ts"] for c in checks) < started[0]["ts"]


@then("the checks covered an unlisted host and the backend endpoint")
def then_checks_covered(world):
    targets = [
        c["args"][-1] for c in world["sbx"].commands("policy") if "check" in c["args"]
    ]
    assert CANARY_HOST in targets and ENDPOINTS["ollama"] in targets


@then(
    parsers.re(
        r'the agent was started with the model "(?P<model>[^"]+)" and the endpoint "(?P<endpoint>[^"]+)"'
    )
)
def then_agent_model(world, model, endpoint):
    config = agent_config(world)
    assert config["model"] == f"{world['backend']}/{model}"
    assert endpoint in config["provider"][world["backend"]]["options"]["baseURL"]


@then("the agent may edit files inside the workspace")
def then_edit_inside(world):
    edit = agent_config(world)["permission"]["edit"]
    rooted = str(world["workspace"]).lstrip("/")
    assert any(v == "allow" and rooted in k for k, v in edit.items())


@then("the agent may not edit files anywhere else")
def then_edit_elsewhere(world):
    edit = agent_config(world)["permission"]["edit"]
    assert edit["*"] == "deny"
    assert not any(
        v == "allow" and str(world["docs"]).lstrip("/") in k for k, v in edit.items()
    )


@then("the agent may run no shell command")
def then_no_shell(world):
    bash = agent_config(world)["permission"]["bash"]
    assert bash == "deny" or bash == {"*": "deny"}


@then("the agent may not fetch web pages")
def then_no_web(world):
    assert agent_config(world)["permission"]["webfetch"] == "deny"


@then(parsers.re(r'the agent may run the shell command "(?P<command>[^"]+)"'))
def then_shell_allowed(world, command):
    assert agent_config(world)["permission"]["bash"][command] == "allow"


@then("the agent may not run any other shell command")
def then_shell_default_deny(world):
    assert agent_config(world)["permission"]["bash"]["*"] == "deny"


# --- Then: fire and forget and the run record ---------------------------------------------------------------


@then("the agent is still running")
def then_agent_running(world):
    assert wait_for(lambda: world["sbx"].running()), "the agent is not running"


@then(
    parsers.re(
        r'the completion record has the status "(?P<status>[^"]+)" and the exit code (?P<code>\d+)'
    )
)
def then_completion_status_code(world, status, code):
    record = completion_of(world)
    assert (record["status"], record["exit_code"]) == (status, int(code)), record


@then(parsers.re(r'the completion record has the status "(?P<status>[^"]+)"$'))
def then_completion_status(world, status):
    assert completion_of(world)["status"] == status, completion_of(world)


@then(parsers.re(r'the completion record lists "(?P<name>[^"]+)" as changed'))
def then_changed(world, name):
    assert any(p.endswith(f"/{name}") for p in completion_of(world)["changed_files"])


@then(parsers.re(r'the completion record does not list "(?P<name>[^"]+)"'))
def then_not_changed(world, name):
    assert not any(
        p.endswith(f"/{name}") for p in completion_of(world)["changed_files"]
    )


@then("the completion record names the branch of the clone")
def then_branch(world):
    clone = completion_of(world)["clone"]
    assert clone["remote"] == f"sandbox-{sandbox_of(world)}"
    assert f"sandbox/{sandbox_of(world)}" in clone["branches"]


@then("the agent process was stopped")
def then_agent_stopped(world):
    assert wait_for(lambda: world["sbx"].events("agent_stopped"))


@then(
    parsers.re(
        r"the start response names the run id, the sandbox, the backend \"(?P<b>[^\"]+)\" and the model \"(?P<m>[^\"]+)\""
    )
)
def then_start_names(world, b, m):
    r = response(world)
    assert r["run_id"] and r["sandbox"] and (r["backend"], r["model"]) == (b, m)


@then("the start response lists the volumes and the network rules that were applied")
def then_start_applied(world):
    r = response(world)
    assert r["volumes"] and r["network"]


@then("the start response gives the run directory")
def then_start_run_dir(world):
    assert Path(response(world)["run_dir"]).is_dir()


@then(parsers.re(r'the run directory holds "(?P<a>[^"]+)" and "(?P<b>[^"]+)"'))
def then_run_dir_holds(world, a, b):
    assert (world["run_dir"] / a).is_file() and (world["run_dir"] / b).is_file()


@then(
    parsers.re(
        r'"(?P<file>[^"]+)" in the run directory does not contain "(?P<text>[^"]+)"'
    )
)
def then_file_lacks(world, file, text):
    assert text not in (world["run_dir"] / file).read_text()


@then(
    parsers.re(
        r'"(?P<file>[^"]+)" in the run directory holds the SHA-256 of "(?P<text>[^"]+)"'
    )
)
def then_file_hash(world, file, text):
    assert (
        hashlib.sha256(text.encode()).hexdigest()
        in (world["run_dir"] / file).read_text()
    )


@then(parsers.re(r'"(?P<file>[^"]+)" in the run directory contains "(?P<text>[^"]+)"'))
def then_file_has(world, file, text):
    assert text in (world["run_dir"] / file).read_text()


@then("the sandbox was not removed")
def then_not_removed(world):
    run_ends(world)
    name = sandbox_of(world)
    assert not [c for c in world["sbx"].commands("rm") if name in c["args"]]
    assert world["sbx"].sandbox(name) is not None


@then(parsers.re(r'the sandbox "(?P<name>[^"]+)" was neither reused nor removed'))
def then_taken_untouched(world, name):
    assert not [c for c in world["sbx"].commands("create") if name in c["args"]]
    assert not [c for c in world["sbx"].commands("rm") if name in c["args"]]
    assert world["sbx"].sandbox(name) is not None


# --- Then: audit and secrets --------------------------------------------------------------------------------


@then("one audit line was appended")
def then_one_audit(world):
    assert len(audit_lines(world)) == 1


@then(
    "the audit line holds the run id, the time, the backend, the model, the volumes, the network decisions and the outcome"
)
def then_audit_fields(world):
    line = audit_lines(world)[0]
    for key in ("run_id", "time", "backend", "model", "volumes", "network", "outcome"):
        assert key in line, f"{key} missing from {sorted(line)}"


@then(parsers.re(r'the audit line holds the outcome "(?P<outcome>[^"]+)"'))
def then_audit_outcome(world, outcome):
    assert audit_lines(world)[0]["outcome"] == outcome


@then("the audit file is outside every mounted volume")
def then_audit_outside(world):
    audit = (world["state_dir"] / "audit.jsonl").resolve()
    for volume in response(world)["volumes"]:
        assert Path(volume["host_path"]).resolve() not in audit.parents


@then(parsers.re(r'the audit line does not contain "(?P<text>[^"]+)"'))
def then_audit_lacks(world, text):
    assert audit_lines(world) and text not in json.dumps(audit_lines(world)[0])


@then(parsers.re(r'the start response does not contain "(?P<text>[^"]+)"'))
def then_response_lacks(world, text):
    assert text not in json.dumps(response(world))


@then(parsers.re(r'the run files do not contain "(?P<text>[^"]+)"'))
def then_run_files_lack(world, text):
    assert run_files_text(world) and text not in run_files_text(world)


@then(parsers.re(r'the tool log and the audit line do not contain "(?P<text>[^"]+)"'))
def then_log_lacks(world, text):
    log = world["state_dir"] / "tool.log"
    assert log.exists() and log.read_text(), "the tool wrote no log"
    assert text not in log.read_text() and text not in json.dumps(audit_lines(world))
