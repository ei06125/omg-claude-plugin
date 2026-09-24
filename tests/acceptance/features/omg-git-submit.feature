Feature: omg-git-submit
  As the owner of the omg plugin
  I want to run /omg:git-submit
  So that finished work becomes one focused pull request without me repeating the same rules each time

  Scenario: The plugin ships the git-submit skill
    Given the omg plugin manifest
    Then the "git-submit" skill exists in that directory

  Scenario: The git-submit skill runs only when invoked explicitly
    Given the "git-submit" skill
    Then the model cannot invoke it on its own

  Scenario: Invoking the skill authorizes one commit, a push and a pull request
    Given the "git-submit" skill
    Then its instructions state that invoking it authorizes staging relevant files, one commit, a push and a pull request

  Scenario Outline: Invoking the skill does not authorize more than that
    Given the "git-submit" skill
    Then its instructions state that invoking it does not authorize "<action>"

    Examples:
      | action                      |
      | merging                     |
      | auto-merging                |
      | tagging                     |
      | releases                    |
      | force-pushing               |
      | deleting branches           |
      | applying infrastructure     |
      | including unrelated changes |

  Scenario: Only explicit task-relevant paths are staged
    Given the "git-submit" skill
    Then its instructions require staging explicit task-relevant paths
    And its instructions forbid staging with "git add --all" and "git add ."

  Scenario Outline: History is never rewritten and hooks are never bypassed
    Given the "git-submit" skill
    Then its instructions forbid "<practice>"

    Examples:
      | practice                                          |
      | amending an existing commit                       |
      | force-pushing                                     |
      | bypassing, disabling or skipping repository hooks |

  Scenario: The skill never submits directly from a protected branch
    Given the "git-submit" skill
    Then its instructions forbid submitting directly from a protected or long-lived branch
    And its instructions require creating a short-lived branch instead

  Scenario Outline: Staged content is scanned for sensitive values
    Given the "git-submit" skill
    Then its instructions require scanning staged content for "<value>"

    Examples:
      | value                         |
      | credentials                   |
      | absolute home-directory paths |
      | local usernames               |
      | hostnames                     |
      | personal email addresses      |

  Scenario: The skill stops and asks instead of guessing
    Given the "git-submit" skill
    Then its instructions require stopping and asking when relevance is ambiguous
    And its instructions require asking when the pull request base evidence conflicts

  Scenario: An existing pull request is updated, never duplicated or merged
    Given the "git-submit" skill
    Then its instructions require updating an open pull request that already exists instead of creating a duplicate
    And its instructions forbid merging it

  Scenario: No empty commit is created
    Given the "git-submit" skill
    Then its instructions forbid creating an empty commit when there are no relevant changes

  Scenario: The skill reports what it did
    Given the "git-submit" skill
    Then its instructions require reporting the branch, commit, PR URL, validation result and anything excluded
