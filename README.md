# omg

[![Security](https://github.com/ei06125/omg-claude-plugin/actions/workflows/security.yml/badge.svg)](https://github.com/ei06125/omg-claude-plugin/actions/workflows/security.yml)
[![Quality](https://github.com/ei06125/omg-claude-plugin/actions/workflows/quality.yml/badge.svg)](https://github.com/ei06125/omg-claude-plugin/actions/workflows/quality.yml)
[![Tests](https://github.com/ei06125/omg-claude-plugin/actions/workflows/tests.yml/badge.svg)](https://github.com/ei06125/omg-claude-plugin/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Claude Code plugin for the OhMyGod (omg) dev ecosystem.

## Layout

```
.claude-plugin/plugin.json   plugin manifest (points into .claude/)
.claude/                     Claude Code only: agents/, skills/, commands/, hooks/
.agents/                     shared across agents: policies, standards, procedures, rules, guidelines
documentation/               repo documentation
sources/                     source code (MCP servers, libraries)
tests/                       unit, integration, system, acceptance, performance, fuzzing, security
configs/                     packaged configuration files
tools/                       development tooling (git, docker, cmake, cargo, ...)
```

## Skills

| Command | What it does | Spec |
|---|---|---|
| `/omg:hello` | Replies "Hello Pedro." and nothing else | [omg-hello](documentation/Product/Features/omg-hello.md) |

The plugin is not installed globally, so a plain `claude` session in a new terminal does not have it.
There is no `marketplace.json` yet, so there is no persistent install: load it per session with
`--plugin-dir` (see Develop).

## Develop

Load the working tree without installing. Run it from outside this repo, otherwise
`.claude/` is also loaded as project config and hides plugin discovery problems:

```bash
claude --plugin-dir <path-to-this-repo>
```

Validate the manifest:

```bash
claude plugin validate .
```

Run the tests. Features are specified in `documentation/Product/Features/` and executed as Gherkin
scenarios in `tests/acceptance/`:

```bash
uv run pytest                  # scenarios that need no claude CLI; same as the CI test job
uv run pytest -m claude_cli    # scenarios that need an authenticated claude CLI and make real model calls
```

## Tooling and secrets detection

Dev tooling is managed with `uv` (`pyproject.toml`, `uv.lock`). One-time setup:

```bash
uv sync
uv run pre-commit install
```

Layers, all using `.gitleaks.toml` as the single rule set:

- pre-commit: `gitleaks` on staged changes, `detect-private-key`, `uv-lock` (keeps `uv.lock` in sync).
- GitHub Actions (`.github/workflows/`): separate security, quality, and test workflows run for pull
  requests and pushes to `main`. Gitleaks scans the complete history; quality runs the remaining
  pre-commit hooks; tests runs `uv run pytest`.
- GitLab CI (`.gitlab-ci.yml`) retains equivalent jobs for the private downstream repository.
- `.gitleaks.toml` extends the default rules with `omg-pat-assignment`, which catches hardcoded
  `*_PAT` values that the default generic rule misses.

Pull requests are assigned to their authors and labeled from changed paths. Merging requires an
`Approved` label after the `Approved label` status check is configured as required in the `main`
ruleset.

Run everything manually:

```bash
uv run pre-commit run --all-files
gitleaks git --redact --verbose
```

Test the GitLab CI jobs locally (needs a running Docker engine):

```bash
brew install gitlab-ci-local
tools/ci-local.sh              # all jobs
tools/ci-local.sh gitleaks     # one job
```

The wrapper runs from a throwaway clone with your current files overlaid, including new untracked files. Don't run `gitlab-ci-local`
directly from a git worktree: its `.git` is a pointer file that doesn't resolve in the job container,
so gitleaks scans 0 commits and still passes. The CI `uv` image is pulled from Docker Hub (`astral/uv`),
which serves the same digest as `ghcr.io/astral-sh/uv`.

Versions are pinned by immutable hash, with the human-readable tag kept next to it:

- pre-commit `rev:` is a commit SHA with a `# frozen: <tag>` comment.
- GitHub Actions use full commit SHAs with version comments.
- CI images are `image:<tag>@sha256:<index digest>`.
- Python dependencies are hash-locked in `uv.lock`.

Bump Gitleaks together in `.pre-commit-config.yaml`, `.github/workflows/security.yml`, the GitLab
security job, and the local installation. Keep the local uv installation, `uv-pre-commit` revision,
GitHub setup action configuration, and GitLab CI image compatible.

Resolve new pins:

```bash
git ls-remote https://github.com/<owner>/<repo> 'refs/tags/<tag>*'   # commit SHA (use the ^{} line if present)
docker buildx imagetools inspect <image>:<tag> | head -3             # image index digest
```

## Manifest notes

- `skills` and `commands` accept directories.
- `agents` only accepts a list of `.md` files, and replaces the default `agents/` scan.
  Add each new agent to `plugin.json` explicitly.
- `hooks`: add a `hooks` path to `plugin.json` once `.claude/hooks/hooks.json` exists.

## License

MIT, see [LICENSE](LICENSE).
