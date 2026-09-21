# omg-bootstrap-architecture

- **Status:** In development, awaiting owner acceptance
- **Executable spec:** `tests/acceptance/features/omg-bootstrap-architecture.feature`
- **Implementation:** not yet written
- **Issue:** <https://github.com/ei06125/omg-claude-plugin/issues/29>

## Summary

`bootstrap_project_architecture` is the only tool of the omg plugin's first MCP server. It scaffolds a
standard documentation and governance layout under a target directory and writes
`documentation/Technical/ARCHITECTURE.md`, which lists the target's top-level directories and files. It
replaces a shell stub that only logged `To be implemented`.

## Problem

- The plugin ships no MCP server.
- The shell function meant to bootstrap a project's architecture only logs `To be implemented`, so the
  documentation layout and `ARCHITECTURE.md` of a new project are created by hand.
- The older shell helper that generates `ARCHITECTURE.md` appends on every run, so running it twice duplicates
  its entries.

## User story

As the owner of the omg plugin, I want a tool `bootstrap_project_architecture` so that I can scaffold the
plugin's standard layout and regenerate its `ARCHITECTURE.md` for a target directory without overwriting
what already exists.

## Behaviour

| # | Acceptance criterion | Checked by | Runs in CI |
|---|---|---|---|
| 1 | `.mcp.json` registers exactly one MCP server, launched with `uv run` and implemented in Python with the official `mcp` SDK, whose dependency is pinned in `uv.lock` | Structural scenario | Yes |
| 2 | Tool discovery on the server returns exactly one tool, named `bootstrap_project_architecture` | Structural scenario | Yes |
| 3 | The tool accepts `path` (default: current working directory) and `dry_run` (default: `false`) | Behavioural scenario | Yes |
| 4 | The tool reports the paths created, the paths skipped because they already exist, and whether `ARCHITECTURE.md` was written or left unchanged | Behavioural scenario | Yes |
| 5 | The scaffold creates `documentation/Product/Features`, `documentation/Technical`, `.agents/Governance` and `tests/acceptance/features`, creating only what is missing and never overwriting an existing file or directory | Behavioural scenario | Yes |
| 6 | `documentation/Technical/ARCHITECTURE.md` lists one section per top-level directory and file of the target, directories first, in `LC_ALL=C` order, and omits `.git`, git-ignored entries and secret-bearing entries such as `.env` | Behavioural scenario | Yes |
| 7 | Regenerating `ARCHITECTURE.md` with no change to the tree leaves the file byte-identical | Behavioural scenario | Yes |
| 8 | With `dry_run` set to `true` nothing is written and the output reports what would be created | Behavioural scenario | Yes |
| 9 | When `path` contains a symlink that points outside it, nothing is written outside `path` | Behavioural scenario | Yes |

## Out of scope

- The content of the governance documents under `.agents/Governance`.
- The system-info MCP fixture (issue #21).
- Changing the shell alias in the owner's DotFiles.
- Deleting or migrating existing files.

## Constraints and notes

- The target directory is untrusted input: writes are confined to it, so a symlink pointing outside it
  cannot be used to escape it.
- `ARCHITECTURE.md` regeneration is idempotent: a second run over an unchanged tree is a no-op at the byte
  level.
- Git-ignored and secret-bearing entries are omitted so the document can be committed without leaking them.
- The tests use synthetic temporary directories only, make no model calls and run in the existing
  `uv run pytest` CI job, so every criterion is checked in CI.

## How to verify

```bash
uv run pytest                     # criteria 1-9, synthetic temp dirs, no model calls, same as CI
```

## Acceptance

Done by the owner only: review the feature and check the CI result. The author does not tick these.

- [ ] CI is green
- [ ] Feature review passed
