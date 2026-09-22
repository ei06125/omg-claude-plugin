---
name: prepare-subtask
description: Turns a SUBTASK-rank GitHub issue into a verbatim recipe, runs it on a small local model through the omg delegate MCP tool, checks the result, and retries. Invoke as /omg:prepare-subtask <issue-number> [path], or automatically whenever a TASK-rank process needs a SUBTASK's acceptance criteria satisfied.
argument-hint: "issue number, optional path"
---

`/omg:prepare-subtask <issue-number> [path]` turns one SUBTASK issue into a checked delegate run. `path` defaults
to the current working directory; it is the worktree or directory the recipe operates in. This skill was written
after a free-form delegation to a small model silently skipped 2 of 13 files, while a verbatim numbered recipe on
the same model got 13 of 13 in a third of the time — small models need the checklist to already exist.

## 1. Fetch and validate the issue

Run `gh issue view <issue-number> --json number,title,body,labels`. Refuse and stop if the title is not tagged
`[06_SUBTASKS]`: this skill only handles SUBTASK rank. Report the refusal; do not guess a different rank's
behaviour.

## 2. Read the Objective and Acceptance criteria

Extract the issue's `## Objective` and `## Acceptance criteria` sections. Only unticked criteria are in scope.

## 3. Inspect the target (not delegated)

Using your own Read, Grep and Glob tools against `path`, find the concrete files and content the criteria
describe. This step is yours: it needs codebase judgment a small model should not be asked to supply.

## 4. Write the recipe (not delegated)

You, the invoking agent, write the recipe from the issue's Objective and Acceptance criteria yourself. Recipe
authoring is not delegated to the acting model; a small model given a goal instead of a checklist misses steps.
The recipe must be:

- **Verbatim**: exact commands or exact edits, not a paraphrased goal.
- **Numbered**: one step at a time, in order.
- **Idempotent**: running it again over already-correct files must be a no-op, because Check-Act reruns it in
  full rather than patching it.

End the recipe with a step whose output proves the result, and tell the model to reply with that output.

## 5. Do: call `delegate`

Call the `delegate` MCP tool with:

- `task`: the recipe text.
- `volumes`: `[{"host_path": path, "mode": "rw"}]`.
- `backend`/`model`: the acting model, `gemma4:12b` or `gpt-oss:20b`. Default `gemma4:12b`, since at the time of
  writing it is the one confirmed served; use `gpt-oss:20b` only when the caller asks for it or `gemma4:12b` is
  unavailable. Never substitute a model the caller did not name and this skill does not allow.
- `commands`: list only what the recipe uses, exactly — never a wildcard such as `"*"`, which would grant the
  acting model an unscoped shell.
- `timeout_seconds`: enough for a short recipe (a few minutes); do not set the ceiling.

Wait for `completion.json` in the returned `run_dir` before continuing.

## 6. Check: prefer a deterministic command

If every unticked acceptance criterion can be verified by a command you can run yourself (a `grep`, a `diff`, the
test suite), run that deterministic command directly. Do not spend a model call on something code can already
decide. Only when a criterion needs judgment a command cannot render, delegate a Check task to a same-tier
reviewer model (the same tier as acting: `gemma4:12b` or `gpt-oss:20b`), with its own verbatim recipe (for
example: run `diff`, then report `PASS` or `FAIL` with reasons). A reviewer call that returns no parseable
verdict is a failed round, never a pass and never the ground truth on its own.

## 7. Act: retry or stop

If Check fails, rerun step 5 (the recipe is idempotent) up to `max_rounds` (default 3). After the last round's
failure, stop and report `FAIL` with what is still wrong. Never guess a fix outside the recipe, and never lower
the acceptance criteria to make it pass.

## 8. Report, and stop there

Report: which files changed, the pass/fail outcome, and the round count. This skill's job ends here.

- Never run `git add`, `git commit` or `git push`.
- Never open a pull request.
- Never tick an acceptance box in the issue.

The TASK owner reviews the result, fixes anything wrong, and is the one who commits, pushes and opens the pull
request.
