---
name: git-submit
description: Submits the current Git work as a focused pull request by staging task-relevant files, committing with hooks enabled, pushing the branch, and creating or updating its PR. Only runs when invoked as /omg:git-submit.
disable-model-invocation: true
---

# Git Submit

Invoking this skill authorizes staging relevant files, creating one commit, pushing the current work branch, and creating a pull request. It does not authorize merging, auto-merging, tagging, releases, force-pushing, deleting branches, applying infrastructure, or including unrelated changes.

## Submit

1. Inspect repository instructions (`CLAUDE.md`, `AGENTS.md`), status, diffs, branch, remotes, and recent history. Preserve unrelated user changes.
2. Identify only files belonging to the current task. If relevance is ambiguous or unrelated edits overlap required files, stop and ask.
3. Do not submit directly from a protected or long-lived branch. Create a short-lived branch when needed, following repository conventions. Prefer Conventional Branch names such as `feature/<description>`, `bugfix/<description>`, or `chore/<description>`.
4. Determine the PR base from repository configuration and established workflow. Prefer `dev` when it is the active integration branch; otherwise use the default branch. Ask when evidence conflicts.
5. Run proportionate validation before committing. Do not bypass, disable, or skip repository hooks.
6. Stage explicit task-relevant paths. Never use `git add --all`, `git add .`, or broad globs unless the user explicitly requests every working-tree change.
7. Review the staged diff and secret-sensitive filenames before committing. Scan staged content for credentials, absolute home-directory paths, local usernames, hostnames, personal email addresses, and other machine identity values. Prefer repository-relative paths; when a machine-local artifact cannot be made portable, unstage it and add its pattern to `.gitignore` when that ignore rule belongs to the task. Stop on unexpected files, generated secrets, or failed checks.
8. Create a new commit with a short imperative subject scoped to the task. Never amend an existing commit.
9. Push normally and establish upstream tracking when needed. Never force-push.
10. If an open PR already exists for the branch, update it instead of creating a duplicate. Otherwise create a PR (`gh pr create`, or `glab mr create` on GitLab) with a concise title and body covering the outcome and validation. Do not merge it.
11. Report the branch, commit, PR URL, validation result, and anything intentionally excluded.

If there are no relevant uncommitted changes, do not create an empty commit. Push or create the PR only when the branch contains task commits not already submitted; otherwise report that nothing needs submission.
