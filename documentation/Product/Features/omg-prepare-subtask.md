# omg-prepare-subtask

- **Status:** In development, awaiting owner acceptance
- **Executable spec:** `tests/acceptance/features/omg-prepare-subtask.feature`
- **Implementation:** `.claude/skills/prepare-subtask/SKILL.md`
- **Issue:** <https://github.com/ei06125/omg-claude-plugin/issues/35>

## Summary

`/omg:prepare-subtask <task-issue-number>` reads a `[05_TASKS]` GitHub issue and creates one `[06_SUBTASKS]`
issue per goal in its Objective and Acceptance criteria. Each new issue is linked as a native GitHub sub-issue of
the TASK and carries a verbatim, numbered, system-tool `## Instructions` section. It checks the count and the
instructions, then reports the outcome to whoever ran it. It never executes a SUBTASK, never calls a model to do
its writing, and never touches git or the TASK's own acceptance boxes.

## Problem

TASK's purpose is to decompose a STORY's work into SUBTASKs. Doing that by hand is slow and drifts: SUBTASKs go
unlinked, their instructions stay vague, and numbering collides with issues already created. A small model
executing a SUBTASK later needs a checklist, not a goal — the fable-to-sonnet test showed a free-form goal made
`gemma4:12b` silently skip work, while a verbatim numbered recipe on the same model did not. That means the
instructions must already be verbatim when the SUBTASK is created, not written later by whoever executes it.

## User story

As the TASK-rank process (interactive, or a small model such as `qwen3.8:27b-mlx` or `gpt-oss:120b`), I want to
call `/omg:prepare-subtask` with a TASK issue so that each of its goals becomes a linked SUBTASK issue with
instructions precise enough to execute later, without writing each one by hand.

## How it works

1. **PLAN:** read the TASK issue, refuse it if it is not tagged `[05_TASKS]`, list its goals, and find the
   highest `SUBTASK-NNN` number already in use.
2. **DO:** for each goal, write and create one SUBTASK issue, with a verbatim numbered `## Instructions` section,
   and link it as a native sub-issue of the TASK.
3. **CHECK:** the sub-issue count matches the goal count, and every created SUBTASK has a real `## Instructions`
   section.
4. **ACT:** report the outcome to whoever ran it (`whoami`) — the created issues on success, or exactly what is
   wrong on failure. No retry, no guessed fix.

## Behaviour

| # | Acceptance criterion | Checked by | Runs in CI |
|---|---|---|---|
| 1 | The skill exists at `.claude/skills/prepare-subtask/SKILL.md`, is invocable by the model (not `disable-model-invocation`), and its front matter names `/omg:prepare-subtask` | Structural scenario | Yes |
| 2 | The skill instructs refusing an issue whose title is not tagged `[05_TASKS]` | Structural scenario | Yes |
| 3 | The skill instructs finding the highest existing `SUBTASK-NNN` number first, so new numbers never repeat one already used | Structural scenario | Yes |
| 4 | The skill instructs writing and creating one issue per goal itself, never delegating that writing | Structural scenario | Yes |
| 5 | The skill instructs each SUBTASK's `## Instructions` to be verbatim, numbered, system-tool commands, never a prose goal | Structural scenario | Yes |
| 6 | The skill instructs linking each created SUBTASK as a native GitHub sub-issue of the TASK | Structural scenario | Yes |
| 7 | The skill instructs CHECK to verify the sub-issue count equals the goal count and every SUBTASK has a numbered `## Instructions` section | Structural scenario | Yes |
| 8 | The skill instructs ACT to report to the person `whoami` names, and never to retry or guess a fix on failure | Structural scenario | Yes |
| 9 | The skill instructs never running `git add`, `git commit` or `git push`, never opening a pull request, and never ticking a box in the TASK issue | Structural scenario | Yes |
| 10 | Given a real disposable TASK issue with two goals, running the skill creates exactly two linked SUBTASK issues, each with a numbered `## Instructions` section, and the report names Pedro | Claude CLI scenario | No |

Criteria 1 to 9 are checked by reading the skill file; no model call. Criterion 10 needs the real `claude` CLI and
`gh`, so it is tagged `@claude_cli` and runs locally only.

## Out of scope

- Any rank other than this TASK-to-SUBTASK step. THEME, INITIATIVE, EPIC, STORY and the rest of TASK's own
  behaviour are separate skills, built one at a time.
- Executing a SUBTASK. That is a separate concern; this skill only creates the ticket and its instructions.
- Delegating to a model through `delegate` or any sandbox. This skill only reads and writes GitHub issues.
- Committing, pushing, opening a pull request, or ticking acceptance boxes.
- Retrying automatically on a failed CHECK; ACT reports the problem instead.

## Constraints and notes

- SUBTASK numbering continues from the highest `SUBTASK-NNN` already used anywhere in the repository's issues,
  open or closed, so two TASKs prepared in parallel do not collide by chance (a real race is still possible and
  is not solved here).
- Native GitHub sub-issue linking is the hierarchy, not a markdown `## Parent` link alone: the CHECK step reads
  the real `sub_issues` REST endpoint, not the issue body.
- `## Instructions` is checked for structure (a section with numbered steps), not for correctness; nothing here
  verifies the commands actually work. That happens when a SUBTASK is executed, not when it is prepared.

## How to verify

```bash
uv run pytest                    # criteria 1-9, reads the skill file, no model calls, same as CI
uv run pytest -m claude_cli       # criterion 10, needs the real claude CLI and gh, creates and closes real issues
```

## Acceptance

Done by the owner only: review the feature and check the CI result. The author does not tick these.

- [ ] CI is green
- [ ] Feature review passed
