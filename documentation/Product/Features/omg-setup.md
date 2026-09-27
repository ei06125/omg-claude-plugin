# omg-setup

- **Status:** In development, awaiting owner acceptance
- **Executable spec:** `tests/acceptance/features/omg-setup.feature`
- **Implementation:** `.claude/skills/setup/SKILL.md`

## Summary

`/omg:setup [session-name]` starts a working session. It checks that the access the owner's work needs is in place
(GitHub through the `gh` CLI, Atlassian and Slack through their MCP tools, all behind personal access tokens in
environment variables), runs the project's own agent setup when the project declares one, reads the workspace's
`DIARY.md` and `PEDRO.md`, and opens a new `session-*` directory in `.claude/`. It is the user-level `/setup` skill
moved into the plugin, adapted only where a plugin skill differs: it is namespaced (`/omg:setup`) and it uses the
real `$ARGUMENTS` placeholder for the optional session name.

## Problem

Every session starts with the same checks and the same reading: are the tokens and connectors usable, what did the
last session leave in the diary, who is the user. Done from memory it gets skipped or done differently each time,
and a missing token is found halfway through a task. The skill exists at user level only, so it is not versioned,
tested or shared with the rest of the plugin. The Codex copy is also older and lacks the project-local agent setup.

## User story

As the owner of the omg plugin, I want to run `/omg:setup` at the start of a session so that access is verified and
the workspace's diary and profile are read before any work begins.

## Behaviour

| # | Acceptance criterion | Checked by | Runs in CI |
|---|---|---|---|
| 1 | The `setup` skill exists in the plugin's skills directory | Structural scenario | Yes |
| 2 | The skill runs both on explicit invocation and when the model chooses it, and its front matter takes the `session-name` argument | Structural scenario | Yes |
| 3 | The skill checks that the required personal access tokens exist in environment variables | Structural scenario | Yes |
| 4 | The skill checks access to GitHub through the `gh` CLI, and to Atlassian (Confluence, Jira) and Slack through their MCP tools | Structural scenario | Yes |
| 5 | The skill determines the active `AGENTNAME`, compares it case-insensitively with the agent name declared in the project's `CLAUDE.md`, and when they match runs the project-local `.claude/skills/setup-$AGENTNAME/SKILL.md` once; otherwise it skips it | Structural scenario | Yes |
| 6 | The skill checks `.claude/` for existing session directories, reads `DIARY.md` for a recap and `PEDRO.md` for user profiling | Structural scenario | Yes |
| 7 | The skill creates `session-$DATETIME` when no argument is given, and `session-$ARGUMENTS/` when one is | Structural scenario | Yes |
| 8 | The skill uses the `$ARGUMENTS` placeholder and no unresolved `{{ARGUMENT}}` template | Structural scenario | Yes |
| 9 | The skill states its global rules: never print the tokens, prefer scripts to autonomous actions, iterate on scripts and add tests, and set up gitleaks and other secret detection in a Git repository | Structural scenario | Yes |

All criteria are checked by reading the skill file; no model call. There is no `@claude_cli` scenario: a real run
reads the owner's environment variables and connectors, so it is not safe to automate.

## Out of scope

- Storing or generating tokens. The skill only checks that they exist and never prints them.
- Writing the summary, diary or memory at the end of a session. That is `/omg:teardown`.
- The project-local `setup-$AGENTNAME` skills themselves. This skill only finds and runs one.
- Removing the user-level `/setup` skill. It keeps working next to `/omg:setup`.
- Keeping the Codex skill, the user-level skill and this one in sync automatically.

## Constraints and notes

- The source is the user-level Claude skill, not the Codex one, because it is the newer version with the
  project-local agent setup.
- The original used `"${{ARGUMENT}}"`, which Claude Code does not substitute, so the session name was never applied.
  It is now `"$ARGUMENTS"`. The quotes stay so an empty argument reads as `""`.
- The `$DATETIME` format is left to the agent, as in the original. Existing session directories already use more
  than one format, so none is imposed here.
- The skill file is checked for the presence of its rules, not for whether a model follows them.

## How to verify

```bash
uv run pytest                    # criteria 1-9, reads the skill file, no model calls, same as CI
tools/ci-local.sh                # the GitLab CI jobs, locally
```

## Acceptance

Done by the owner only: review the feature and check the CI result. The author does not tick these.

- [ ] CI is green
- [ ] Feature review passed
