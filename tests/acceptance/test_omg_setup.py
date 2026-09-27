import json
import re

import yaml
from pytest_bdd import given, parsers, scenarios, then

scenarios("omg-setup.feature")


def read_skill(repo_root, name):
    text = (repo_root / ".claude" / "skills" / name / "SKILL.md").read_text()
    _, front, body = text.split("---", 2)
    return {"front": yaml.safe_load(front), "body": re.sub(r"\s+", " ", body.strip())}


def assert_matches(pattern, skill):
    assert re.search(pattern, skill["body"], re.I), pattern


@given("the omg plugin manifest", target_fixture="manifest")
def given_manifest(repo_root):
    return json.loads((repo_root / ".claude-plugin" / "plugin.json").read_text())


@given(parsers.parse('the "{name}" skill'), target_fixture="skill")
def given_skill(repo_root, name):
    return read_skill(repo_root, name)


@then(parsers.parse('the "{name}" skill exists in that directory'))
def then_skill_exists(repo_root, manifest, name):
    assert (repo_root / manifest["skills"] / name / "SKILL.md").is_file()


@then("the model can invoke it on its own")
def then_model_invocable(skill):
    assert skill["front"].get("disable-model-invocation") is not True


@then(parsers.parse('its front matter takes the "{argument}" argument'))
def then_takes_argument(skill, argument):
    assert argument in skill["front"].get("argument-hint", "")


@then(
    "its instructions require checking that the required personal access tokens exist in environment variables"
)
def then_checks_tokens(skill):
    assert_matches(
        r"check if the required personal access tokens \(PATs\) exist in the env\. vars",
        skill,
    )


@then(
    parsers.parse(
        'its instructions require checking access to "{platform}" via "{tool}"'
    )
)
def then_checks_platform(skill, platform, tool):
    assert_matches(
        rf"check access to {re.escape(platform)}.*? via {re.escape(tool)}", skill
    )


@then(parsers.parse('its instructions require determining the active "{name}"'))
def then_determines_agent_name(skill, name):
    assert_matches(rf"determine the active `{re.escape(name)}`", skill)


@then(
    "its instructions require comparing it case-insensitively with the agent name declared in the "
    "project's CLAUDE.md"
)
def then_compares_names(skill):
    assert_matches(
        r"read the project-local `CLAUDE\.md` and identify its declared agent name\. "
        r"(?:- )?compare the names case-insensitively",
        skill,
    )


@then(parsers.parse('its instructions require running "{path}" once when they match'))
def then_runs_project_setup(skill, path):
    assert_matches(
        rf"if they match, lowercase `AGENTNAME`, look for the project-local "
        rf"`/setup-\$AGENTNAME` skill at `{re.escape(path)}`, and run it once",
        skill,
    )


@then(
    "its instructions require skipping it when the names do not match or the skill does not exist"
)
def then_skips_project_setup(skill):
    assert_matches(
        r"skip the project-local agent setup if the names do not match or the skill does not exist",
        skill,
    )


@then(
    parsers.parse('its instructions require checking "{path}" for session directories')
)
def then_checks_sessions(skill, path):
    assert_matches(rf"check {re.escape(path)} dir for session-\$DATETIME dirs", skill)


@then(parsers.parse('its instructions require reading "{name}" for a recap'))
def then_reads_diary(skill, name):
    assert_matches(rf"check for {re.escape(name)} file \(read for recap\)", skill)


@then(parsers.parse('its instructions require reading "{name}" for user profiling'))
def then_reads_profile(skill, name):
    assert_matches(
        rf"check for {re.escape(name)} file \(read for user profiling\)", skill
    )


@then(
    parsers.parse(
        'its instructions require creating "{name}" when the argument is empty'
    )
)
def then_creates_default_session(skill, name):
    assert_matches(rf'create a new {re.escape(name)} if "\$ARGUMENTS" is empty', skill)


@then(
    parsers.parse(
        'its instructions require creating "{name}" when an argument is given'
    )
)
def then_creates_named_session(skill, name):
    assert_matches(rf'otherwise, create a "{re.escape(name)}" dir in \.claude', skill)


@then(parsers.parse('its instructions use the "{placeholder}" placeholder'))
def then_uses_placeholder(skill, placeholder):
    assert placeholder in skill["body"]


@then(parsers.parse('its instructions contain no "{template}" template'))
def then_no_template(skill, template):
    assert template not in skill["body"]


@then(parsers.parse('its instructions state the rule "{rule}"'))
def then_states_rule(skill, rule):
    assert rule in skill["body"]
