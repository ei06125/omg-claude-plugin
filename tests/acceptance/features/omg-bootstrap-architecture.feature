Feature: omg-bootstrap-architecture
  As the owner of the omg plugin
  I want a tool bootstrap_project_architecture
  So that I can scaffold the plugin's standard layout and regenerate its ARCHITECTURE.md for a target directory without overwriting what already exists

  Scenario: The plugin registers exactly one MCP server
    Given the omg plugin repository
    Then ".mcp.json" registers exactly one MCP server
    And that server is launched with "uv run"
    And that server is implemented in Python with the "mcp" SDK
    And the "mcp" dependency is pinned in "uv.lock"

  Scenario: Tool discovery returns exactly one tool
    Given the MCP server registered in ".mcp.json"
    When I discover the tools on that server
    Then the tool list contains exactly one tool
    And that tool is named "bootstrap_project_architecture"

  Scenario: Omitting path targets the current working directory
    Given a synthetic project directory
    When I run the tool from the project directory without "path"
    Then all four documented directories exist in the project directory

  Scenario: Omitting dry_run writes to disk
    Given a synthetic project directory
    When I run the tool on the project directory without "dry_run"
    Then all four documented directories exist in the project directory

  Scenario: The report lists created and skipped paths and the ARCHITECTURE.md status
    Given a synthetic project directory
    And the project directory already contains the directory "documentation/Technical"
    When I run the tool on the project directory with dry_run "false"
    Then the tool reports "documentation/Technical" as skipped
    And the tool reports "documentation/Product/Features" as created
    And the report shows ARCHITECTURE.md was written

  Scenario Outline: The scaffold never overwrites the content of an existing directory
    Given a synthetic project directory
    And the project directory already contains "<directory>" holding the file "keep.txt" with the content "original"
    When I run the tool on the project directory with dry_run "false"
    Then all four documented directories exist in the project directory
    And "<directory>/keep.txt" still contains "original"

    Examples:
      | directory                      |
      | documentation/Product/Features |
      | documentation/Technical        |
      | .agents/Governance             |
      | tests/acceptance/features      |

  Scenario: ARCHITECTURE.md lists real entries and omits ignored and secret ones
    Given a synthetic project directory containing "src/", "README.md", "secrets/", ".env" and ".git/"
    And the project directory has a ".gitignore" that ignores "secrets"
    When I run the tool on the project directory with dry_run "false"
    Then "documentation/Technical/ARCHITECTURE.md" lists "src" and "README.md"
    And "documentation/Technical/ARCHITECTURE.md" omits "secrets", ".env" and ".git"

  Scenario: ARCHITECTURE.md lists directories first, then files, in C order
    Given a synthetic project directory containing "b_dir/", "A_dir/", "a_file.md" and "B_file.md"
    When I run the tool on the project directory with dry_run "false"
    Then "documentation/Technical/ARCHITECTURE.md" lists "A_dir", "b_dir", "B_file.md" and "a_file.md" in that order

  Scenario: Regenerating ARCHITECTURE.md over an unchanged tree is a no-op
    Given a synthetic project directory
    When I run the tool on the project directory with dry_run "false"
    And I capture "documentation/Technical/ARCHITECTURE.md" from the project directory
    And I run the tool on the project directory with dry_run "false"
    Then the report shows ARCHITECTURE.md was left unchanged
    And "documentation/Technical/ARCHITECTURE.md" is byte-identical to the captured file

  Scenario: A dry run writes nothing and reports what would be created
    Given a synthetic project directory
    When I run the tool on the project directory with dry_run "true"
    Then the tool reports "documentation/Product/Features" as would be created
    And the project directory is still empty

  Scenario: A symlink pointing outside the target is never written through
    Given a synthetic project directory
    And a separate directory outside the project directory
    And the project directory contains a symlink "documentation" that points to the separate directory
    When I run the tool on the project directory with dry_run "false"
    Then the separate directory is unchanged
