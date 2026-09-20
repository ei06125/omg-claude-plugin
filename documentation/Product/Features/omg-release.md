# omg-release

- **Status:** In development, awaiting owner acceptance
- **Executable spec:** `tests/acceptance/features/omg-release.feature`
- **Implementation:** `tools/release.py`, `.github/workflows/release.yml`, `.github/workflows/release-tag.yml`
- **Decision record:** `documentation/Technical/ADR-0002-version-bumps-from-accepted-feature-specs.md`

## Summary

Versioning and tagging are automated without any workflow pushing to `main`. When a releasable change lands on
`main`, a workflow proposes a release pull request that bumps the plugin version. The owner reviews and merges it,
and the workflow then tags the merge commit and starts a tag workflow.

## Problem

- The version is edited by hand (`.claude-plugin/plugin.json` says `0.1.0`) and nothing is tagged.
- Plugin installs are snapshots. A version that never changes may stop updates from being picked up.
- `main` is protected against direct pushes, so a release workflow cannot commit to it.

## User story

As the owner of the omg plugin, I want a release pull request opened for me with the next version, so that I cut a
release by reviewing and merging it, and I stay the only person who merges into `main`.

## Flow

1. A feature pull request is reviewed and merged into `main`.
2. The push to `main` starts the `Release` workflow. It runs the tests itself first, because workflows started by
   the same push run in parallel and have no ordering between them.
3. The release job checks whether `plugin.json` on `main` declares a version newer than the latest tag. If so, an
   untagged release is pending: it creates the annotated tag `vX.Y.Z`, pushes it, and stops.
4. Otherwise it computes the next version from what changed since the latest tag. With nothing releasable, it
   stops.
5. Otherwise it pushes a `release/vX.Y.Z` branch with one commit that bumps `version`, and opens a pull request
   titled `chore(release): vX.Y.Z` through the GitHub API. Open release pull requests for other versions are closed
   with a comment and their branches deleted.
6. Because a workflow opened it, the pull request's `pull_request` checks start in an approval-required state.
   The owner approves the workflow runs, adds the `Approved` label that the `main` ruleset requires, reviews the
   pull request, and merges it.
7. The push to `main` starts the `Release` workflow again. Step 3 tags the release commit and starts the
   `Release tag` workflow.
8. The `Release tag` workflow verifies the tag and runs the tests.

## Behaviour

Version rules are defined in ADR-0002. "Shipped content" is `.claude/`, `.claude-plugin/`, `sources/` and
`configs/`.

| # | Acceptance criterion | Checked by |
|---|---|---|
| 1 | A feature spec whose `Status` becomes `Accepted` since the latest tag bumps MINOR | Scenario, temp git repo |
| 2 | A change to shipped content bumps PATCH | Scenario |
| 3 | Changes only to docs, tests, CI or tooling produce no release | Scenario |
| 4 | When several rules apply, the highest wins, and several accepted specs bump MINOR once | Scenario |
| 5 | A `Breaking: yes` header newly added since the latest tag bumps MINOR below 1.0.0 and MAJOR from 1.0.0 | Scenario |
| 6 | A `Breaking: yes` header already present at the latest tag does not bump again | Scenario |
| 7 | The bump changes `version` in `.claude-plugin/plugin.json` and nothing else | Scenario |
| 8 | A releasable change pushes `release/vX.Y.Z` with one commit on top of `main` and opens one pull request titled `chore(release): vX.Y.Z` from that branch into `main` | Scenario, local remote and fake API |
| 9 | If the pull request for the version is already open, nothing new is pushed or opened. A release branch left without an open pull request gets one, without a new push. Release pull requests for other versions are closed and their branches deleted | Scenario |
| 10 | When `plugin.json` on `main` is newer than the latest tag, the job creates and pushes the annotated tag, reports it to the workflow, and proposes nothing | Scenario |
| 11 | When the version is already tagged and nothing is releasable, the job does nothing | Scenario |
| 12 | A missing baseline tag, a missing token, or a repository that does not allow workflows to create pull requests exits with code 78 and an explanation, shown as a workflow warning | Scenario |
| 13 | A dry run prints the plan and pushes and opens nothing | Scenario |
| 14 | The token never appears in output | Scenario |
| 15 | A tag workflow passes only for a tag named `vX.Y.Z` that is annotated, whose version equals `plugin.json` at that commit, and whose commit is on `main`. Other tag names are rejected before any use | Scenario |
| 16 | On the real repository: the pull request is opened, its checks wait for approval, merging tags the release, and the tag workflow starts | Owner, real workflows |

Criteria 1 to 15 are deterministic and run in CI against real git repositories: a local bare repository stands in
for GitHub's git side and a small local HTTP server stands in for the GitHub API. Business-level behaviour is
Gherkin in `tests/acceptance/`, and the version rule matrix and the API client are plain unit tests in
`tests/unit/`. A local stand-in cannot prove how GitHub itself behaves, which is why criterion 16 is the owner's.

## Design constraints

- `main` stays protected. The workflow only pushes `release/*` branches and `v*` tags.
- The workflow uses the automatic `GITHUB_TOKEN`: short-lived, scoped to the run, and nothing to store or rotate.
  Permissions are declared per job and are the minimum: `contents: write` (branch and tag), `pull-requests: write`
  (open and close release pull requests) and `actions: write` (start the tag workflow).
- Git receives the token through `GIT_ASKPASS` and the API receives it in a header. It is never in a URL or in
  output, and checkout uses `persist-credentials: false`.
- The release commit is built with git plumbing (a temporary index), so the working tree is never touched.
- Pushes made with `GITHUB_TOKEN` start no workflow runs, except `workflow_dispatch` and `repository_dispatch`.
  The tag workflow therefore also has a `workflow_dispatch` trigger, and the release job starts it explicitly.
- The version source of truth is `.claude-plugin/plugin.json`. `pyproject.toml` is not tracked.
- The workflow runs on `main` in a `release` concurrency group without cancelling, with a 5-minute timeout.
- Tag names and other event data are untrusted input: they reach the script through environment variables, are
  validated against `vX.Y.Z`, and never go through a shell.
- Actions are pinned to full commit SHAs, matching the existing workflows.
- No changelog and no GitHub release objects: the tag is the release.

## Setup by the owner

1. In Settings > Actions > General > Workflow permissions, turn on "Allow GitHub Actions to create and approve
   pull requests". It is off by default for personal repositories.
2. Add a tag ruleset for `v*` that blocks updates and deletions, so a published tag is never moved. Do not restrict
   creation: GitHub Actions cannot be added to a ruleset bypass list.
3. After this feature is merged, create the annotated tag `v0.1.0` on that `main` commit. It is the baseline.
   `omg-hello` is `Accepted` in this change, so it counts as already released.

Until the baseline tag exists, or while the setting in step 1 is off, the release job exits with code 78 and shows
a warning without failing the workflow.

## Assumptions to check on the real repository

- The pull request created by the workflow is accepted and its checks wait for approval, as GitHub documents.
- Closing a superseded pull request and deleting its branch works with the job's token.
- `gh workflow run` can start the tag workflow on a tag ref.
- The `release/*` branch push is not blocked by the existing rulesets.
- The governance workflows (`Approval`, `Assign pull request author`, `Label pull request`) run on
  `pull_request_target`. GitHub's documentation does not say whether those runs start for a pull request opened
  with `GITHUB_TOKEN`. Either way the `Approved label` check should pass once the owner adds the label by hand,
  and `Assign pull request author` should not fail for a bot author. If it does, it needs a guard for bot
  authors.

## Out of scope

- Publishing to a marketplace or registry.
- Changelogs, GitHub release objects and pre-release versions such as `-rc.1`.
- Signed tags.
- Automatic detection of breaking changes (deferred in ADR-0002).
- Mirroring to GitLab, which the migration handles separately.
- Installing or updating the plugin on a machine (see the future `omg-install` feature).

## How to verify

```bash
uv run pytest                                    # criteria 1 to 15, same as the Tests workflow
uv run python tools/release.py next              # print the next version for this repository
uv run python tools/release.py publish --dry-run # print what the release job would do
```

Criterion 16 is verified on the real repository by the owner.

## Acceptance

Done by the owner only: review the feature and check the workflow results. The author does not tick these.

- [ ] Workflows are green
- [ ] Feature review passed
