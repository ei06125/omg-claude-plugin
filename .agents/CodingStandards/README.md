# Coding Standards

## Scope

These standards cover the languages GitHub currently detects in this
repository: Python, Gherkin, and Shell. Supporting configuration and
documentation formats are covered separately.

The GitHub language percentages measure bytes, not architectural importance.
Apply standards by file type and risk, not by percentage.

## Standards index

- [Python](python.md)
- [Gherkin](gherkin.md)
- [Shell](shell.md)
- [Supporting data and documentation formats](data-formats.md)
- [Gherkin linter evaluation](gherkin-linter-evaluation.md)

## Authority hierarchy

1. Repository rules in `AGENTS.md` and accepted architecture decisions.
2. Tool configuration committed to the repository.
3. Language-community standards referenced by each language document.
4. Local convention in the file being changed.

Automation is authoritative where prose and configuration disagree. A rule
that cannot be checked automatically should be short, necessary, and reviewed
manually.

## Tool selection

Prefer mature Rust-based developer tools when capability, maintenance, and
integration quality are comparable. Current examples are Ruff for Python,
ripgrep for repository search, and uv for Python environments. Future
candidates include rumdl for Markdown and Taplo for TOML.

Implementation language is a selection criterion, not a reason to replace a
more capable domain-standard tool. Prefer tools owned by official language or
framework organizations. Individual-maintainer tools require stronger evidence
of maintenance, adoption, licensing, and supply-chain safety.

Evaluate tools in containers with repository contents copied inside. Do not
install trial tools globally on the host.

## Enforcement plan

1. Keep normative settings in committed configuration files.
2. Run the same locked tools locally and in CI.
3. Separate formatter-only changes from semantic lint fixes.
4. Do not hide baseline findings with broad exclusions.
5. Enable new rule families in isolated pull requests.
6. Record narrow exceptions beside the relevant tool configuration.
7. Reassess deferred tools when the source surface or defect rate grows.

All versions must be locked. Pre-commit repositories use immutable commit SHAs
with a readable release tag beside them.

## Repository organization

Keep mandatory language rules in this directory. Store broader control
frameworks in `.agents/Governance/` and accepted tool decisions in
`documentation/Technical/` ADRs. Do not duplicate normative rules across
files; link to this index.

## `.gitignore` policy

Curate `.gitignore` for tools actually used by this repository. Do not replace
it wholesale with the 227-line Toptal gitignore.io combination for macOS,
Python, and Visual Studio Code.

The current file includes Python caches, environments, coverage, builds, Ruff,
local secrets, Claude local settings, GitLab CI local state, and Gitleaks
reports. Keep `uv.lock` tracked. Do not blanket-ignore `.vscode/`; shared
settings and recommended extensions may be intentionally versioned.
