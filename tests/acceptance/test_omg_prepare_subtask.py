import json
import re
import shutil
import subprocess

import yaml
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("omg-prepare-subtask.feature")

REPO = "ei06125/omg-claude-plugin"


def read_skill(repo_root, name):
    text = (repo_root / ".claude" / "skills" / name / "SKILL.md").read_text()
    _, front, body = text.split("---", 2)
    return {"front": yaml.safe_load(front), "body": body.strip()}


# --- Given -------------------------------------------------------------------------------------------------


@given("the omg plugin manifest", target_fixture="manifest")
def given_manifest(repo_root):
    return json.loads((repo_root / ".claude-plugin" / "plugin.json").read_text())


@given(parsers.parse('the "{name}" skill'), target_fixture="skill")
def given_skill(repo_root, name):
    return read_skill(repo_root, name)


@given(
    "a disposable SUBTASK issue with a mechanically checkable criterion",
    target_fixture="subtask",
)
def given_disposable_issue(tmp_path):
    assert shutil.which("gh"), "gh CLI not found on PATH"
    assert shutil.which("claude"), "claude CLI not found on PATH"
    workdir = tmp_path / "work"
    workdir.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=workdir, check=True)
    (workdir / "greeting.txt").write_text("hello\n")
    body = (
        "## Objective\n\nChange the content of `greeting.txt` to exactly the line `done`.\n\n"
        "## Acceptance criteria\n\n- [ ] `greeting.txt` contains exactly the line `done`.\n"
    )
    created = subprocess.run(
        [
            "gh",
            "issue",
            "create",
            "-R",
            REPO,
            "--title",
            "[06_SUBTASKS] SUBTASK-TEST: disposable prepare-subtask fixture",
            "--body",
            body,
            "--label",
            "test",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    number = created.stdout.strip().rsplit("/", 1)[-1]
    yield {"number": number, "workdir": workdir, "file": workdir / "greeting.txt"}
    subprocess.run(
        [
            "gh",
            "issue",
            "close",
            "-R",
            REPO,
            number,
            "--comment",
            "Disposable test fixture; closing.",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


# --- When --------------------------------------------------------------------------------------------------


@when(parsers.parse('I run "{command}" on that issue'), target_fixture="result")
def when_run_prepare_subtask(repo_root, subtask, command):
    return subprocess.run(
        [
            "claude",
            "--plugin-dir",
            str(repo_root),
            "-p",
            f"{command} {subtask['number']} {subtask['workdir']}",
        ],
        cwd=subtask["workdir"],
        capture_output=True,
        text=True,
    )


# --- Then: structural ----------------------------------------------------------------------------------------


@then(parsers.parse('the "{name}" skill exists in that directory'))
def then_skill_exists(repo_root, manifest, name):
    assert (repo_root / manifest["skills"] / name / "SKILL.md").is_file()


@then("the model can invoke it on its own")
def then_model_invocable(skill):
    assert skill["front"].get("disable-model-invocation") is not True


@then(parsers.parse('its instructions name the invocation "{command}"'))
def then_names_invocation(skill, command):
    assert command in skill["body"]


@then(
    parsers.parse(
        'its instructions require refusing an issue whose title is not tagged "{tag}"'
    )
)
def then_refuses_non_subtask(skill, tag):
    assert re.search(r"\brefuse\b", skill["body"], re.I)
    assert tag in skill["body"]


@then(
    "its instructions require the invoking agent to write the recipe from the issue's Objective and Acceptance criteria"
)
def then_agent_writes_recipe(skill):
    body = skill["body"]
    assert "Objective" in body
    assert "Acceptance criteria" in body
    assert re.search(r"writes? the recipe", body, re.I)


@then("its instructions state that recipe authoring is not delegated")
def then_recipe_not_delegated(skill):
    assert re.search(r"not delegat\w*", skill["body"], re.I)


@then(parsers.parse("its instructions require the recipe to be {trait}"))
def then_recipe_trait(skill, trait):
    assert trait.lower() in skill["body"].lower()


@then(
    parsers.parse('its instructions name "{a}" and "{b}" as the acting model choices')
)
def then_model_choices(skill, a, b):
    assert a in skill["body"]
    assert b in skill["body"]


@then(parsers.parse('its instructions default the acting model to "{model}"'))
def then_default_model(skill, model):
    assert re.search(
        rf"default\w*.*{re.escape(model)}", skill["body"], re.I
    ) or re.search(rf"{re.escape(model)}.*default\w*", skill["body"], re.I)


@then(
    parsers.parse(
        'its instructions require the delegate "{arg}" argument to list only what the recipe uses'
    )
)
def then_commands_scoped(skill, arg):
    assert arg in skill["body"]
    assert re.search(r"only what the recipe uses", skill["body"], re.I)


@then(parsers.parse('its instructions forbid a wildcard in "{arg}"'))
def then_forbid_wildcard(skill, arg):
    assert arg in skill["body"]
    assert re.search(r"never.*wildcard", skill["body"], re.I)


@then(
    "its instructions require a deterministic command when the acceptance criteria allow one"
)
def then_prefer_deterministic(skill):
    assert re.search(r"deterministic (command|check|gate)", skill["body"], re.I)


@then(
    "its instructions require a same-tier reviewer model only when a deterministic command cannot decide it"
)
def then_reviewer_fallback(skill):
    body = re.sub(r"\s+", " ", skill["body"])
    assert re.search(r"same[- ]tier reviewer", body, re.I)
    assert re.search(r"only when", body, re.I)


@then("its instructions bound the number of rounds")
def then_bounded_rounds(skill):
    assert re.search(r"\bmax_rounds\b", skill["body"])


@then(
    "its instructions require reporting failure after the last round instead of a guessed fix"
)
def then_honest_failure(skill):
    body = skill["body"]
    assert re.search(r"last round", body, re.I)
    assert re.search(r"never guess", body, re.I)


@then(parsers.parse('its instructions forbid running "{a}", "{b}" and "{c}"'))
def then_forbid_git(skill, a, b, c):
    pattern = rf"never.*{re.escape(a)}.*{re.escape(b)}.*{re.escape(c)}"
    assert re.search(pattern, skill["body"], re.I | re.S)


@then("its instructions forbid opening a pull request")
def then_forbid_pr(skill):
    assert re.search(r"never open a pull request", skill["body"], re.I)


@then("its instructions forbid ticking an acceptance box in the issue")
def then_forbid_ticking(skill):
    assert re.search(r"never tick.*acceptance (box|checkbox)", skill["body"], re.I)


# --- Then: real run -------------------------------------------------------------------------------------------


@then("only the file the criterion describes changed")
def then_only_file_changed(result, subtask):
    assert result.returncode == 0, result.stdout + result.stderr
    others = [
        p
        for p in subtask["workdir"].rglob("*")
        if p.is_file() and ".git" not in p.parts and p != subtask["file"]
    ]
    assert others == [], f"unexpected files changed: {others}"


@then("the deterministic gate for that criterion passes")
def then_gate_passes(subtask):
    assert subtask["file"].read_text().strip() == "done"


@then("no commit was made in the working directory")
def then_no_commit(subtask):
    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=subtask["workdir"],
        capture_output=True,
        text=True,
    )
    assert log.stdout.strip() == ""
