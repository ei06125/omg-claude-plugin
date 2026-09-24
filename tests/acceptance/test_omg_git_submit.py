import json
import re

import yaml
from pytest_bdd import given, parsers, scenarios, then

scenarios("omg-git-submit.feature")

PRACTICES = {
    "amending an existing commit": r"never amend",
    "force-pushing": r"never force-push",
    "bypassing, disabling or skipping repository hooks": r"do not bypass, disable, or skip repository hooks",
}


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


@then(
    "its instructions state that invoking it authorizes staging relevant files, one commit, a push and a pull request"
)
def then_authorizes(skill):
    assert_matches(
        r"authorizes staging relevant files.*one commit.*pushing.*pull request", skill
    )


@then(
    parsers.parse(
        'its instructions state that invoking it does not authorize "{action}"'
    )
)
def then_does_not_authorize(skill, action):
    assert_matches(rf"does not authorize [^.]*(?<![\w-]){re.escape(action)}", skill)


@then("its instructions require staging explicit task-relevant paths")
def then_explicit_paths(skill):
    assert_matches(r"stage explicit task-relevant paths", skill)


@then(parsers.parse('its instructions forbid staging with "{a}" and "{b}"'))
def then_forbid_broad_staging(skill, a, b):
    assert_matches(r"never use `", skill)
    assert f"`{a}`" in skill["body"]
    assert f"`{b}`" in skill["body"]


@then(parsers.parse('its instructions forbid "{practice}"'))
def then_forbid_practice(skill, practice):
    assert_matches(PRACTICES[practice], skill)


@then(
    "its instructions forbid submitting directly from a protected or long-lived branch"
)
def then_no_protected_branch(skill):
    assert_matches(
        r"do not submit directly from a protected or long-lived branch", skill
    )


@then("its instructions require creating a short-lived branch instead")
def then_short_lived_branch(skill):
    assert_matches(r"create a short-lived branch", skill)


@then(parsers.parse('its instructions require scanning staged content for "{value}"'))
def then_scans_staged_content(skill, value):
    assert_matches(rf"scan staged content for [^.]*{re.escape(value)}", skill)


@then("its instructions require stopping and asking when relevance is ambiguous")
def then_stops_on_ambiguity(skill):
    assert_matches(r"relevance is ambiguous.*stop and ask", skill)


@then("its instructions require asking when the pull request base evidence conflicts")
def then_asks_on_conflicting_base(skill):
    assert_matches(r"ask when evidence conflicts", skill)


@then(
    "its instructions require updating an open pull request that already exists instead of creating a duplicate"
)
def then_updates_existing_pr(skill):
    assert_matches(
        r"open PR already exists.*update it instead of creating a duplicate", skill
    )


@then("its instructions forbid merging it")
def then_no_merge(skill):
    assert_matches(r"do not merge it", skill)


@then(
    "its instructions forbid creating an empty commit when there are no relevant changes"
)
def then_no_empty_commit(skill):
    assert_matches(
        r"no relevant uncommitted changes, do not create an empty commit", skill
    )


@then(
    "its instructions require reporting the branch, commit, PR URL, validation result and anything excluded"
)
def then_reports(skill):
    assert_matches(
        r"report the branch, commit, PR URL, validation result, and anything intentionally excluded",
        skill,
    )
