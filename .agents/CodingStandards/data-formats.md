# Data and Documentation Format Standard

GitHub Linguist does not include Markdown, YAML, JSON, and TOML in the primary
language bar for this repository, but they remain maintained source artifacts.

| Format | Required validation | Tooling decision |
|---|---|---|
| JSON | Parse with `jq empty` | Use jq; two-space indentation |
| YAML | Parse and run domain-specific validation | yamllint with `.yamllint.yaml` |
| TOML | Parse with the consuming tool | Ruff and uv own their sections; consider Rust-based Taplo later |
| Markdown | Validate headings, lists, links, and fenced code | Rust-based rumdl with `[tool.rumdl]` in `pyproject.toml` |

`.editorconfig` defines UTF-8, LF endings, final newlines, trailing-whitespace
removal, and indentation defaults.

Run the format linters with locked uv dependencies:

```bash
uv run yamllint .
uv run rumdl check .
```

yamllint is the mature YAML-specific exception to the Rust preference. rumdl
is written in Rust, supports GitHub Flavored Markdown, and avoids a Node
runtime. Both tools run through pre-commit and use committed configuration.

Do not introduce Prettier merely to format configuration and documentation. It
would add a Node runtime without covering Python or Shell.
