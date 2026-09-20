import secrets

import pytest
import release
from support.fake_github import FakeGitHub


@pytest.fixture
def github():
    fake = FakeGitHub().start()
    yield fake
    fake.stop()


@pytest.fixture
def token():
    return secrets.token_hex(8)


@pytest.fixture
def api(github, token):
    return release.GitHubApi(github.url, github.repo, token)


class TestOpenReleasePullRequests:
    def test_only_release_branches_are_returned_by_branch_name(self, api, github):
        release_pr = github.seed("release/v0.2.0")
        github.seed("feature/search")
        github.seed("release/not-a-version")
        github.seed("release/v0.1.1", state="closed")
        assert api.open_release_pull_requests() == {"release/v0.2.0": release_pr["number"]}

    def test_pull_requests_from_forks_are_ignored(self, api, github):
        github.seed("release/v0.9.0", head_repo="someone/omg")
        assert api.open_release_pull_requests() == {}

    def test_it_sends_the_token_as_a_bearer_header(self, api, github, token):
        api.open_release_pull_requests()
        assert [r["auth"] for r in github.requests] == [f"Bearer {token}"]


class TestCreatePullRequest:
    def test_it_creates_the_pull_request(self, api, github):
        number = api.create_pull_request("release/v0.2.0", "main", "chore(release): v0.2.0", "Body text.")
        [pull_request] = github.open_prs()
        assert number == pull_request["number"]
        assert (pull_request["head"], pull_request["base"], pull_request["body"]) == ("release/v0.2.0", "main", "Body text.")

    def test_a_repository_that_blocks_workflow_pull_requests_is_not_configured(self, api, github):
        github.pr_creation_allowed = False
        with pytest.raises(release.NotConfigured, match="Allow GitHub Actions to create and approve pull requests"):
            api.create_pull_request("release/v0.2.0", "main", "title", "body")

    def test_a_validation_failure_is_a_release_error(self, api, github):
        github.seed("release/v0.2.0")
        with pytest.raises(release.ReleaseError, match="422"):
            api.create_pull_request("release/v0.2.0", "main", "title", "body")


class TestClosePullRequest:
    def test_it_comments_then_closes(self, api, github):
        pull_request = github.seed("release/v0.1.1")
        api.close_pull_request(pull_request["number"], "Superseded by v0.2.0.")
        assert pull_request["state"] == "closed"
        assert pull_request["comments"] == ["Superseded by v0.2.0."]


class TestFailures:
    def test_an_unknown_repository_is_a_release_error(self, github, token):
        api = release.GitHubApi(github.url, "someone/else", token)
        with pytest.raises(release.ReleaseError, match="404"):
            api.open_release_pull_requests()

    def test_an_unreachable_api_is_a_release_error_not_a_traceback(self, token):
        api = release.GitHubApi("http://127.0.0.1:9", "octo/omg", token)
        with pytest.raises(release.ReleaseError, match="GitHub API"):
            api.open_release_pull_requests()

    def test_the_token_is_never_part_of_an_error_message(self, github, token):
        api = release.GitHubApi(github.url, "someone/else", token)
        with pytest.raises(release.ReleaseError) as error:
            api.open_release_pull_requests()
        assert token not in str(error.value)
