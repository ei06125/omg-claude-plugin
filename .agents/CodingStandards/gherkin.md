# Gherkin Coding Standard

## Language standard

Follow the official [Gherkin reference](https://cucumber.io/docs/gherkin/reference/):

- Use two-space indentation and one `Feature` per capability.
- Describe business behavior, not implementation or UI mechanics.
- Give every scenario a unique, outcome-oriented name.
- Use `Given` for context, `When` for one principal action, and `Then` for an
  externally observable result.
- Use `And` or `But` only when it preserves the preceding keyword's grammar.
- Keep scenarios independent and deterministic. Do not depend on execution
  order or shared state.
- Use `Background` only for short, universal context.
- Use `Scenario Outline` only when examples express meaningful behavioral
  variants.
- Keep step wording reusable by domain meaning. Do not combine multiple actions
  in one step.
- Tag scenarios by execution characteristic, such as `@claude_cli`, rather
  than ownership or temporary status.

## Enforcement

`pytest-bdd` uses the official Cucumber `gherkin-official` parser. Treat syntax
errors, undefined or ambiguous steps, collection failures, and failed scenarios
as CI failures.

```bash
uv run pytest
```

The official Cucumber parser is the selected Gherkin tool. No third-party
semantic linter is required. AI-assisted review may assess domain language,
scenario clarity, duplication, and behavioral quality; those findings remain
review decisions rather than deterministic lint failures. See
[the scored evaluation](gherkin-linter-evaluation.md).

If a semantic rule becomes stable and objectively testable, implement it over
the existing official parser. Do not add a second parser or a new runtime
solely for formatting.
