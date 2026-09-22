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


def flat(skill):
    """The skill body with whitespace collapsed, for regex checks that may span a line wrap."""
    return re.sub(r"\s+", " ", skill["body"])


def gh_json(*args):
    out = subprocess.run(
        ["gh", *args, "--json", "number,title,body"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


# --- Given -------------------------------------------------------------------------------------------------


@given("the omg plugin manifest", target_fixture="manifest")
def given_manifest(repo_root):
    return json.loads((repo_root / ".claude-plugin" / "plugin.json").read_text())


@given(parsers.parse('the "{name}" skill'), target_fixture="skill")
def given_skill(repo_root, name):
    return read_skill(repo_root, name)


@given("a disposable TASK issue with two goals", target_fixture="task")
def given_disposable_task(tmp_path):
    assert shutil.which("gh"), "gh CLI not found on PATH"
    assert shutil.which("claude"), "claude CLI not found on PATH"
    body = (
        "## Objective\n\nDisposable prepare-subtask fixture.\n\n"
        "## Acceptance criteria\n\n"
        "- [ ] First disposable goal.\n"
        "- [ ] Second disposable goal.\n"
    )
    created = subprocess.run(
        [
            "gh",
            "issue",
            "create",
            "-R",
            REPO,
            "--title",
            "[05_TASKS] TASK-TEST: disposable prepare-subtask fixture",
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
    workdir = tmp_path / "work"
    workdir.mkdir()
    yield {"number": number, "workdir": workdir}
    created_subtasks = gh_json(
        "issue",
        "list",
        "-R",
        REPO,
        "--search",
        f'"prepare-subtask fixture" in:body "{number}"',
        "--state",
        "all",
    )
    for sub in created_subtasks:
        if sub["number"] != int(number) and f"issues/{number}" in sub["body"]:
            subprocess.run(
                [
                    "gh",
                    "issue",
                    "close",
                    "-R",
                    REPO,
                    str(sub["number"]),
                    "--comment",
                    "Disposable test fixture; closing.",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
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
def when_run_prepare_subtask(repo_root, task, command):
    return subprocess.run(
        ["claude", "--plugin-dir", str(repo_root), "-p", f"{command} {task['number']}"],
        cwd=task["workdir"],
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
def then_refuses_non_task(skill, tag):
    assert re.search(r"\brefuse\b", skill["body"], re.I)
    assert tag in skill["body"]


@then(
    parsers.parse(
        'its instructions require finding the highest existing "{pattern}" number first'
    )
)
def then_finds_highest(skill, pattern):
    assert re.search(r"highest existing", skill["body"], re.I)
    assert pattern in skill["body"]


@then("its instructions state that new numbers never repeat one already used")
def then_numbers_unique(skill):
    assert re.search(r"never repeat one already used", skill["body"], re.I)


@then("its instructions require writing and creating one issue per goal")
def then_one_issue_per_goal(skill):
    assert re.search(r"for each goal", skill["body"], re.I)
    assert re.search(r"one issue", skill["body"], re.I)


@then("its instructions state that writing it is never delegated")
def then_not_delegated(skill):
    assert re.search(r"never delegate", skill["body"], re.I)


@then(
    parsers.parse(
        'its instructions require the "{section}" section to be verbatim and numbered'
    )
)
def then_instructions_verbatim(skill, section):
    body = flat(skill)
    assert section in body
    assert re.search(r"verbatim, numbered", body, re.I)


@then("its instructions forbid a prose goal in that section")
def then_forbid_prose(skill):
    assert re.search(r"never a prose goal", skill["body"], re.I)


@then("its instructions require linking each SUBTASK as a native sub-issue of the TASK")
def then_native_link(skill):
    body = flat(skill)
    assert re.search(r"native sub-issue", body, re.I)
    assert "addSubIssue" in body


@then("its instructions require the sub-issue count to equal the goal count")
def then_count_check(skill):
    assert re.search(r"sub_issues", skill["body"])
    assert re.search(r"equal(s|ing)? the (number|goal) ", flat(skill), re.I)


@then(
    parsers.parse(
        'its instructions require every SUBTASK to have a numbered "{section}" section'
    )
)
def then_every_subtask_checked(skill, section):
    body = flat(skill)
    assert re.search(rf"every.*created.*subtask.*{section}", body, re.I)


@then(parsers.parse('its instructions require reporting to the person "{tool}" names'))
def then_report_whoami(skill, tool):
    assert tool in skill["body"]
    assert re.search(r"tell the person", skill["body"], re.I)


@then("its instructions forbid retrying or guessing a fix on failure")
def then_no_retry(skill):
    assert re.search(r"do not retry", skill["body"], re.I)
    assert re.search(r"do not guess", skill["body"], re.I)


@then(parsers.parse('its instructions forbid running "{a}", "{b}" and "{c}"'))
def then_forbid_git(skill, a, b, c):
    pattern = rf"never.*{re.escape(a)}.*{re.escape(b)}.*{re.escape(c)}"
    assert re.search(pattern, skill["body"], re.I | re.S)


@then("its instructions forbid opening a pull request")
def then_forbid_pr(skill):
    assert re.search(r"never open a pull request", skill["body"], re.I)


@then("its instructions forbid ticking a box in the TASK issue")
def then_forbid_ticking(skill):
    assert re.search(r"never tick a box in the TASK issue", skill["body"], re.I)


# --- Then: real run -------------------------------------------------------------------------------------------


def created_subtasks(task):
    return gh_json(
        "issue",
        "list",
        "-R",
        REPO,
        "--search",
        f'"[06_SUBTASKS]" in:body {task["number"]}',
        "--state",
        "all",
    )


@then("exactly two linked SUBTASK issues were created")
def then_two_subtasks(result, task):
    assert result.returncode == 0, result.stdout + result.stderr
    subs = subprocess.run(
        ["gh", "api", f"repos/{REPO}/issues/{task['number']}/sub_issues", "--jq", "."],
        capture_output=True,
        text=True,
        check=True,
    )
    task["sub_issues"] = json.loads(subs.stdout)
    assert len(task["sub_issues"]) == 2, task["sub_issues"]


@then(parsers.parse('each has a numbered "{section}" section'))
def then_each_has_instructions(task, section):
    for sub in task["sub_issues"]:
        body = subprocess.run(
            [
                "gh",
                "issue",
                "view",
                str(sub["number"]),
                "-R",
                REPO,
                "--json",
                "body",
                "-q",
                ".body",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert f"## {section}" in body
        assert re.search(r"^\s*1\.", body, re.M)


@then("the report names Pedro")
def then_names_pedro(result):
    assert "Pedro" in result.stdout
