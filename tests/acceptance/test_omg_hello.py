import json
import shutil
import subprocess

import yaml
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("omg-hello.feature")


def read_skill(repo_root, name):
    text = (repo_root / ".claude" / "skills" / name / "SKILL.md").read_text()
    _, front, body = text.split("---", 2)
    return {"front": yaml.safe_load(front), "body": body.strip()}


@given("the omg plugin manifest", target_fixture="manifest")
def given_manifest(repo_root):
    return json.loads((repo_root / ".claude-plugin" / "plugin.json").read_text())


@given(parsers.parse('the "{name}" skill'), target_fixture="skill")
def given_skill(repo_root, name):
    return read_skill(repo_root, name)


@given(
    "a new Claude Code session outside the repository with the omg plugin loaded",
    target_fixture="session",
)
def given_session(repo_root, tmp_path):
    assert shutil.which("claude"), "claude CLI not found on PATH"
    return {"cwd": tmp_path, "plugin_dir": repo_root}


@when("I validate the plugin with Claude Code", target_fixture="result")
def when_validate(repo_root):
    return subprocess.run(
        ["claude", "plugin", "validate", str(repo_root)],
        capture_output=True,
        text=True,
    )


@when(parsers.parse('I run "{command}"'), target_fixture="result")
def when_run(session, command):
    return subprocess.run(
        ["claude", "--plugin-dir", str(session["plugin_dir"]), "-p", command],
        cwd=session["cwd"],
        capture_output=True,
        text=True,
    )


@then(parsers.parse('the manifest points at the skills directory "{path}"'))
def then_manifest_points_at_skills(manifest, path):
    assert manifest["skills"].rstrip("/") == f"./{path}"


@then(parsers.parse('the "{name}" skill exists in that directory'))
def then_skill_exists(repo_root, manifest, name):
    assert (repo_root / manifest["skills"] / name / "SKILL.md").is_file()


@then("the model cannot invoke it on its own")
def then_not_model_invocable(skill):
    assert skill["front"].get("disable-model-invocation") is True


@then(parsers.parse('its instructions require the reply "{reply}" and nothing else'))
def then_requires_exact_reply(skill, reply):
    assert reply in skill["body"].splitlines()
    assert "nothing else" in skill["body"]


@then("validation passes")
def then_validation_passes(result):
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Validation passed" in result.stdout


@then(parsers.parse('the reply is exactly "{reply}"'))
def then_reply_is_exact(result, reply):
    assert result.returncode == 0, result.stderr
    assert result.stdout.rstrip("\n") == reply
