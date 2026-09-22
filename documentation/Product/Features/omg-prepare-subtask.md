# omg-prepare-subtask

- **Status:** In development, awaiting owner acceptance
- **Executable spec:** `tests/acceptance/features/omg-prepare-subtask.feature`
- **Implementation:** `.claude/skills/prepare-subtask/SKILL.md`
- **Issue:** <https://github.com/ei06125/omg-claude-plugin/issues/35>

## Summary

`/omg:prepare-subtask <issue-number> [path]` is the first rank-specific skill of the omg ticket system. Given a
`06_SUBTASKS` GitHub issue, the invoking agent reads its Objective and Acceptance criteria, writes a verbatim,
idempotent, numbered recipe for the work, and runs it through the `delegate` MCP tool on a small local model. It
checks the result — with a deterministic command when the criteria allow one, otherwise a same-tier reviewer
model — and reruns the recipe on failure, up to a round limit. It never commits, pushes, opens a pull request, or
ticks the issue's acceptance boxes.

## Problem

Our first delegation test gave a free-form goal ("change every file") to `gemma4:12b` and it silently did 11 of
13. A verbatim numbered recipe on the same model did 13 of 13, in a third of the time, because each opencode tool
call is a full model round trip and a vague multi-file task invites the model to stop early. Small models need
the checklist to already exist; they should not be asked to invent one. Without a skill that builds and checks
that checklist, every future SUBTASK-rank piece of work repeats this by hand.

## User story

As the owner of the omg plugin, or an agent acting for them at TASK rank, I want to call `/omg:prepare-subtask`
with a SUBTASK issue so that its acceptance criteria are turned into a recipe, run on a small local model inside
an isolated sandbox, checked, and retried, without me writing the recipe or the delegate call by hand each time.

## How it works

1. Fetch the issue (`gh issue view <n> --json number,title,body,labels`). Refuse if its title is not tagged
   `[06_SUBTASKS]`.
2. Read its Objective and unticked Acceptance criteria.
3. Inspect `path` (default: the current working directory) with the invoking agent's own file tools to find the
   concrete files the criteria describe. This step is not delegated: it needs codebase judgment.
4. Write a verbatim, numbered, idempotent recipe: exact shell commands or exact edits, one step at a time, ending
   with a step whose output proves the result.
5. **Do:** call `delegate` with the recipe as `task`, `path` mounted `rw`, `backend`/`model` for the chosen acting
   model, and `commands` scoped to exactly what the recipe uses. Wait for `completion.json`.
6. **Check:** if every acceptance criterion can be verified by a command (a `grep`, a `diff`, the test suite), run
   that command directly — no model call. Otherwise call `delegate` again with a same-tier reviewer model, given a
   verbatim recipe of its own (for example `diff -r`, then a pass/fail report).
7. **Act:** on failure, rerun step 5 (the recipe is idempotent) up to `max_rounds`. On the last round's failure,
   stop and report failure; never guess a fix.
8. Report: which files changed, the pass/fail outcome, and the round count. Do not `git add`, `commit`, `push`,
   open a pull request, or tick a box in the issue.

## Behaviour

| # | Acceptance criterion | Checked by | Runs in CI |
|---|---|---|---|
| 1 | The skill exists at `.claude/skills/prepare-subtask/SKILL.md`, is invocable by the model (not `disable-model-invocation`), and its front matter names `/omg:prepare-subtask` | Structural scenario | Yes |
| 2 | The skill instructs refusing an issue whose title is not tagged `[06_SUBTASKS]` | Structural scenario | Yes |
| 3 | The skill instructs writing the recipe itself from the issue's Objective and Acceptance criteria; it does not delegate recipe authoring | Structural scenario | Yes |
| 4 | The skill requires the recipe to be verbatim, numbered and idempotent | Structural scenario | Yes |
| 5 | The skill names the acting model as `gemma4:12b` or `gpt-oss:20b`, defaulting to `gemma4:12b` | Structural scenario | Yes |
| 6 | The skill instructs a `commands` list scoped to what the recipe uses, never a wildcard | Structural scenario | Yes |
| 7 | The skill instructs preferring a deterministic command for Check when the acceptance criteria allow one, and only delegating to a same-tier reviewer model otherwise | Structural scenario | Yes |
| 8 | The skill instructs a bounded number of Do/Check rounds (default 3) and a plain failure report when the last round still fails | Structural scenario | Yes |
| 9 | The skill instructs never running `git add`, `commit`, `push`, opening a pull request, or ticking an acceptance box in the issue | Structural scenario | Yes |
| 10 | Given a real disposable SUBTASK issue with a mechanically checkable criterion, running the skill changes only the described file, the deterministic gate passes, and no commit is made | Claude CLI scenario | No |

Criteria 1 to 9 are checked by reading the skill file; no model call. Criterion 10 needs the real `claude` CLI,
`delegate`, sbx and a running backend, so it is tagged `@claude_cli` and runs locally only.

## Out of scope

- Any rank other than SUBTASK. THEME, INITIATIVE, EPIC, STORY and TASK are separate skills, built one at a time.
- Committing, pushing, opening a pull request, or ticking acceptance boxes: the TASK owner's job.
- Creating or editing the GitHub issue.
- Choosing volumes or network policy beyond `path`: SUBTASK work is assumed to fit inside one already-checked-out
  directory with no network need, matching `delegate`'s own default of nothing reachable but the backend.
- A general-purpose recipe generator for arbitrary goals; this skill only turns one SUBTASK issue into one recipe.

## Constraints and notes

- `path` defaults to the current working directory because SUBTASKs are expected to run inside a worktree a TASK
  or the owner already created; this skill does not create worktrees.
- The recipe must be idempotent because Act reruns it in full rather than patching it; the fable-to-sonnet test
  confirmed a `sed`-based recipe is safe to rerun.
- A reviewer model that gives no parseable verdict is a failure of that round, not a pass; the loop must never
  fall back to treating "unclear" as either PASS or as the ground truth.
- `gpt-oss:20b` is named as an allowed acting model by the owner, but at the time of writing it is not served by
  a running backend; the skill must name what to start, per `delegate`'s own `backend_unreachable` hint, not
  silently substitute another model.

## Open questions for the owner

1. **Criterion 10's fixture.** It needs a real SUBTASK issue to run against. Proposal: the scenario creates a
   small disposable issue in this repo (title `[06_SUBTASKS] SUBTASK-TEST: ...`, a trivial file-content
   criterion), runs the skill, asserts the outcome, then closes it. Confirm, or say how you'd rather fixture it.
2. **Round limit.** Defaulting to 3, matching the fable-to-sonnet test. Fixed in the skill, or should it be a
   caller argument?

## How to verify

```bash
uv run pytest                    # criteria 1-9, reads the skill file, no model calls, same as CI
uv run pytest -m claude_cli       # criterion 10, needs the real claude CLI, delegate, sbx, a running backend
```

## Acceptance

Done by the owner only: review the feature and check the CI result. The author does not tick these.

- [ ] CI is green
- [ ] Feature review passed
