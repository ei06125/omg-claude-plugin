# omg-hello

- **Status:** In development, awaiting owner acceptance
- **Executable spec:** `tests/acceptance/features/omg-hello.feature`
- **Implementation:** `.claude/skills/hello/SKILL.md`

## Summary

`/omg:hello` is the first skill of the omg plugin. It replies `Hello Pedro.` and nothing else. Its purpose is to
prove that the plugin loads and that its skills are reachable from a Claude Code session.

## User story

As the owner of the omg plugin, I want to run `/omg:hello` so that I can confirm the plugin is loaded and its
skills are reachable.

## Behaviour

| # | Acceptance criterion | Checked by | Runs in CI |
|---|---|---|---|
| 1 | The plugin manifest points at `.claude/skills` and the `hello` skill exists there | Structural scenario | Yes |
| 2 | The skill runs only when invoked explicitly; the model cannot trigger it on its own | Structural scenario | Yes |
| 3 | The skill's instructions require the reply `Hello Pedro.` and nothing else | Structural scenario | Yes |
| 4 | The plugin manifest passes `claude plugin validate` | Claude CLI scenario | No |
| 5 | In a new session outside this repository, with the plugin loaded, `/omg:hello` replies exactly `Hello Pedro.` | Claude CLI scenario | No |

Criteria 4 and 5 need an authenticated `claude` CLI and criterion 5 makes a real model call, so they are tagged
`@claude_cli` and run locally only.

## Out of scope

- Persistent installation. The repository has no `marketplace.json`, so the plugin is loaded per session with
  `claude --plugin-dir`.
- Configurable names, arguments or languages.
- Other agents (Codex, Gemini, ...).

## Constraints and notes

- The name in the reply is hard-coded by design.
- The user-level `/hello` skill is unrelated. The plugin skill is namespaced as `/omg:hello`.
- Criteria 1 to 3 prove the skill is wired and instructed correctly. Only criterion 5 shows the model follows
  the instruction, and because model output is not deterministic, one passing run is evidence, not a guarantee.

## How to verify

```bash
uv run pytest                    # criteria 1-3, no model calls, same as CI
uv run pytest -m claude_cli      # criteria 4-5, needs an authenticated claude CLI
tools/ci-local.sh                # the GitLab CI jobs, locally
```

## Acceptance

Done by the owner only: review the feature and check the CI result. The author does not tick these.

- [ ] CI is green
- [ ] Feature review passed
