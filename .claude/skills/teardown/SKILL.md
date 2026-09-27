---
name: teardown
description: Terminates session, saving important info to long-term and medium-term memory. Only runs when invoked as /omg:teardown.
argument-hint: "[session-name]"
disable-model-invocation: true
---

Terminates session, saving important info to long-term and medium-term memory.

## Terminate Session

- For all scripts created, save them into a scripts/ dir within its corresponding working dir.
- Save a summary of the conversation into "session-$ARGUMENTS" if "$ARGUMENTS" is given.
- Otherwise, save a summary of the conversation into the last session-$TIMESTAMP/ dir.
- Save the summary also to the DIARY.md within .claude/ dir (create if none).
- Save cross-session information into the DIARY.md as well.
- Save important information unrelated to workspace in long-term memory (~/.claude probably).
- Save User Profiling data (e.g. speech style) into PEDRO.md.
- If working on a git repo, commit only the files this teardown wrote, except PEDRO.md and anything git ignores.
  Stage them by explicit path, create a new commit with hooks enabled, never amend, and do not push.
