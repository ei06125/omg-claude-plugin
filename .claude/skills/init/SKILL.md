---
name: init
description: Initializes a repository that has no AGENTS.md with canonical documentation, a minimal agent philosophy, Claude forwarding, and visible agent workspaces. Only runs when invoked as /omg:init.
disable-model-invocation: true
---

# Init

## Exit Guard

Before setup, discovery, directory creation, or any other mutation, check for `AGENTS.md` at the repository root. If it exists, do not read, rewrite, move, or modify it or any other repository file. Report that initialization was skipped and exit immediately.

## Initialize

When root `AGENTS.md` does not exist, run after the `setup` skill when available. Do not depend on setup: locate the repository root, inspect Git status, and discover relevant files directly when necessary.

1. Find root-level and nested `README.md` and `CLAUDE.md` files case-insensitively. Read them before editing and respect nested instructions.
2. Create the visible repository workspaces `.agents/Governance/` and `.claude/`:

   ```text
   .agents/
   └── Governance/
   .claude/
   ```

   Preserve existing contents. Do not add either directory to `.gitignore` or `.git/info/exclude`.
3. Find a root-level directory named `doc`, `docs`, or `documentation`, case-insensitively. Reuse it and preserve its spelling. If none exists, create:

   ```text
   Documentation/
   ├── Legal/
   ├── Product/
   └── Technical/
       ├── ARCHITECTURE.md
       ├── BUILDING.md
       ├── DEPLOYING.md
       └── TESTING.md
   ```

4. When a documentation root already exists, create only missing `Legal/`, `Product/`, `Technical/`, and Technical files. Never overwrite useful existing documents.

## Organize Documentation

Move, rather than duplicate, relevant material from README.md and CLAUDE.md:

- Architecture, module boundaries, data flow, and design decisions → `Technical/ARCHITECTURE.md`.
- Prerequisites, setup, build commands, and generated outputs → `Technical/BUILDING.md`.
- Environments, releases, packaging, infrastructure, and deployment → `Technical/DEPLOYING.md`.
- Test strategy, commands, fixtures, coverage, CI, and regression expectations → `Technical/TESTING.md`.

Preserve verified repository facts and commands. Reconcile overlaps. Do not invent missing architecture, environments, commands, or policies.

## Rewrite Guidance

### README.md

Keep the project identity, purpose, quick start, basic usage, badges, licensing notices, and essential links. Replace moved material with short summaries and relative links to the canonical Technical documents. If README.md is missing, create one only from verified repository facts.

### AGENTS.md

Create root `AGENTS.md` with the title `# Agents Philosophy`. Do not add technology, commands, layout, naming, testing, or workflow details discoverable from project files and tools.

Add `## Laws` containing only durable behavioral constraints, including:

- Never print API keys, credentials, secrets or tokens.
- Never bypass required tests, validation, or commit hooks.
- Never commit generated secrets or machine-local artifacts.
- Never rewrite Git history or force-push without explicit authorization.
- Never discard unrelated user changes.

Add `## Governance` and point to `[.agents/Governance/](.agents/Governance/)` for repository-specific governance material.

### CLAUDE.md

Create or replace the root file with a short notice that forwards Claude to `AGENTS.md` through a relative Markdown link and states that AGENTS.md is authoritative. Preserve nested directory-specific CLAUDE instructions and forward only their shared rules to the nearest applicable AGENTS file.

## Verify

- Confirm `.agents/Governance/`, `.claude/`, the documentation structure, AGENTS.md, and CLAUDE.md exist.
- Confirm README and CLAUDE links resolve.
- Confirm moved subjects are not substantially duplicated in README.md or CLAUDE.md.
- Confirm `.agents/` and `.claude/` were not newly ignored.
- Review the diff for lost content, placeholder text, absolute paths, machine identity, or secrets.
- Run documentation validation when the repository provides it.

Report created, rewritten, and preserved files. Do not commit or push unless explicitly requested.
