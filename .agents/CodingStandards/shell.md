# Shell Coding Standard

## Language standard

Use Shell only for small orchestration wrappers.

- Executable scripts have an explicit interpreter and `set -euo pipefail`.
- Keep scripts compatible with the interpreter named by the shebang.
- Use two-space indentation and no tabs.
- Quote expansions.
- Use lower-case local variables and upper-case exported or immutable
  environment variables.
- Avoid `eval`, aliases, parsing `ls`, and implicit temporary-file locations.
- Use `mktemp -d` with a cleanup trap.
- Prefer functions over repeated command sequences.

Use the [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
as advisory guidance where it does not conflict with repository rules.

## Tooling

- [ShellCheck](https://www.shellcheck.net/) checks correctness and portability.
  `.shellcheckrc` is normative. `shellcheck-py` supplies the pinned binary
  through uv; pre-commit invokes `uv run shellcheck`.
- [shfmt](https://github.com/mvdan/sh) provides deterministic formatting.
  `.editorconfig` is normative, with Bash syntax, two-space indentation,
  binary operators on the next line, and indented case bodies.

```bash
uv run shellcheck tools/*.sh
shfmt -d tools
```

ShellCheck is written in Haskell and shfmt in Go. They are deliberate
exceptions to the Rust preference. Rust-based Shellharden focuses on safe
quoting transformations, complements ShellCheck, and is not a general
formatter or full replacement.

Pin shfmt before adding it to CI. Do not depend on an unpinned system binary.
