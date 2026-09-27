Feature: omg-teardown
  As the owner of the omg plugin
  I want to run /omg:teardown at the end of a session
  So that its scripts, summary and cross-session facts are saved for the next session without me collecting them by hand

  Scenario: The plugin ships the teardown skill
    Given the omg plugin manifest
    Then the "teardown" skill exists in that directory

  Scenario: The teardown skill runs only when invoked explicitly
    Given the "teardown" skill
    Then the model cannot invoke it on its own
    And its front matter takes the "session-name" argument

  Scenario: The skill saves the scripts it created
    Given the "teardown" skill
    Then its instructions require saving every script created into a "scripts/" directory within its working directory

  Scenario: The skill saves the summary into the session directory
    Given the "teardown" skill
    Then its instructions require saving the summary into "session-$ARGUMENTS" when an argument is given
    And its instructions require saving the summary into the last "session-$TIMESTAMP/" directory otherwise

  Scenario: The skill saves the summary and cross-session information into the diary
    Given the "teardown" skill
    Then its instructions require saving the summary into "DIARY.md" within ".claude/", creating it if missing
    And its instructions require saving cross-session information into "DIARY.md"

  Scenario: The skill saves information unrelated to the workspace in long-term memory
    Given the "teardown" skill
    Then its instructions require saving important information unrelated to the workspace in long-term memory

  Scenario: The skill saves user profiling data
    Given the "teardown" skill
    Then its instructions require saving user profiling data into "PEDRO.md"

  Scenario Outline: The commit is limited to what the skill wrote
    Given the "teardown" skill
    Then its instructions state the commit rule "<rule>"

    Examples:
      | rule                                                                |
      | If working on a git repo, commit only the files this teardown wrote |
      | except PEDRO.md and anything git ignores                            |
      | Stage them by explicit path                                         |
      | create a new commit with hooks enabled                              |
      | never amend                                                         |
      | do not push                                                         |

  Scenario: The skill uses the real argument placeholder
    Given the "teardown" skill
    Then its instructions use the "$ARGUMENTS" placeholder
    And its instructions contain no "{{ARGUMENT}}" template
