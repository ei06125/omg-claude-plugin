import json
import re
import shutil
import subprocess

import yaml
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("omg-init.feature")


def read_skill(repo_root, name):
    text = (repo_root / ".claude" / "skills" / name / "SKILL.md").read_text()
    _, front, body = text.split("---", 2)
    return {"front": yaml.safe_load(front), "body": re.sub(r"\s+", " ", body.strip())}


def assert_matches(pattern, skill):
    assert re.search(pattern, skill["body"], re.I), pattern


def snapshot(root):
    """Every path under root, with the bytes of each file."""
    return {
        str(path.relative_to(root)): path.read_bytes() if path.is_file() else None
        for path in sorted(root.rglob("*"))
    }


# --- Given -------------------------------------------------------------------------------------------------


@given("the omg plugin manifest", target_fixture="manifest")
def given_manifest(repo_root):
    return json.loads((repo_root / ".claude-plugin" / "plugin.json").read_text())


@given(parsers.parse('the "{name}" skill'), target_fixture="skill")
def given_skill(repo_root, name):
    return read_skill(repo_root, name)


@given("a repository whose root already has AGENTS.md", target_fixture="repo")
def given_initialized_repository(tmp_path):
    assert shutil.which("claude"), "claude CLI not found on PATH"
    path = tmp_path / "repo"
    path.mkdir()
    (path / "AGENTS.md").write_text("# Existing\n")
    (path / "README.md").write_text("# Demo\n\nBuild it with make.\n")
    (path / "CLAUDE.md").write_text("Read AGENTS.md.\n")
    return {"path": path, "before": snapshot(path)}


# --- When --------------------------------------------------------------------------------------------------


@when(parsers.parse('I run "{command}" in it'), target_fixture="result")
def when_run_in_repository(repo_root, repo, command):
    return subprocess.run(
        ["claude", "--plugin-dir", str(repo_root), "-p", command],
        cwd=repo["path"],
        capture_output=True,
        text=True,
    )


# --- Then: structural ----------------------------------------------------------------------------------------


@then(parsers.parse('the "{name}" skill exists in that directory'))
def then_skill_exists(repo_root, manifest, name):
    assert (repo_root / manifest["skills"] / name / "SKILL.md").is_file()


@then("the model cannot invoke it on its own")
def then_not_model_invocable(skill):
    assert skill["front"].get("disable-model-invocation") is True


@then("its instructions require checking for a root AGENTS.md before any mutation")
def then_checks_agents_first(skill):
    assert_matches(
        r"before setup, discovery, directory creation, or any other mutation, "
        r"check for `AGENTS\.md` at the repository root",
        skill,
    )


@then("its instructions forbid reading or changing any repository file when it exists")
def then_touches_nothing(skill):
    assert_matches(
        r"if it exists, do not read, rewrite, move, or modify it or any other repository file",
        skill,
    )


@then("its instructions require reporting that initialization was skipped")
def then_reports_skip(skill):
    assert_matches(
        r"report that initialization was skipped and exit immediately", skill
    )


@then(parsers.parse('its instructions require creating the workspaces "{a}" and "{b}"'))
def then_creates_workspaces(skill, a, b):
    assert_matches(
        rf"visible repository workspaces `{re.escape(a)}` and `{re.escape(b)}`", skill
    )


@then("its instructions require preserving their existing contents")
def then_preserves_workspaces(skill):
    assert_matches(r"preserve existing contents", skill)


@then("its instructions forbid adding them to the ignore files")
def then_no_ignore(skill):
    assert_matches(
        r"do not add either directory to `\.gitignore` or `\.git/info/exclude`", skill
    )


@then(
    parsers.parse(
        'its instructions require reusing an existing "{a}", "{b}" or "{c}" directory with its spelling'
    )
)
def then_reuses_docs_root(skill, a, b, c):
    assert_matches(
        rf"directory named `{a}`, `{b}`, or `{c}`, case-insensitively\. "
        r"reuse it and preserve its spelling",
        skill,
    )


@then("its instructions forbid overwriting a useful existing document")
def then_no_overwrite(skill):
    assert_matches(r"never overwrite useful existing documents", skill)


@then(
    parsers.parse(
        'its instructions require creating "{a}", "{b}" and "{c}" under "{root}"'
    )
)
def then_creates_docs_tree(skill, a, b, c, root):
    assert_matches(
        rf"{re.escape(root)}.*{re.escape(a)}.*{re.escape(b)}.*{re.escape(c)}", skill
    )


@then(
    parsers.parse(
        'its instructions require creating the Technical document "{document}"'
    )
)
def then_creates_technical_document(skill, document):
    assert_matches(rf"Technical/.*{re.escape(document)}", skill)


@then(
    "its instructions require moving relevant material from README.md and CLAUDE.md rather than duplicating it"
)
def then_moves_material(skill):
    assert_matches(
        r"move, rather than duplicate, relevant material from README\.md and CLAUDE\.md",
        skill,
    )


@then(
    "its instructions forbid inventing missing architecture, environments, commands or policies"
)
def then_no_inventing(skill):
    assert_matches(
        r"do not invent missing architecture, environments, commands, or policies",
        skill,
    )


@then(
    "its instructions require README.md to keep the project identity, quick start and essential links"
)
def then_readme_keeps(skill):
    assert_matches(r"keep the project identity.*quick start.*essential links", skill)


@then(
    "its instructions require short summaries and relative links to the Technical documents"
)
def then_readme_links(skill):
    assert_matches(
        r"short summaries and relative links to the canonical Technical documents",
        skill,
    )


@then(parsers.parse('its instructions require AGENTS.md to be titled "{title}"'))
def then_agents_title(skill, title):
    assert_matches(rf"with the title `{re.escape(title)}`", skill)


@then(
    "its instructions forbid technology, command, layout, naming, testing and workflow details in it"
)
def then_agents_minimal(skill):
    assert_matches(
        r"do not add technology, commands, layout, naming, testing, or workflow details",
        skill,
    )


@then(
    parsers.parse('its instructions require a "{heading}" section pointing at "{path}"')
)
def then_agents_governance(skill, heading, path):
    assert_matches(
        rf"`{re.escape(heading)}` and point to `\[{re.escape(path)}\]\({re.escape(path)}\)`",
        skill,
    )


@then(parsers.parse('its instructions require the law "{law}"'))
def then_states_law(skill, law):
    assert law in skill["body"]


@then(
    "its instructions require CLAUDE.md to forward to AGENTS.md through a relative link"
)
def then_claude_forwards(skill):
    assert_matches(
        r"forwards Claude to `AGENTS\.md` through a relative Markdown link", skill
    )


@then("its instructions require CLAUDE.md to state that AGENTS.md is authoritative")
def then_claude_says_authoritative(skill):
    assert_matches(r"states that AGENTS\.md is authoritative", skill)


@then("its instructions require preserving nested CLAUDE.md instructions")
def then_preserves_nested(skill):
    assert_matches(r"preserve nested directory-specific CLAUDE instructions", skill)


@then("its instructions require confirming that links resolve")
def then_confirms_links(skill):
    assert_matches(r"confirm README and CLAUDE links resolve", skill)


@then(
    parsers.parse(
        'its instructions require confirming that "{a}" and "{b}" were not newly ignored'
    )
)
def then_confirms_not_ignored(skill, a, b):
    assert_matches(
        rf"confirm `{re.escape(a)}` and `{re.escape(b)}` were not newly ignored", skill
    )


@then(
    "its instructions require reviewing the diff for lost content, placeholder text, absolute paths, "
    "machine identity and secrets"
)
def then_reviews_diff(skill):
    assert_matches(
        r"review the diff for lost content, placeholder text, absolute paths, "
        r"machine identity, or secrets",
        skill,
    )


@then(
    "its instructions require running documentation validation when the repository provides it"
)
def then_runs_validation(skill):
    assert_matches(
        r"run documentation validation when the repository provides it", skill
    )


@then("its instructions require reporting created, rewritten and preserved files")
def then_reports_files(skill):
    assert_matches(r"report created, rewritten, and preserved files", skill)


@then("its instructions forbid committing or pushing unless explicitly requested")
def then_no_commit(skill):
    assert_matches(r"do not commit or push unless explicitly requested", skill)


@then(
    "its instructions state that it runs after setup when available and does not depend on it"
)
def then_after_setup(skill):
    assert_matches(
        r"run after the `setup` skill when available\. do not depend on setup", skill
    )


# --- Then: real run -------------------------------------------------------------------------------------------


@then("no file changed and nothing was created")
def then_nothing_changed(result, repo):
    assert result.returncode == 0, result.stdout + result.stderr
    assert snapshot(repo["path"]) == repo["before"]


@then("the reply says initialization was skipped")
def then_reply_says_skipped(result):
    assert "skip" in result.stdout.lower(), result.stdout
