# Gherkin Linter Evaluation

## Scope and scoring

Evaluated on 2026-09-20 through GitHub metadata, manifests, releases, source
trees, and containerized trials against this repository. Scores total 100:

| Criterion | Weight |
|---|---:|
| Ownership and trust; official organizations preferred | 20 |
| Maintenance and recent releases | 20 |
| Parsing, semantic rules, configuration, and diagnostics | 20 |
| Repository and runtime fit | 15 |
| Maturity and adoption | 15 |
| Supply chain and licensing | 10 |

The adoption threshold is 75. A parser's high score does not turn it into a
semantic linter.

## Results

| Candidate | Owner/runtime | Score | Assessment |
|---|---|---:|---|
| [cucumber/gherkin](https://github.com/cucumber/gherkin) | Official Cucumber; multi-language | **87** | Adopted parser baseline; authoritative and active, but syntax-only |
| [gherkin-lint/gherkin-lint](https://github.com/gherkin-lint/gherkin-lint) | Specialist organization; Node.js | **64** | Broad rules and strongest adoption; last release 2023, last push 2024, 78 open issues, deprecated dependencies |
| [dantleech/gherkin-lint-php](https://github.com/dantleech/gherkin-lint-php) | Individual; PHP | **60** | Active and configurable; PHP has no other repository purpose |
| [krrish377/gherkin-lint-plus](https://github.com/krrish377/gherkin-lint-plus) | Individual; Node.js 20+ | **58** | Modern Cucumber packages and broad rules; created in 2026, three stars, one fork, no GitHub release |
| [procitec/gherkin-lint](https://github.com/procitec/gherkin-lint) | Company; Python 3.12+/uv | **55** | Best runtime fit and zero dependencies; beta, absent from PyPI, limited configuration, opinionated findings |
| [kevgo/cucumber-sort](https://github.com/kevgo/cucumber-sort) | Individual; Rust | **41** | Active and Rust-based, but only orders steps; not a general linter and lacks a detected license |
| [funkwerk/gherkin_lint](https://github.com/funkwerk/gherkin_lint) | Company; Ruby | **39** | No source push since 2019 and no release since 2017 |

The official Cucumber organization has maintained parsers and utilities but no
maintained semantic linter. Its former JavaScript linter is archived under
`cucumber-attic` and is disqualified for new adoption.

## Container trials

The repository was copied into temporary containers. Trial tools were installed
only inside those containers, and containers were removed afterward.

- `gherkin-lint` 4.2.4 passed with an empty configuration, but npm reported
  deprecated `gherkin`, `cucumber-messages`, `glob`, `inflight`, and `uuid`
  dependencies. Optional semantic rules are disabled by default.
- `gherkin-lint-plus` 1.0.2 passed with an empty configuration and current
  `@cucumber/gherkin`, but lacks organizational ownership and maturity.
- `procitec/gherkin-lint` 26.1.1 was absent from PyPI and built from its pinned
  GitHub release tarball. It reported ten findings, including requiring
  top-level scenarios at zero indentation and replacing `And` with `*`. These
  conflict with the selected style and are insufficiently configurable.

## Decision

Use the official Cucumber parser supplied through `pytest-bdd` for syntax,
collection, step binding, and execution. Do not add a third-party semantic
linter. Semantic analysis is AI-assisted during review; acceptance remains a
human decision.

If a recurring semantic concern needs deterministic enforcement:

1. Check the official Cucumber organization first.
2. Re-score `gherkin-lint-plus` after sustained releases and adoption.
3. Implement narrow repository-owned rules over `gherkin-official`; do not
   create another parser.
4. Use `gherkin-lint` in a pinned Node container only as a temporary fallback,
   with every enabled rule committed in `.gherkin-lintrc`.

Do not adopt a tool merely because it is written in Rust. Reconsider
`cucumber-sort` independently only if step ordering becomes a real requirement.
