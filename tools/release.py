#!/usr/bin/env python3
"""Release automation for the omg plugin (ADR-0002 and the omg-release spec).

Commands:
  next        print the next version, or nothing when there is nothing to release
  publish     tag a merged release, or propose the next one as a pull request
  verify-tag  check that a tag is a genuine release tag
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

EX_CONFIG = 78
API_URL = "https://api.github.com"
PR_SETTING = "Allow GitHub Actions to create and approve pull requests"
MANIFEST = ".claude-plugin/plugin.json"
SPEC_DIR = "documentation/Product/Features"
SHIPPED = (".claude/", ".claude-plugin/", "sources/", "configs/")
BOT_IDENTITY = {
    "GIT_AUTHOR_NAME": "github-actions[bot]",
    "GIT_AUTHOR_EMAIL": "41898282+github-actions[bot]@users.noreply.github.com",
    "GIT_COMMITTER_NAME": "github-actions[bot]",
    "GIT_COMMITTER_EMAIL": "41898282+github-actions[bot]@users.noreply.github.com",
}

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
TAG_RE = re.compile(r"^v(\d+\.\d+\.\d+)$")
RELEASE_BRANCH_RE = re.compile(r"^release/v\d+\.\d+\.\d+$")
STATUS_RE = re.compile(r"^- \*\*Status:\*\*[ \t]*(.+?)[ \t]*$", re.MULTILINE)
BREAKING_RE = re.compile(
    r"^- \*\*Breaking:\*\*[ \t]*yes\b", re.MULTILINE | re.IGNORECASE
)
VERSION_LINE_RE = re.compile(r'^([ \t]*"version"[ \t]*:[ \t]*)"[^"]*"', re.MULTILINE)
STATUSES = ("accepted", "in development", "draft")

_secrets = set()


class ReleaseError(Exception):
    """A release rule or a git operation failed."""


class NotConfigured(ReleaseError):
    """Release automation is not set up yet (exit code 78)."""


def redact(text):
    for secret in _secrets:
        text = text.replace(secret, "***")
    return text


def emit(message):
    print(redact(message))


class GitHubApi:
    """The few GitHub REST calls the release needs. The token only ever goes into a header."""

    def __init__(self, api_url, repo, token):
        self.repo = repo
        self.base = f"{api_url.rstrip('/')}/repos/{repo}"
        self.token = token

    def request(self, method, path, body=None):
        request = urllib.request.Request(
            f"{self.base}{path}",
            data=None if body is None else json.dumps(body).encode(),
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read() or b"null")
        except urllib.error.HTTPError as error:
            try:
                return error.code, json.loads(error.read() or b"null")
            except ValueError:
                return error.code, None
        except OSError as error:
            raise ReleaseError(
                f"could not reach the GitHub API: {redact(str(error))}"
            ) from None

    def fail(self, action, status, payload):
        detail = payload.get("message", "") if isinstance(payload, dict) else ""
        raise ReleaseError(
            f"GitHub API call to {action} failed with {status}: {redact(detail)}".rstrip(
                ": "
            )
        )

    def open_release_pull_requests(self):
        status, payload = self.request("GET", "/pulls?state=open&per_page=100")
        if status != 200:
            self.fail("list pull requests", status, payload)
        return {
            pr["head"]["ref"]: pr["number"]
            for pr in payload
            if RELEASE_BRANCH_RE.match(pr["head"]["ref"])
            and pr["head"].get("repo", {}).get("full_name") == self.repo
        }

    def create_pull_request(self, head, base, title, body):
        status, payload = self.request(
            "POST", "/pulls", {"head": head, "base": base, "title": title, "body": body}
        )
        if status == 201:
            return payload["number"]
        if status == 403:
            raise NotConfigured(
                f"GitHub refused to create the pull request. Turn on '{PR_SETTING}' in "
                "Settings > Actions > General > Workflow permissions, and give the job pull-requests: write"
            )
        self.fail("create the pull request", status, payload)

    def close_pull_request(self, number, comment):
        status, payload = self.request(
            "POST", f"/issues/{number}/comments", {"body": comment}
        )
        if status != 201:
            self.fail("comment on the pull request", status, payload)
        status, payload = self.request("PATCH", f"/pulls/{number}", {"state": "closed"})
        if status != 200:
            self.fail("close the pull request", status, payload)


def git(repo, *args, env=None, input_text=None, check=True):
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        input=input_text,
        env={**os.environ, **(env or {})},
    )
    if check and result.returncode != 0:
        raise ReleaseError(f"git {args[0]} failed: {redact(result.stderr.strip())}")
    return result.stdout


def parse_version(text):
    match = VERSION_RE.match(text)
    if not match:
        raise ValueError(f"not a version X.Y.Z: {text!r}")
    return tuple(int(part) for part in match.groups())


def bump(version, kind):
    major, minor, patch = parse_version(version)
    return {
        "major": f"{major + 1}.0.0",
        "minor": f"{major}.{minor + 1}.0",
        "patch": f"{major}.{minor}.{patch + 1}",
    }[kind]


def spec_status(text):
    match = STATUS_RE.search(text)
    if not match:
        return None
    value = match.group(1).lower()
    return next((name for name in STATUSES if value.startswith(name)), None)


def is_breaking(text):
    return bool(BREAKING_RE.search(text))


def bump_manifest_text(text, version):
    parse_version(version)
    if "version" not in json.loads(text):
        raise ReleaseError(f"{MANIFEST} has no version field")
    matches = list(VERSION_LINE_RE.finditer(text))
    if not matches:
        raise ReleaseError(f"could not find the version line in {MANIFEST}")
    top = min(matches, key=lambda m: len(m.group(1)) - len(m.group(1).lstrip(" \t")))
    return f'{text[: top.start()]}{top.group(1)}"{version}"{text[top.end() :]}'


def manifest_version(repo, rev):
    try:
        text = git(repo, "show", f"{rev}:{MANIFEST}")
    except ReleaseError:
        raise ReleaseError(f"{MANIFEST} not found at {rev}") from None
    return json.loads(text).get("version", "")


def latest_tag(repo, head="HEAD"):
    tags = git(repo, "tag", "--list", "v*", "--merged", head).split()
    versions = [
        (parse_version(m.group(1)), tag) for tag in tags if (m := TAG_RE.match(tag))
    ]
    return max(versions)[1] if versions else None


def specs_at(repo, rev):
    names = git(repo, "ls-tree", "-r", "--name-only", rev, "--", SPEC_DIR).splitlines()
    return {
        name: git(repo, "show", f"{rev}:{name}")
        for name in names
        if name.endswith(".md")
    }


def next_version(repo, base_tag=None, head="HEAD"):
    base_tag = base_tag or latest_tag(repo, head)
    if base_tag is None:
        raise NotConfigured(
            "no baseline release tag: create an annotated tag vX.Y.Z on main first"
        )
    base = base_tag[1:]
    before, after = specs_at(repo, base_tag), specs_at(repo, head)
    accepted = any(
        spec_status(text) == "accepted"
        and spec_status(before.get(name, "")) != "accepted"
        for name, text in after.items()
    )
    breaking = any(
        is_breaking(text) and not is_breaking(before.get(name, ""))
        for name, text in after.items()
    )
    changed = git(
        repo, "diff", "--name-only", "--no-renames", base_tag, head
    ).splitlines()
    shipped = any(path.startswith(SHIPPED) for path in changed)
    if breaking:
        kind = "major" if parse_version(base)[0] >= 1 else "minor"
    elif accepted:
        kind = "minor"
    elif shipped:
        kind = "patch"
    else:
        return None
    return bump(base, kind), kind


@contextmanager
def remote_env(remote, token):
    """Git environment for network calls. The token reaches git through GIT_ASKPASS, never through a URL."""
    env = {"GIT_TERMINAL_PROMPT": "0"}
    if remote.startswith("https://") and token:
        with tempfile.TemporaryDirectory() as directory:
            helper = Path(directory) / "askpass.sh"
            helper.write_text("#!/bin/sh\nprintf '%s' \"$RELEASE_TOKEN\"\n")
            helper.chmod(0o700)
            yield {**env, "GIT_ASKPASS": str(helper), "RELEASE_TOKEN": token}
    else:
        yield env


def remote_refs(repo, remote, pattern, env, kind):
    out = git(repo, "ls-remote", f"--{kind}", remote, pattern, env=env)
    return [line.split("\t")[1] for line in out.splitlines() if "\t" in line]


def release_commit(repo, manifest_text, message):
    """Build the release commit with git plumbing so the working tree is never touched."""
    with tempfile.TemporaryDirectory() as directory:
        env = {"GIT_INDEX_FILE": str(Path(directory) / "index"), **BOT_IDENTITY}
        mode = git(repo, "ls-tree", "HEAD", MANIFEST).split()[0]
        git(repo, "read-tree", "HEAD", env=env)
        blob = git(
            repo, "hash-object", "-w", "--stdin", input_text=manifest_text, env=env
        ).strip()
        git(repo, "update-index", "--cacheinfo", f"{mode},{blob},{MANIFEST}", env=env)
        tree = git(repo, "write-tree", env=env).strip()
        return git(
            repo, "commit-tree", tree, "-p", "HEAD", "-m", message, env=env
        ).strip()


def tag_release(repo, remote, version, token, dry_run, out):
    tag = f"v{version}"
    sha = git(repo, "rev-parse", "HEAD").strip()
    with remote_env(remote, token) as env:
        if remote_refs(repo, remote, f"refs/tags/{tag}", env, "tags"):
            out(f"{tag} already exists on the remote; it is never moved.")
            return None
        if dry_run:
            out(f"Would create the annotated tag {tag} on {sha[:12]} and push it.")
            return None
        git(repo, "tag", "-a", "-m", f"Release {tag}", tag, "HEAD", env=BOT_IDENTITY)
        git(repo, "push", remote, f"refs/tags/{tag}:refs/tags/{tag}", env=env)
    out(f"Tagged {tag} on {sha[:12]}.")
    return tag


def propose_release(
    repo, remote, target, base, version, kind, token, dry_run, out, api
):
    branch = f"release/v{version}"
    title = f"chore(release): v{version}"
    with remote_env(remote, token) as env:
        refs = remote_refs(repo, remote, "refs/heads/release/v*", env, "heads")
        existing = sorted(
            n
            for n in (ref.removeprefix("refs/heads/") for ref in refs)
            if RELEASE_BRANCH_RE.match(n)
        )
        if dry_run:
            out(
                f"Would push {branch} with one commit '{title}' and open a pull request into {target}."
            )
            for name in existing:
                if name != branch:
                    out(f"Would close the superseded {name} and delete its branch.")
            return
        if api is None:
            raise NotConfigured(
                "no GitHub repository given: pass --github-repo or set GITHUB_REPOSITORY"
            )
        open_prs = api.open_release_pull_requests()
        if branch not in existing:
            text = bump_manifest_text(git(repo, "show", f"HEAD:{MANIFEST}"), version)
            commit = release_commit(repo, text, title)
            git(repo, "push", remote, f"{commit}:refs/heads/{branch}", env=env)
        if branch in open_prs:
            out(f"{branch} is already proposed.")
        else:
            description = (
                f"Automated release proposal for v{version} ({kind} bump from {base}). "
                "Review it and merge it to tag the release."
            )
            api.create_pull_request(branch, target, title, description)
            out(f"Proposed release v{version} ({kind} bump from {base}) as {branch}.")
        for name in sorted((set(existing) | set(open_prs)) - {branch}):
            if name in open_prs:
                api.close_pull_request(open_prs[name], f"Superseded by v{version}.")
            if name in existing:
                git(repo, "push", remote, "--delete", name, env=env)
            out(f"Withdrew the superseded {name}.")


def report_tag(env, tag):
    """Tell the workflow which tag was created, through GITHUB_OUTPUT."""
    path = env.get("GITHUB_OUTPUT")
    if tag and path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"tag={tag}\n")


def publish(
    repo, remote="origin", target="main", dry_run=False, env=None, out=emit, api=None
):
    env = os.environ if env is None else env
    token = env.get("RELEASE_TOKEN", "")
    if token:
        _secrets.add(token)
    base = latest_tag(repo)
    if base is None:
        raise NotConfigured(
            "no baseline release tag: create an annotated tag vX.Y.Z on main first"
        )
    if not dry_run and not token:
        raise NotConfigured("RELEASE_TOKEN is not set")
    version = manifest_version(repo, "HEAD")
    if parse_version(version) > parse_version(base[1:]):
        tag = tag_release(repo, remote, version, token, dry_run, out)
        report_tag(env, tag)
        return None
    result = next_version(repo, base)
    if result is None:
        out(f"No releasable changes since {base}.")
        return None
    return propose_release(
        repo, remote, target, base, result[0], result[1], token, dry_run, out, api
    )


def verify_tag(repo, tag, main_ref="origin/main"):
    match = TAG_RE.match(tag or "")
    if not match:
        raise ReleaseError(f"tag name must look like vX.Y.Z, got {tag!r}")
    ref = f"refs/tags/{tag}"
    if git(repo, "cat-file", "-t", ref, check=False).strip() != "tag":
        raise ReleaseError(f"{tag} must be an annotated tag")
    commit = git(repo, "rev-list", "-n", "1", ref).strip()
    version = manifest_version(repo, commit)
    if version != match.group(1):
        raise ReleaseError(
            f"{tag} does not match the plugin version {version!r} at that commit"
        )
    on_main = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, main_ref],
        cwd=repo,
        capture_output=True,
    )
    if on_main.returncode != 0:
        raise ReleaseError(f"the tagged commit is not on {main_ref}")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="release.py", description=__doc__.splitlines()[0]
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("next", "publish", "verify-tag"):
        command = commands.add_parser(name)
        command.add_argument("--repo", default=".")
        if name == "publish":
            command.add_argument("--remote", default="origin")
            command.add_argument("--target", default="main")
            command.add_argument("--dry-run", action="store_true")
            command.add_argument(
                "--github-repo", help="owner/name; defaults to GITHUB_REPOSITORY"
            )
            command.add_argument(
                "--api-url",
                help="GitHub API URL; defaults to GITHUB_API_URL or api.github.com",
            )
        if name == "verify-tag":
            command.add_argument("tag", nargs="?")
            command.add_argument("--main-ref", default="origin/main")
    return parser


def main(argv=None, env=None):
    env = os.environ if env is None else env
    args = build_parser().parse_args(argv)
    try:
        if args.command == "next":
            result = next_version(args.repo)
            if result:
                print(result[0])
        elif args.command == "publish":
            slug = args.github_repo or env.get("GITHUB_REPOSITORY", "")
            token = env.get("RELEASE_TOKEN", "")
            api = (
                GitHubApi(
                    args.api_url or env.get("GITHUB_API_URL") or API_URL, slug, token
                )
                if slug and token
                else None
            )
            publish(args.repo, args.remote, args.target, args.dry_run, env, api=api)
        else:
            verify_tag(args.repo, args.tag or "", args.main_ref)
            emit(f"{args.tag} is a valid release tag.")
    except NotConfigured as error:
        print(
            f"release automation is not configured: {redact(str(error))}",
            file=sys.stderr,
        )
        return EX_CONFIG
    except (ReleaseError, ValueError) as error:
        print(f"error: {redact(str(error))}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
