Feature: omg-init
  As the owner of the omg plugin
  I want to run /omg:init in a new or undocumented repository
  So that it gets canonical documentation and minimal agent guidance without me restructuring it by hand

  Scenario: The plugin ships the init skill
    Given the omg plugin manifest
    Then the "init" skill exists in that directory

  Scenario: The init skill runs only when invoked explicitly
    Given the "init" skill
    Then the model cannot invoke it on its own

  Scenario: The skill exits before any mutation when AGENTS.md already exists
    Given the "init" skill
    Then its instructions require checking for a root AGENTS.md before any mutation
    And its instructions forbid reading or changing any repository file when it exists
    And its instructions require reporting that initialization was skipped

  Scenario: The skill creates the visible agent workspaces
    Given the "init" skill
    Then its instructions require creating the workspaces ".agents/Governance/" and ".claude/"
    And its instructions require preserving their existing contents
    And its instructions forbid adding them to the ignore files

  Scenario: The skill reuses an existing documentation root
    Given the "init" skill
    Then its instructions require reusing an existing "doc", "docs" or "documentation" directory with its spelling
    And its instructions forbid overwriting a useful existing document

  Scenario: The skill creates a documentation root when none exists
    Given the "init" skill
    Then its instructions require creating "Legal/", "Product/" and "Technical/" under "Documentation/"

  Scenario Outline: The Technical documents are created
    Given the "init" skill
    Then its instructions require creating the Technical document "<document>"

    Examples:
      | document        |
      | ARCHITECTURE.md |
      | BUILDING.md     |
      | DEPLOYING.md    |
      | TESTING.md      |

  Scenario: Material is moved into the Technical documents, not duplicated or invented
    Given the "init" skill
    Then its instructions require moving relevant material from README.md and CLAUDE.md rather than duplicating it
    And its instructions forbid inventing missing architecture, environments, commands or policies

  Scenario: README.md keeps its identity and links to the Technical documents
    Given the "init" skill
    Then its instructions require README.md to keep the project identity, quick start and essential links
    And its instructions require short summaries and relative links to the Technical documents

  Scenario: AGENTS.md is a minimal philosophy
    Given the "init" skill
    Then its instructions require AGENTS.md to be titled "# Agents Philosophy"
    And its instructions forbid technology, command, layout, naming, testing and workflow details in it
    And its instructions require a "## Governance" section pointing at ".agents/Governance/"

  Scenario Outline: AGENTS.md states the durable laws
    Given the "init" skill
    Then its instructions require the law "<law>"

    Examples:
      | law                                                                    |
      | Never print API keys, credentials, secrets or tokens                   |
      | Never bypass required tests, validation, or commit hooks               |
      | Never commit generated secrets or machine-local artifacts              |
      | Never rewrite Git history or force-push without explicit authorization |
      | Never discard unrelated user changes                                   |

  Scenario: CLAUDE.md forwards to AGENTS.md
    Given the "init" skill
    Then its instructions require CLAUDE.md to forward to AGENTS.md through a relative link
    And its instructions require CLAUDE.md to state that AGENTS.md is authoritative
    And its instructions require preserving nested CLAUDE.md instructions

  Scenario: The skill verifies its result
    Given the "init" skill
    Then its instructions require confirming that links resolve
    And its instructions require confirming that ".agents/" and ".claude/" were not newly ignored
    And its instructions require reviewing the diff for lost content, placeholder text, absolute paths, machine identity and secrets
    And its instructions require running documentation validation when the repository provides it

  Scenario: The skill reports and does not commit
    Given the "init" skill
    Then its instructions require reporting created, rewritten and preserved files
    And its instructions forbid committing or pushing unless explicitly requested

  Scenario: The skill runs after setup but does not depend on it
    Given the "init" skill
    Then its instructions state that it runs after setup when available and does not depend on it

  @claude_cli
  Scenario: Running /omg:init in a repository that already has AGENTS.md
    Given a repository whose root already has AGENTS.md
    When I run "/omg:init" in it
    Then no file changed and nothing was created
    And the reply says initialization was skipped
