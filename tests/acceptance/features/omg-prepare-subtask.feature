Feature: omg-prepare-subtask
  As the TASK-rank process, interactive or a small model
  I want to call /omg:prepare-subtask with a TASK issue
  So that each of its goals becomes a linked SUBTASK issue with instructions precise enough to execute later, without writing each one by hand

  Scenario: The plugin ships the prepare-subtask skill
    Given the omg plugin manifest
    Then the "prepare-subtask" skill exists in that directory

  Scenario: The skill runs both on explicit invocation and when the model chooses it
    Given the "prepare-subtask" skill
    Then the model can invoke it on its own
    And its instructions name the invocation "/omg:prepare-subtask"

  Scenario: The skill refuses an issue that is not a TASK
    Given the "prepare-subtask" skill
    Then its instructions require refusing an issue whose title is not tagged "[05_TASKS]"

  Scenario: SUBTASK numbers never repeat one already used
    Given the "prepare-subtask" skill
    Then its instructions require finding the highest existing "SUBTASK-NNN" number first
    And its instructions state that new numbers never repeat one already used

  Scenario: Each SUBTASK is written and created by the invoking agent, one per goal
    Given the "prepare-subtask" skill
    Then its instructions require writing and creating one issue per goal
    And its instructions state that writing it is never delegated

  Scenario: Each SUBTASK's instructions are verbatim, numbered, system-tool commands
    Given the "prepare-subtask" skill
    Then its instructions require the "Instructions" section to be verbatim and numbered
    And its instructions forbid a prose goal in that section

  Scenario: Each created SUBTASK is linked as a native sub-issue of the TASK
    Given the "prepare-subtask" skill
    Then its instructions require linking each SUBTASK as a native sub-issue of the TASK

  Scenario: CHECK verifies the count and that every SUBTASK has numbered instructions
    Given the "prepare-subtask" skill
    Then its instructions require the sub-issue count to equal the goal count
    And its instructions require every SUBTASK to have a numbered "Instructions" section

  Scenario: ACT reports to whoami and never retries
    Given the "prepare-subtask" skill
    Then its instructions require reporting to the person "whoami" names
    And its instructions forbid retrying or guessing a fix on failure

  Scenario: The skill never touches git, pull requests or the TASK's acceptance boxes
    Given the "prepare-subtask" skill
    Then its instructions forbid running "git add", "git commit" and "git push"
    And its instructions forbid opening a pull request
    And its instructions forbid ticking a box in the TASK issue

  @claude_cli
  Scenario: Running /omg:prepare-subtask on a real disposable TASK issue
    Given a disposable TASK issue with two goals
    When I run "/omg:prepare-subtask" on that issue
    Then exactly two linked SUBTASK issues were created
    And each has a numbered "Instructions" section
    And the report names Pedro
