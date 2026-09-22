@sbx
Feature: omg-delegate on a real sandbox
  As the owner of the omg plugin
  I want the delegate boundary proven against a real sbx and a real backend
  So that I do not rely on a fake to show that the sandbox enforces it

  Scenario: Writes are confined by volume mode
    Given a real sbx and a running "ollama" backend serving "gemma4:12b"
    And a synthetic read-only volume and a synthetic read-write volume
    When I delegate a probe that writes to both volumes
    Then the write to the read-only volume failed
    And the write to the read-write volume succeeded

  Scenario: Egress is confined to the backend
    Given a real sbx and a running "ollama" backend serving "gemma4:12b"
    And a synthetic read-write volume
    When I delegate a probe that requests an unlisted host and the backend
    Then the unlisted host was blocked
    And the backend answered

  Scenario: A clone hands its commits back through the sandbox remote
    Given a real sbx and a running "ollama" backend serving "gemma4:12b"
    And a synthetic git repository
    When I delegate a probe that commits a file in the clone
    Then the repository has the sandbox remote with that commit
    And the working tree of the repository is unchanged
