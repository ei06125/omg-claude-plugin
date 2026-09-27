# omg-init

- **Status:** In development, awaiting owner acceptance
- **Executable spec:** `tests/acceptance/features/omg-init.feature`
- **Implementation:** `.claude/skills/init/SKILL.md`

## Summary

`/omg:init` initializes a repository that has no root `AGENTS.md`: it creates the visible agent workspaces, gives
the repository a canonical documentation tree, moves architecture, build, deploy and test material out of
`README.md` and `CLAUDE.md` into it, and writes a minimal `AGENTS.md` plus a `CLAUDE.md` that forwards to it. When a
root `AGENTS.md` already exists it changes nothing and exits. It is the Claude Code port of the Codex skill
`omg-init`, adapted only where Claude Code differs: the plugin namespaces the skill (`/omg:init`, so no `omg-`
prefix), it only runs when invoked explicitly, and the second visible agent workspace is `.claude/` instead of
`.codex/`.

## Problem

A repository without agent guidance makes every agent session rediscover the same facts, and `README.md` and
`CLAUDE.md` slowly fill with material that belongs in architecture, build, deploy and test documents. Doing the
split by hand is slow, and doing it carelessly overwrites useful documents or invents facts. Codex already has a
skill that fixes the procedure and refuses to touch a repository that is already initialized. Claude Code needs the
same one so both agents leave a repository in the same shape.

## User story

As the owner of the omg plugin, I want to run `/omg:init` in a new or undocumented repository so that it gets
canonical documentation and minimal agent guidance without me restructuring it by hand.

## Behaviour

| # | Acceptance criterion | Checked by | Runs in CI |
|---|---|---|---|
| 1 | The `init` skill exists in the plugin's skills directory | Structural scenario | Yes |
| 2 | The skill runs only when invoked explicitly; the model cannot trigger it on its own | Structural scenario | Yes |
| 3 | The skill checks for a root `AGENTS.md` before any mutation, and when it exists touches no repository file, reports that initialization was skipped and exits | Structural scenario | Yes |
| 4 | The skill creates the visible workspaces `.agents/Governance/` and `.claude/`, preserves their contents, and never ignores them | Structural scenario | Yes |
| 5 | The skill reuses an existing `doc`, `docs` or `documentation` directory with its spelling, otherwise creates `Documentation/` with `Legal/`, `Product/` and `Technical/` holding `ARCHITECTURE.md`, `BUILDING.md`, `DEPLOYING.md` and `TESTING.md`, and never overwrites a useful existing document | Structural scenario | Yes |
| 6 | The skill moves rather than duplicates material from `README.md` and `CLAUDE.md` into the Technical documents, and invents nothing | Structural scenario | Yes |
| 7 | The skill keeps `README.md` to identity, quick start and essential links, with short summaries and relative links to the Technical documents | Structural scenario | Yes |
| 8 | The skill writes `AGENTS.md` titled `# Agents Philosophy` with `## Laws` (five durable constraints) and `## Governance` pointing at `.agents/Governance/`, and no technology, command or workflow details | Structural scenario | Yes |
| 9 | The skill writes a short `CLAUDE.md` that forwards to `AGENTS.md` through a relative link, states that `AGENTS.md` is authoritative, and preserves nested `CLAUDE.md` instructions | Structural scenario | Yes |
| 10 | The skill verifies its result: links resolve, moved subjects are not duplicated, `.agents/` and `.claude/` are not newly ignored, the diff has no lost content, placeholders, absolute paths, machine identity or secrets, and documentation validation runs when the repository has it | Structural scenario | Yes |
| 11 | The skill reports created, rewritten and preserved files, and does not commit or push unless explicitly requested | Structural scenario | Yes |
| 12 | The skill runs after `setup` when available but does not depend on it | Structural scenario | Yes |
| 13 | Given a repository whose root already has `AGENTS.md`, running `/omg:init` changes no file and creates nothing | Claude CLI scenario | No |

Criteria 1 to 12 are checked by reading the skill file; no model call. Criterion 13 needs the real `claude` CLI and
makes a model call, so it is tagged `@claude_cli` and runs locally only. It works in a disposable directory outside
this repository.

## Out of scope

- Initializing a repository that already has `AGENTS.md`. The skill exits without reading or changing it.
- Committing or pushing the result. The owner reviews the diff first.
- Verifying the full initialization by a model run. The output depends on each repository's own files, so only the
  guard, which must never write, is exercised for real.
- Keeping the Codex skill and this one in sync automatically. This is a one-time port.
- The Codex-only `agents/openai.yaml` interface file and the `.codex/` workspace.

## Constraints and notes

- `disable-model-invocation: true` is a deliberate difference from the Codex skill. Initialization rewrites
  `README.md` and `CLAUDE.md` and creates directories, so it must only run when the owner asks for it.
- `.claude/` replaces `.codex/` as the second visible workspace. `.agents/Governance/` is unchanged and shared with
  Codex.
- The skill file is checked for the presence of its rules, not for whether a model follows them.

## How to verify

```bash
uv run pytest                    # criteria 1-12, reads the skill file, no model calls, same as CI
uv run pytest -m claude_cli      # criterion 13, needs an authenticated claude CLI
tools/ci-local.sh                # the GitLab CI jobs, locally
```

## Acceptance

Done by the owner only: review the feature and check the CI result. The author does not tick these.

- [ ] CI is green
- [ ] Feature review passed
