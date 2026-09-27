---
name: setup
description: Asserts access requirements and initializes the session. Invoke as /omg:setup.
argument-hint: "[session-name]"
---

Assert Access Requirements and Initializes Session.

## Access Requirements

Check if the required Personal Access Tokens (PATs) exist in the env. vars to:

- Check access to GitHub platform via GH CLI tool
- Check access to Atlassian platforms (Confluence, Jira) via MCP tool
- Check access to Slack platform via MCP tool

## Initialize Session

Check the current workspace and setup session.

- Determine the active `AGENTNAME`.
- Read the project-local `CLAUDE.md` and identify its declared agent name.
- Compare the names case-insensitively. If they match, lowercase `AGENTNAME`,
  look for the project-local `/setup-$AGENTNAME` skill at
  `.claude/skills/setup-$AGENTNAME/SKILL.md`, and run it once.
- Skip the project-local agent setup if the names do not match or the skill does
  not exist.
- Check .claude/ dir for session-$DATETIME dirs.
- Check for DIARY.md file (read for recap)
- Check for PEDRO.md file (read for user profiling)
- Create a new session-$DATETIME if "$ARGUMENTS" is empty.
- Otherwise, create a "session-$ARGUMENTS/" dir in .claude for new session.

## Global Rules

- Never print the PATs
- Prefer scripts to autonomous actions
- Iterate on scripts and add tests if needed
- If working on a git repo, setup gitleaks and other secret detection tools
