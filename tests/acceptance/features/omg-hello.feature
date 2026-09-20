Feature: omg-hello
  As the owner of the omg plugin
  I want to run /omg:hello
  So that I can confirm the plugin is loaded and its skills are reachable

  Scenario: The plugin ships the hello skill
    Given the omg plugin manifest
    Then the manifest points at the skills directory ".claude/skills"
    And the "hello" skill exists in that directory

  Scenario: The hello skill runs only when invoked explicitly
    Given the "hello" skill
    Then the model cannot invoke it on its own

  Scenario: The hello skill requires an exact reply
    Given the "hello" skill
    Then its instructions require the reply "Hello Pedro." and nothing else

  @claude_cli
  Scenario: The plugin manifest is valid
    Given the omg plugin manifest
    When I validate the plugin with Claude Code
    Then validation passes

  @claude_cli
  Scenario: Running /omg:hello in a new session
    Given a new Claude Code session outside the repository with the omg plugin loaded
    When I run "/omg:hello"
    Then the reply is exactly "Hello Pedro."
