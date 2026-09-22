# Python Coding Standard

## Language standard

- Follow [PEP 8](https://peps.python.org/pep-0008/) for layout, naming, imports,
  and readability.
- Use four-space indentation, `snake_case` for functions and variables,
  `PascalCase` for classes, and `UPPER_CASE` for constants.
- Follow [PEP 257](https://peps.python.org/pep-0257/) when a public module,
  class, or function needs a docstring. Do not add docstrings that merely
  restate a name or implementation.
- Add type annotations to production-facing APIs and non-obvious data
  structures. Tests and small fixtures may rely on inference.
- Prefer `pathlib`, context managers, explicit encodings for persistent text,
  and argument-list subprocess calls.
- Set `subprocess.run(check=True)` when failure should abort. Use
  `check=False` explicitly when the return code is the assertion subject.
- Name tests by observable behavior: `test_<observable_behavior>`.

## Tooling

[Ruff](https://docs.astral.sh/ruff/) is the single formatter, import sorter,
and linter. It replaces overlapping Black, isort, Flake8, pyupgrade, and common
plugin installations.

The normative configuration is `[tool.ruff]` in `pyproject.toml`. Do not create
a second `ruff.toml` or `.ruff.toml`. The repository targets Python 3.12, uses
an 88-character line length, and enables `E4`, `E7`, `E9`, `F`, `I`, `UP`,
`B`, `SIM`, and `RUF`.

```bash
uv run ruff check .
uv run ruff format --check .
```

Ruff and its official pre-commit hooks are locked. The lint hook may apply
safe fixes; formatting runs afterward.

## Deferred tooling

Static typing is premature for the current test-only Python surface. Reassess
Pyright or mypy when `sources/` contains a public Python package. Prefer a
Rust-based implementation when maturity and compatibility are comparable.
