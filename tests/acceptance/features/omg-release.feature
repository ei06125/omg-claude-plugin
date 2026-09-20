Feature: omg-release
  As the owner of the omg plugin
  I want releases proposed and tagged automatically
  So that I cut a release by reviewing and merging a release pull request

  Scenario: Accepting a feature proposes a minor release
    Given the plugin is released as "0.1.0"
    And a feature spec was accepted since that release
    When the release job runs
    Then a release "0.2.0" is proposed for review

  Scenario: Fixing shipped content proposes a patch release
    Given the plugin is released as "0.1.0"
    And shipped content was fixed since that release
    When the release job runs
    Then a release "0.1.1" is proposed for review

  Scenario: Changes users never receive do not propose a release
    Given the plugin is released as "0.1.0"
    And only documentation, tests and CI changed since that release
    When the release job runs
    Then no release is proposed

  Scenario: A breaking change proposes a minor release while below 1.0.0
    Given the plugin is released as "0.3.0"
    And a feature spec was marked as breaking since that release
    When the release job runs
    Then a release "0.4.0" is proposed for review

  Scenario: The same release is not proposed twice
    Given the plugin is released as "0.1.0"
    And a feature spec was accepted since that release
    And the release job already proposed "0.2.0"
    When the release job runs
    Then no further release is proposed

  Scenario: A new proposal replaces an outdated one
    Given the plugin is released as "0.1.0"
    And shipped content was fixed since that release
    And the release job already proposed "0.1.1"
    And a feature spec was accepted since that release
    When the release job runs
    Then a release "0.2.0" is proposed for review
    And the proposal for "0.1.1" is withdrawn

  Scenario: A proposal that lost its pull request is completed
    Given the plugin is released as "0.1.0"
    And a feature spec was accepted since that release
    And the release job proposed "0.2.0" while pull requests were not allowed
    When the release job runs
    Then a release "0.2.0" is proposed for review
    And the existing release branch was reused

  Scenario: Merging a release tags it and proposes nothing else
    Given the plugin is released as "0.1.0"
    And the release "0.2.0" was merged into main
    When the release job runs
    Then "v0.2.0" is tagged on main with an annotated tag
    And the workflow is told about the tag "v0.2.0"
    And no release is proposed

  Scenario: A missing baseline release is reported without failing the workflow
    Given the plugin has no baseline release
    When the release job runs
    Then the release job reports that it is not configured

  Scenario: A missing release token is reported without failing the workflow
    Given the plugin is released as "0.1.0"
    And a feature spec was accepted since that release
    And no release token is configured
    When the release job runs
    Then the release job reports that it is not configured
    And nothing was pushed

  Scenario: A repository that blocks workflow pull requests is reported without failing the workflow
    Given the plugin is released as "0.1.0"
    And a feature spec was accepted since that release
    And workflows are not allowed to create pull requests
    When the release job runs
    Then the release job reports that it is not configured
    And it explains which repository setting to change

  Scenario: A dry run shows the plan and changes nothing
    Given the plugin is released as "0.1.0"
    And a feature spec was accepted since that release
    When the release job runs as a dry run
    Then the plan mentions release "0.2.0"
    And nothing was pushed

  Scenario: The release token never appears in the output
    Given the plugin is released as "0.1.0"
    And a feature spec was accepted since that release
    When the release job runs
    Then the release token does not appear in the output

  Scenario Outline: A tag workflow accepts only a genuine release tag
    Given <kind> "<tag>" on main for plugin version "<version>"
    When the tag workflow verifies "<tag>"
    Then the tag is <verdict>

    Examples:
      | kind              | tag           | version | verdict  |
      | an annotated tag  | v0.2.0        | 0.2.0   | accepted |
      | a lightweight tag | v0.2.0        | 0.2.0   | rejected |
      | an annotated tag  | v0.2.0        | 0.3.0   | rejected |
      | an annotated tag  | release-final | 0.2.0   | rejected |
