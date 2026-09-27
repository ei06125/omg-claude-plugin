import json
import re

import yaml
from pytest_bdd import given, parsers, scenarios, then

scenarios("omg-teardown.feature")


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


@then("the model cannot invoke it on its own")
def then_not_model_invocable(skill):
    assert skill["front"].get("disable-model-invocation") is True


@then(parsers.parse('its front matter takes the "{argument}" argument'))
def then_takes_argument(skill, argument):
    assert argument in skill["front"].get("argument-hint", "")


@then(
    parsers.parse(
        'its instructions require saving every script created into a "{directory}" directory '
        "within its working directory"
    )
)
def then_saves_scripts(skill, directory):
    assert_matches(
        rf"for all scripts created, save them into a {re.escape(directory)} dir "
        r"within its corresponding working dir",
        skill,
    )


@then(
    parsers.parse(
        'its instructions require saving the summary into "{name}" when an argument is given'
    )
)
def then_saves_named_summary(skill, name):
    assert_matches(
        rf'save a summary of the conversation into "{re.escape(name)}" if "\$ARGUMENTS" is given',
        skill,
    )


@then(
    parsers.parse(
        'its instructions require saving the summary into the last "{name}" directory otherwise'
    )
)
def then_saves_last_summary(skill, name):
    assert_matches(
        rf"otherwise, save a summary of the conversation into the last {re.escape(name)} dir",
        skill,
    )


@then(
    parsers.parse(
        'its instructions require saving the summary into "{name}" within "{directory}", creating it if missing'
    )
)
def then_saves_diary_summary(skill, name, directory):
    assert_matches(
        rf"save the summary also to the {re.escape(name)} within {re.escape(directory)} dir "
        r"\(create if none\)",
        skill,
    )


@then(
    parsers.parse(
        'its instructions require saving cross-session information into "{name}"'
    )
)
def then_saves_cross_session(skill, name):
    assert_matches(
        rf"save cross-session information into the {re.escape(name)} as well", skill
    )


@then(
    "its instructions require saving important information unrelated to the workspace in long-term memory"
)
def then_saves_long_term(skill):
    assert_matches(
        r"save important information unrelated to workspace in long-term memory", skill
    )


@then(
    parsers.parse('its instructions require saving user profiling data into "{name}"')
)
def then_saves_profile(skill, name):
    assert_matches(
        rf"save user profiling data \(e\.g\. speech style\) into {re.escape(name)}",
        skill,
    )


@then(parsers.parse('its instructions state the commit rule "{rule}"'))
def then_states_commit_rule(skill, rule):
    assert rule.lower() in skill["body"].lower()


@then(parsers.parse('its instructions use the "{placeholder}" placeholder'))
def then_uses_placeholder(skill, placeholder):
    assert placeholder in skill["body"]


@then(parsers.parse('its instructions contain no "{template}" template'))
def then_no_template(skill, template):
    assert template not in skill["body"]
