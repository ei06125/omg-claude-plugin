Feature: omg-prepare-subtask
  As the owner of the omg plugin, or an agent acting for them at TASK rank
  I want to call /omg:prepare-subtask with a SUBTASK issue
  So that its acceptance criteria become a checked, retried recipe run on a small local model, without me writing the recipe or the delegate call by hand

  Scenario: The plugin ships the prepare-subtask skill
    Given the omg plugin manifest
    Then the "prepare-subtask" skill exists in that directory

  Scenario: The skill runs both on explicit invocation and when the model chooses it
    Given the "prepare-subtask" skill
    Then the model can invoke it on its own
    And its instructions name the invocation "/omg:prepare-subtask"

  Scenario: The skill refuses an issue that is not a SUBTASK
    Given the "prepare-subtask" skill
    Then its instructions require refusing an issue whose title is not tagged "[06_SUBTASKS]"

  Scenario: The recipe is authored by the invoking agent, not delegated
    Given the "prepare-subtask" skill
    Then its instructions require the invoking agent to write the recipe from the issue's Objective and Acceptance criteria
    And its instructions state that recipe authoring is not delegated

  Scenario: The recipe must be verbatim, numbered and idempotent
    Given the "prepare-subtask" skill
    Then its instructions require the recipe to be verbatim
    And its instructions require the recipe to be numbered
    And its instructions require the recipe to be idempotent

  Scenario: The acting model is a small model, defaulting to gemma4:12b
    Given the "prepare-subtask" skill
    Then its instructions name "gemma4:12b" and "gpt-oss:20b" as the acting model choices
    And its instructions default the acting model to "gemma4:12b"

  Scenario: The commands allowlist is scoped to the recipe, never a wildcard
    Given the "prepare-subtask" skill
    Then its instructions require the delegate "commands" argument to list only what the recipe uses
    And its instructions forbid a wildcard in "commands"

  Scenario: Check prefers a deterministic command over a reviewer model
    Given the "prepare-subtask" skill
    Then its instructions require a deterministic command when the acceptance criteria allow one
    And its instructions require a same-tier reviewer model only when a deterministic command cannot decide it

  Scenario: The Do and Check loop is bounded and fails honestly
    Given the "prepare-subtask" skill
    Then its instructions bound the number of rounds
    And its instructions require reporting failure after the last round instead of a guessed fix

  Scenario: The skill never commits, pushes, opens a pull request or ticks a box
    Given the "prepare-subtask" skill
    Then its instructions forbid running "git add", "git commit" and "git push"
    And its instructions forbid opening a pull request
    And its instructions forbid ticking an acceptance box in the issue

  @claude_cli
  Scenario: Running /omg:prepare-subtask on a real disposable SUBTASK issue
    Given a disposable SUBTASK issue with a mechanically checkable criterion
    When I run "/omg:prepare-subtask" on that issue
    Then only the file the criterion describes changed
    And the deterministic gate for that criterion passes
    And no commit was made in the working directory
