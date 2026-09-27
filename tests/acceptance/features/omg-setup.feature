Feature: omg-setup
  As the owner of the omg plugin
  I want to run /omg:setup at the start of a session
  So that access is verified and the workspace's diary and profile are read before any work begins

  Scenario: The plugin ships the setup skill
    Given the omg plugin manifest
    Then the "setup" skill exists in that directory

  Scenario: The skill runs both on explicit invocation and when the model chooses it
    Given the "setup" skill
    Then the model can invoke it on its own
    And its front matter takes the "session-name" argument

  Scenario: The skill checks the personal access tokens
    Given the "setup" skill
    Then its instructions require checking that the required personal access tokens exist in environment variables

  Scenario Outline: The skill checks access to each platform
    Given the "setup" skill
    Then its instructions require checking access to "<platform>" via "<tool>"

    Examples:
      | platform  | tool        |
      | GitHub    | GH CLI tool |
      | Atlassian | MCP tool    |
      | Slack     | MCP tool    |

  Scenario: The skill runs the project-local agent setup when the agent names match
    Given the "setup" skill
    Then its instructions require determining the active "AGENTNAME"
    And its instructions require comparing it case-insensitively with the agent name declared in the project's CLAUDE.md
    And its instructions require running ".claude/skills/setup-$AGENTNAME/SKILL.md" once when they match
    And its instructions require skipping it when the names do not match or the skill does not exist

  Scenario: The skill reads the workspace's session history and profile
    Given the "setup" skill
    Then its instructions require checking ".claude/" for session directories
    And its instructions require reading "DIARY.md" for a recap
    And its instructions require reading "PEDRO.md" for user profiling

  Scenario: The skill opens a new session directory
    Given the "setup" skill
    Then its instructions require creating "session-$DATETIME" when the argument is empty
    And its instructions require creating "session-$ARGUMENTS/" when an argument is given

  Scenario: The skill uses the real argument placeholder
    Given the "setup" skill
    Then its instructions use the "$ARGUMENTS" placeholder
    And its instructions contain no "{{ARGUMENT}}" template

  Scenario Outline: The skill states its global rules
    Given the "setup" skill
    Then its instructions state the rule "<rule>"

    Examples:
      | rule                                                                      |
      | Never print the PATs                                                      |
      | Prefer scripts to autonomous actions                                      |
      | Iterate on scripts and add tests if needed                                |
      | If working on a git repo, setup gitleaks and other secret detection tools |
