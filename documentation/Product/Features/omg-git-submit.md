# omg-git-submit

- **Status:** In development, awaiting owner acceptance
- **Executable spec:** `tests/acceptance/features/omg-git-submit.feature`
- **Implementation:** `.claude/skills/git-submit/SKILL.md`

## Summary

`/omg:git-submit` submits the current Git work as a focused pull request: it stages only task-relevant files,
creates one commit with hooks enabled, pushes the branch, and creates the pull request or updates the one that
already exists. It is the Claude Code port of the Codex skill `omg-git-submit`, kept identical in behaviour and
adapted only where Claude Code differs: the skill is namespaced by the plugin (`/omg:git-submit`, so no `omg-`
prefix) and only runs when invoked explicitly.

## Problem

Submitting work is a fixed sequence with many ways to go wrong: staging everything with `git add .`, amending an
earlier commit, skipping hooks, force-pushing, leaking a home-directory path or a personal email into a commit,
opening a second PR for the same branch, or merging without being asked. Codex already has a skill that fixes the
sequence. Claude Code needs the same one so both agents submit work the same way.

## User story

As the owner of the omg plugin, I want to run `/omg:git-submit` so that finished work becomes one focused pull
request without me repeating the same rules each time.

## Behaviour

| # | Acceptance criterion | Checked by | Runs in CI |
|---|---|---|---|
| 1 | The `git-submit` skill exists in the plugin's skills directory | Structural scenario | Yes |
| 2 | The skill runs only when invoked explicitly; the model cannot trigger it on its own | Structural scenario | Yes |
| 3 | The skill states that invoking it authorizes staging relevant files, one commit, a push of the work branch and a pull request | Structural scenario | Yes |
| 4 | The skill states that invoking it does not authorize merging, auto-merging, tagging, releases, force-pushing, deleting branches, applying infrastructure or including unrelated changes | Structural scenario | Yes |
| 5 | The skill instructs staging explicit task-relevant paths and never `git add --all` or `git add .` | Structural scenario | Yes |
| 6 | The skill instructs never amending a commit, never force-pushing, and never bypassing, disabling or skipping hooks | Structural scenario | Yes |
| 7 | The skill instructs never submitting directly from a protected or long-lived branch, and creating a short-lived branch instead | Structural scenario | Yes |
| 8 | The skill instructs scanning staged content for credentials, absolute home-directory paths, local usernames, hostnames and personal email addresses before committing | Structural scenario | Yes |
| 9 | The skill instructs stopping and asking when relevance is ambiguous, and asking when the PR base evidence conflicts | Structural scenario | Yes |
| 10 | The skill instructs updating an existing open PR instead of creating a duplicate, and never merging it | Structural scenario | Yes |
| 11 | The skill instructs creating no empty commit when there are no relevant changes | Structural scenario | Yes |
| 12 | The skill instructs reporting the branch, commit, PR URL, validation result and anything intentionally excluded | Structural scenario | Yes |

All criteria are checked by reading the skill file; no model call. There is no `@claude_cli` scenario: a real run
commits, pushes and opens a pull request, so it is not safe to automate against this repository.

## Out of scope

- Merging, auto-merging, tagging, releases, force-pushing, deleting branches and applying infrastructure. The
  skill states it does not authorize them.
- Following a different workflow per host. The skill names `gh pr` and `glab mr` for creating the pull request
  and otherwise stays host-neutral.
- Keeping the Codex skill and this one in sync automatically. This is a one-time port.
- The Codex-only `agents/openai.yaml` interface file. Claude Code has no equivalent.

## Constraints and notes

- The skill file is checked for the presence of its rules, not for whether a model follows them. Only a real
  submission shows that, and none is automated here.
- `disable-model-invocation: true` is the one deliberate difference from the Codex skill. Codex relies on the
  description ("Use when the user explicitly asks") to keep the model from submitting on its own. Claude Code can
  enforce it, and the owner's rules already forbid committing, pushing or opening a pull request unasked.
- The skill's own commit rules (never amend, never skip hooks) match the owner's global agent rules.

## How to verify

```bash
uv run pytest                    # criteria 1-12, reads the skill file, no model calls, same as CI
tools/ci-local.sh                # the GitLab CI jobs, locally
```

## Acceptance

Done by the owner only: review the feature and check the CI result. The author does not tick these.

- [ ] CI is green
- [ ] Feature review passed
