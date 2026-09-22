import secrets
import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from support.fake_github import FakeGitHub
from support.git_repo import MANIFEST, Origin, clean_env, make_released_repo

scenarios("omg-release.feature")

RELEASE_SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "release.py"
NOT_CONFIGURED = 78
SETTING = "Allow GitHub Actions to create and approve pull requests"


@pytest.fixture
def world(tmp_path):
    github = FakeGitHub().start()
    yield {
        "tmp": tmp_path,
        "token": secrets.token_hex(16),
        "has_token": True,
        "github": github,
        "output": tmp_path / "github-output.txt",
    }
    github.stop()


def run_script(world, *args):
    extra = {"GITHUB_OUTPUT": str(world["output"])}
    if world["has_token"]:
        extra["RELEASE_TOKEN"] = world["token"]
    result = subprocess.run(
        [sys.executable, str(RELEASE_SCRIPT), *args],
        cwd=world["repo"].path,
        capture_output=True,
        text=True,
        env=clean_env(**extra),
    )
    world["result"] = result
    return result


def publish(world, *extra):
    github = world["github"]
    return run_script(
        world,
        "publish",
        "--remote",
        "origin",
        "--target",
        "main",
        "--github-repo",
        github.repo,
        "--api-url",
        github.url,
        *extra,
    )


def released(world, version, tagged=True):
    repo = make_released_repo(world["tmp"], version=version, tagged=tagged)
    origin = Origin(world["tmp"] / "origin.git")
    origin.connect(repo)
    world.update(repo=repo, origin=origin)


@given(parsers.parse('the plugin is released as "{version}"'))
def given_released(world, version):
    released(world, version)


@given("the plugin has no baseline release")
def given_no_baseline(world):
    released(world, "0.1.0", tagged=False)


@given("a feature spec was accepted since that release")
def given_accepted(world):
    world["repo"].write_spec("omg-search", "Accepted")
    world["repo"].commit("Accept omg-search")


@given("shipped content was fixed since that release")
def given_fixed(world):
    world["repo"].write(".claude/skills/hello/SKILL.md", "hello v2\n")
    world["repo"].commit("Fix the hello skill")


@given("only documentation, tests and CI changed since that release")
def given_unshipped(world):
    repo = world["repo"]
    repo.write("README.md", "reworded\n")
    repo.write("tests/test_x.py", "x = 2\n")
    repo.write(".github/workflows/tests.yml", "name: Tests\n")
    repo.commit("Docs, tests and CI")


@given("a feature spec was marked as breaking since that release")
def given_breaking(world):
    world["repo"].write_spec("omg-hello", "Accepted", breaking=True)
    world["repo"].commit("Mark omg-hello as breaking")


@given(parsers.parse('the release job already proposed "{version}"'))
def given_already_proposed(world, version):
    result = publish(world)
    assert result.returncode == 0, result.stderr
    assert f"release/v{version}" in world["origin"].release_branches()


@given(
    parsers.parse(
        'the release job proposed "{version}" while pull requests were not allowed'
    )
)
def given_proposed_without_pull_request(world, version):
    world["github"].pr_creation_allowed = False
    result = publish(world)
    assert result.returncode == NOT_CONFIGURED, result.stderr
    branch = f"release/v{version}"
    assert branch in world["origin"].release_branches()
    world["tip"] = world["origin"].git("rev-parse", branch)
    world["github"].pr_creation_allowed = True


@given(parsers.parse('the release "{version}" was merged into main'))
def given_release_merged(world, version):
    world["repo"].set_manifest_version(version)
    world["repo"].commit(f"Merge release v{version}")


@given("no release token is configured")
def given_no_token(world):
    world["has_token"] = False


@given("workflows are not allowed to create pull requests")
def given_pull_requests_blocked(world):
    world["github"].pr_creation_allowed = False


@given(parsers.parse('{kind} "{tag}" on main for plugin version "{version}"'))
def given_tag_on_main(world, kind, tag, version):
    released(world, "0.1.0")
    repo = world["repo"]
    repo.set_manifest_version(version)
    repo.commit("Release commit")
    repo.tag(tag, annotated=(kind == "an annotated tag"))


@when("the release job runs")
def when_release_job_runs(world):
    publish(world)


@when("the release job runs as a dry run")
def when_dry_run(world):
    publish(world, "--dry-run")


@when(parsers.parse('the tag workflow verifies "{tag}"'))
def when_verify(world, tag):
    run_script(world, "verify-tag", tag, "--main-ref", "main")


@then(parsers.parse('a release "{version}" is proposed for review'))
def then_proposed(world, version):
    result, origin, github = world["result"], world["origin"], world["github"]
    assert result.returncode == 0, result.stdout + result.stderr
    branch = f"release/v{version}"
    assert origin.release_branches() == {branch}
    assert origin.git("rev-parse", f"{branch}~1") == world["repo"].git(
        "rev-parse", "HEAD"
    )
    assert origin.changed_files(branch, f"{branch}~1") == {MANIFEST}
    assert f'"version": "{version}"' in origin.file_at(branch, MANIFEST)
    [pull_request] = github.open_prs()
    assert pull_request["head"] == branch
    assert pull_request["base"] == "main"
    assert pull_request["title"] == f"chore(release): v{version}"
    assert {request["auth"] for request in github.requests} == {
        f"Bearer {world['token']}"
    }


@then("no release is proposed")
def then_none_proposed(world):
    assert world["result"].returncode == 0, world["result"].stderr
    assert world["origin"].release_branches() == set()
    assert world["github"].prs == []


@then("no further release is proposed")
def then_no_further(world):
    assert world["result"].returncode == 0, world["result"].stderr
    assert len(world["github"].posts_to_pulls()) == 1
    assert len(world["github"].open_prs()) == 1


@then(parsers.parse('the proposal for "{version}" is withdrawn'))
def then_withdrawn(world, version):
    branch = f"release/v{version}"
    assert branch not in world["origin"].release_branches()
    [withdrawn] = [pr for pr in world["github"].prs if pr["head"] == branch]
    assert withdrawn["state"] == "closed"
    assert any("v0.2.0" in comment for comment in withdrawn["comments"])


@then("the existing release branch was reused")
def then_branch_reused(world):
    branch = next(iter(world["origin"].release_branches()))
    assert world["origin"].git("rev-parse", branch) == world["tip"]


@then(parsers.parse('"{tag}" is tagged on main with an annotated tag'))
def then_tagged(world, tag):
    origin = world["origin"]
    assert world["result"].returncode == 0, world["result"].stderr
    assert tag in origin.tags()
    assert origin.object_type(f"refs/tags/{tag}") == "tag"
    assert origin.git("rev-parse", f"{tag}^{{commit}}") == world["repo"].git(
        "rev-parse", "HEAD"
    )


@then(parsers.parse('the workflow is told about the tag "{tag}"'))
def then_workflow_told(world, tag):
    assert world["output"].read_text().splitlines() == [f"tag={tag}"]


@then("the release job reports that it is not configured")
def then_not_configured(world):
    result = world["result"]
    assert result.returncode == NOT_CONFIGURED, result.stdout + result.stderr
    assert "not configured" in (result.stdout + result.stderr)


@then("it explains which repository setting to change")
def then_explains_setting(world):
    assert SETTING in world["result"].stdout + world["result"].stderr


@then("nothing was pushed")
def then_nothing_pushed(world):
    assert world["origin"].release_branches() == set()
    assert world["github"].prs == []


@then(parsers.parse('the plan mentions release "{version}"'))
def then_plan(world, version):
    result = world["result"]
    assert result.returncode == 0, result.stderr
    assert f"release/v{version}" in result.stdout


@then("the release token does not appear in the output")
def then_no_token_in_output(world):
    result = world["result"]
    assert result.returncode == 0, result.stderr
    assert world["token"] not in result.stdout + result.stderr


@then(parsers.parse("the tag is {verdict}"))
def then_verdict(world, verdict):
    result = world["result"]
    output = result.stdout + result.stderr
    assert "Traceback" not in output, output
    if verdict == "accepted":
        assert result.returncode == 0, output
    else:
        assert result.returncode == 1, output
        assert "error:" in result.stderr, output
