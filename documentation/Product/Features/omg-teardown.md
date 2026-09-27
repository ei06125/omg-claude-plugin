# omg-teardown

- **Status:** In development, awaiting owner acceptance
- **Executable spec:** `tests/acceptance/features/omg-teardown.feature`
- **Implementation:** `.claude/skills/teardown/SKILL.md`

## Summary

`/omg:teardown [session-name]` ends a working session and keeps what matters from it. It saves the scripts created
during the session into a `scripts/` directory, writes a summary of the conversation into the session directory and
into the workspace's `DIARY.md`, records cross-session information there too, saves information unrelated to the
workspace in long-term memory, saves user profiling data into `PEDRO.md`, and commits what it wrote. It is the
counterpart of `/omg:setup`. It is the user-level `/teardown` skill moved into the plugin, adapted where a plugin
skill differs: it is namespaced (`/omg:teardown`), it only runs when invoked explicitly, it uses the real
`$ARGUMENTS` placeholder, and its commit is limited to what it wrote.

## Problem

A session's useful output is scattered: scripts left wherever they were written, decisions only in the
conversation, facts about the user nowhere. The next session then starts from nothing, and `/omg:setup` has no
diary to read. The skill exists at user level only, so it is not versioned, tested or shared with the rest of the
plugin. Its last instruction, "if working on a git repo, commit", names no files, so run at the end of a session it
can commit unrelated work, and it can put `PEDRO.md`, which holds personal profiling data, into a repository that
is later pushed.

## User story

As the owner of the omg plugin, I want to run `/omg:teardown` at the end of a session so that its scripts, summary
and cross-session facts are saved for the next session without me collecting them by hand.

## Behaviour

| # | Acceptance criterion | Checked by | Runs in CI |
|---|---|---|---|
| 1 | The `teardown` skill exists in the plugin's skills directory | Structural scenario | Yes |
| 2 | The skill runs only when invoked explicitly; the model cannot trigger it on its own | Structural scenario | Yes |
| 3 | The skill's front matter takes the `session-name` argument | Structural scenario | Yes |
| 4 | The skill saves every script created into a `scripts/` directory within its working directory | Structural scenario | Yes |
| 5 | The skill saves the conversation summary into `session-$ARGUMENTS` when an argument is given, otherwise into the last `session-$TIMESTAMP/` directory | Structural scenario | Yes |
| 6 | The skill saves the summary and cross-session information into `DIARY.md` within `.claude/`, creating it if missing | Structural scenario | Yes |
| 7 | The skill saves important information unrelated to the workspace in long-term memory | Structural scenario | Yes |
| 8 | The skill saves user profiling data into `PEDRO.md` | Structural scenario | Yes |
| 9 | In a Git repository the skill commits only the files it wrote, excluding `PEDRO.md` and ignored files, staged by explicit path, as a new commit with hooks enabled, never amending and never pushing | Structural scenario | Yes |
| 10 | The skill uses the `$ARGUMENTS` placeholder and no unresolved `{{ARGUMENT}}` template | Structural scenario | Yes |

All criteria are checked by reading the skill file; no model call. There is no `@claude_cli` scenario: a real run
writes to the owner's memory and commits to the repository it runs in, so it is not safe to automate.

## Out of scope

- Reading the diary or profile back. That is `/omg:setup`.
- Pushing, opening a pull request or merging. The owner submits the work with `/omg:git-submit`.
- Deciding what counts as important. The skill states what to save and where; the agent judges the content.
- Removing the user-level `/teardown` skill. It keeps working next to `/omg:teardown`.
- Keeping the Codex skill, the user-level skill and this one in sync automatically.

## Constraints and notes

- The commit rule is the deliberate difference from the source skill, which says only "commit". Limiting it to the
  files the skill wrote, and leaving out `PEDRO.md`, follows the owner's rules: no committing unrelated changes, no
  amending, no pushing, and personal data stays out of shared history. It is the one line to relax if the owner
  wants the source behaviour back.
- `disable-model-invocation: true` follows from the commit: invoking `/omg:teardown` is the explicit instruction to
  commit, and the model must not do it on its own.
- The original used `"${{ARGUMENT}}"`, which Claude Code does not substitute, so the session name was never
  applied. It is now `"$ARGUMENTS"`.
- The skill file is checked for the presence of its rules, not for whether a model follows them.

## How to verify

```bash
uv run pytest                    # criteria 1-10, reads the skill file, no model calls, same as CI
tools/ci-local.sh                # the GitLab CI jobs, locally
```

## Acceptance

Done by the owner only: review the feature and check the CI result. The author does not tick these.

- [ ] CI is green
- [ ] Feature review passed
