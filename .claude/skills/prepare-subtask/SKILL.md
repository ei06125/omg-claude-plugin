---
name: prepare-subtask
description: Reads a TASK-rank GitHub issue and creates one linked SUBTASK issue per goal, each with verbatim instructions. Invoke as /omg:prepare-subtask <task-issue-number>.
argument-hint: "task issue number"
---

`/omg:prepare-subtask <task-issue-number>`. Run `whoami` now; address the person it names in step 4.

## 1. PLAN

- `gh issue view <task-issue-number> --json number,title,body,labels`. Refuse and stop if the title is not
  tagged `[05_TASKS]`.
- List the goals: the `## Objective` line and every unticked line under `## Acceptance criteria`.
- Find the highest existing `SUBTASK-NNN` number (`gh issue list --search "[06_SUBTASKS] SUBTASK-" --state all
  --json title`), so new numbers never repeat one already used.

## 2. DO

For each goal, write and create one issue yourself — never delegate this:

- Title: `[06_SUBTASKS] SUBTASK-<next number>: <goal, short>`.
- Body sections: `## Objective`, `## Acceptance criteria`, `## Instructions`, `## Parent` (the TASK issue's URL).
- `## Instructions` is verbatim, numbered, system-tool commands — never a prose goal.
- `gh issue create --title "..." --body "..."`.
- Link it as a native sub-issue of the TASK: get both issues' node ids (`gh issue view <n> --json id -q .id`),
  then `gh api graphql -f query='mutation($p:ID!,$s:ID!){addSubIssue(input:{issueId:$p,subIssueId:$s}){issue{number}}}' -f p=<task-node-id> -f s=<subtask-node-id>`.

## 3. CHECK

- `gh api repos/<owner>/<repo>/issues/<task-issue-number>/sub_issues --jq 'length'` equals the number of goals.
- Every created SUBTASK's body has an `## Instructions` section with numbered steps.

## 4. ACT

- Both checks pass: tell the person from `whoami` the TASK issue and the list of SUBTASK issues created.
- Either check fails: tell the person from `whoami` exactly what is wrong. Do not retry, do not guess a fix.

Never run `git add`, `git commit` or `git push`. Never open a pull request. Never tick a box in the TASK issue.
