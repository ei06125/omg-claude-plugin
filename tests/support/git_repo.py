"""Real git repositories for release tests. Nothing here is mocked."""

import json
import os
import subprocess
from pathlib import Path

MANIFEST = ".claude-plugin/plugin.json"
SPEC_DIR = "documentation/Product/Features"

MANIFEST_TEXT = """{
  "name": "omg",
  "version": "%s",
  "description": "Test plugin",
  "keywords": [
    "omg",
    "skills"
  ],
  "skills": "./.claude/skills/"
}
"""

def clean_env(**extra):
    """Environment for running the release script: nothing inherited from the CI job.

    Tests also run inside CI, where variables such as GITHUB_* and possibly RELEASE_TOKEN exist. The script must
    never see them.
    """
    keep = ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR")
    env = {key: os.environ[key] for key in keep if key in os.environ}
    env.update(extra)
    return env


def git(cwd, *args, env=None):
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, **(env or {})},
    )
    return result.stdout.strip()


class Repo:
    def __init__(self, path: Path):
        self.path = path
        path.mkdir(parents=True, exist_ok=True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test Author")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "tag.gpgsign", "false")

    def git(self, *args, env=None):
        return git(self.path, *args, env=env)

    def write(self, relpath, text):
        target = self.path / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def read(self, relpath):
        return (self.path / relpath).read_text()

    def commit(self, message="change"):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def tag(self, name, annotated=True):
        if annotated:
            self.git("tag", "-a", "-m", f"Release {name}", name)
        else:
            self.git("tag", name)

    def write_spec(self, name, status, breaking=False, summary="A feature."):
        lines = [f"# {name}", "", f"- **Status:** {status}"]
        if breaking:
            lines.append("- **Breaking:** yes")
        lines += ["", "## Summary", "", summary, ""]
        self.write(f"{SPEC_DIR}/{name}.md", "\n".join(lines))

    def manifest_version(self):
        return json.loads(self.read(MANIFEST))["version"]

    def set_manifest_version(self, version):
        self.write(MANIFEST, MANIFEST_TEXT % version)


def make_released_repo(base: Path, version="0.1.0", tagged=True) -> Repo:
    repo = Repo(base / "work")
    repo.set_manifest_version(version)
    repo.write("README.md", "readme\n")
    repo.write(".claude/skills/hello/SKILL.md", "hello v1\n")
    repo.write("tests/test_x.py", "x = 1\n")
    repo.write_spec("omg-hello", "Accepted")
    repo.write_spec("omg-search", "In development")
    repo.commit("Initial")
    if tagged:
        repo.tag(f"v{version}")
    return repo


class Origin:
    """A bare repository standing in for the git side of GitHub."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        git(path.parent, "init", "-q", "--bare", "-b", "main", str(path))

    def connect(self, repo: Repo):
        repo.git("remote", "add", "origin", str(self.path))
        repo.git("push", "-q", "origin", "main", "--tags")

    def git(self, *args):
        return git(self.path, *args)

    def branches(self):
        out = self.git("for-each-ref", "--format=%(refname:short)", "refs/heads")
        return set(out.split()) if out else set()

    def release_branches(self):
        return {b for b in self.branches() if b.startswith("release/")}

    def tags(self):
        out = self.git("for-each-ref", "--format=%(refname:short)", "refs/tags")
        return set(out.split()) if out else set()

    def object_type(self, ref):
        return self.git("cat-file", "-t", ref)

    def file_at(self, ref, relpath):
        return self.git("show", f"{ref}:{relpath}")

    def changed_files(self, ref, base):
        out = self.git("diff", "--name-only", base, ref)
        return set(out.split()) if out else set()
