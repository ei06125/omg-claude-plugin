Feature: omg-delegate
  As the owner of the omg plugin, or an agent acting for them
  I want to call /omg:delegate with the directories a task needs, the network it may reach, a backend, a model and a task
  So that a local model works inside an enforced sandbox boundary while I carry on, and I find its work where I asked for it

  Background:
    Given a fake sbx program that records every call
    And a fake "ollama" backend serving "qwen3.8:27b-mlx"
    And a synthetic workspace directory

  Scenario: The server exposes the delegate tool with its arguments
    Given the MCP server registered in ".mcp.json"
    When I discover the tools on that server
    Then the tool "delegate" is listed
    And its input schema names "task", "volumes", "network", "backend", "model", "commands", "timeout_seconds", "name" and "keep"
    And its input schema restricts "backend", "model" and the volume "mode" to enums

  Scenario: The delegate skill can be invoked by the model and by the human
    Given the "delegate" skill
    Then the model can invoke it on its own
    And its instructions tell the caller to pass the arguments to the "delegate" tool unchanged
    And its instructions tell the caller to ask for a missing required argument and never to invent one
    And its instructions tell the caller to choose the smallest set of directories and to use "ro" unless the task must write

  Scenario Outline: An unsupported argument is refused before any sandbox exists
    When I delegate with <argument>
    Then the result status is "refused" with reason "invalid_argument"
    And the refusal lists the supported values
    And no sandbox was created

    Examples:
      | argument                                        |
      | backend "vllm" and model "qwen3.8:27b-mlx"      |
      | backend "ollama" and model "llama-99"           |
      | backend "llama-server" and model "gpt-oss:120b" |
      | timeout_seconds "999999"                        |

  Scenario Outline: A forbidden volume is refused before any sandbox exists
    When I delegate with a volume that is <kind>
    Then the result status is "refused" with reason "forbidden_volume"
    And no sandbox was created

    Examples:
      | kind                                                    |
      | a relative path                                         |
      | a path that does not exist                              |
      | the home directory                                      |
      | the parent of the home directory                        |
      | the credentials directory                               |
      | the container runtime socket                            |
      | a symlink that points to the credentials directory      |
      | a clone of a directory that is not a git repository     |
      | a clone that is not the first volume                    |

  Scenario Outline: A network policy that widens the boundary is refused
    When I delegate with the network policy "allow" "<host>"
    Then the result status is "refused" with reason "forbidden_network"
    And no sandbox was created

    Examples:
      | host                      |
      | **                        |
      | api.openai.com:443        |
      | *.anthropic.com:443       |
      | localhost:22              |
      | host.docker.internal:5432 |

  Scenario: An allow policy for an ordinary host is applied
    When I delegate with the network policy "allow" "pypi.org:443"
    Then the rules applied to the sandbox allow "pypi.org:443"

  Scenario: A deny policy is always accepted
    When I delegate with the network policy "deny" "example.com:443"
    Then the rules applied to the sandbox deny "example.com:443"

  Scenario: A backend that is not running is refused with a hint
    Given the "exo" backend is not running
    When I delegate with backend "exo" and model "gpt-oss:120b"
    Then the result status is "refused" with reason "backend_unreachable"
    And the hint says to start "exo"
    And the hint lists "ollama" "qwen3.8:27b-mlx" as currently served
    And no sandbox was created

  Scenario: A model the backend does not serve is refused without substituting another
    Given the "ollama" backend serves only "gemma4:12b"
    When I delegate with the default arguments
    Then the result status is "refused" with reason "model_unavailable"
    And the hint lists "ollama" "gemma4:12b" as currently served
    And no sandbox was created
    And no agent was started

  Scenario: The sandbox is created from the pinned image with the configured limits
    Given the guardrail configuration pins the image "sandbox-image@sha256:0123abcd" and limits sandboxes to 2 CPUs and 2048 MiB
    When I delegate with the default arguments
    Then sbx was asked to create a sandbox from the image "sandbox-image@sha256:0123abcd"
    And shared skills are off for the sandbox
    And the sandbox has 2 CPUs and 2048 MiB of memory

  Scenario: Volumes are mounted with their modes and the first is the workspace
    Given a synthetic documentation directory
    When I delegate with the workspace in mode "rw" and the documentation in mode "ro"
    Then the first mount of the sandbox is the workspace, writable
    And the documentation is mounted read-only

  Scenario: A clone volume creates the sandbox with a clone
    Given a synthetic git repository
    When I delegate with the repository as a "clone" volume
    Then sbx was asked to create the sandbox as a clone of the repository
    And the start response names the sandbox remote for the results

  Scenario: With no network policy only the backend endpoint is reachable
    Given the agent kit allows "api.openai.com:443" and "registry.npmjs.org:443" by default
    When I delegate with the default arguments
    Then the rules applied to the sandbox allow "host.docker.internal:11434"
    And the rules applied to the sandbox deny "api.openai.com:443" and "registry.npmjs.org:443"
    And the rules applied to the sandbox allow nothing else

  Scenario: A kit default host that the caller allowed is not masked
    Given the agent kit allows "registry.npmjs.org:443" by default
    When I delegate with the network policy "allow" "registry.npmjs.org:443"
    Then the rules applied to the sandbox allow "registry.npmjs.org:443"
    And the rules applied to the sandbox do not deny "registry.npmjs.org:443"

  Scenario Outline: A boundary that does not hold stops the run before the model starts
    Given the sbx program <fault>
    When I delegate with the network policy "allow" "pypi.org:443"
    Then the result status is "refused" with reason "boundary_check_failed"
    And the sandbox was removed
    And no agent was started

    Examples:
      | fault                                           |
      | reports the global default as allow-all         |
      | allows an unlisted host                         |
      | denies the backend endpoint                     |
      | gives a requested allow rule the wrong decision |

  Scenario: The boundary is verified before the model starts
    When I delegate with the default arguments
    Then the boundary checks were made before the agent was started
    And the checks covered an unlisted host and the backend endpoint

  Scenario Outline: The agent is started with the endpoint and model of the chosen backend
    Given a fake "<backend>" backend serving "<model>"
    When I delegate with backend "<backend>" and model "<model>"
    Then the agent was started with the model "<model>" and the endpoint "<endpoint>"

    Examples:
      | backend      | model           | endpoint                   |
      | ollama       | qwen3.8:27b-mlx | host.docker.internal:11434 |
      | llama-server | gpt-oss:20b     | host.docker.internal:8080  |
      | exo          | gpt-oss:120b    | host.docker.internal:52415 |

  Scenario: The agent may write only inside read-write volumes
    Given a synthetic documentation directory
    When I delegate with the workspace in mode "rw" and the documentation in mode "ro"
    Then the agent may edit files inside the workspace
    And the agent may not edit files anywhere else

  Scenario: The agent may not run shell commands unless the caller listed them
    When I delegate with the default arguments
    Then the agent may run no shell command
    And the agent may not fetch web pages

  Scenario: The agent may run only the shell commands the caller listed
    When I delegate with commands "pytest -q"
    Then the agent may run the shell command "pytest -q"
    And the agent may not run any other shell command

  Scenario: The call returns while the agent is still running
    Given the agent keeps running until released
    When I delegate with the default arguments
    Then the result status is "started"
    And the agent is still running

  Scenario: The agent keeps running after the call has returned
    Given the agent keeps running until released
    When I delegate with the default arguments
    And I release the agent
    And the run ends
    Then the completion record has the status "completed"

  Scenario: The start response reports the run
    When I delegate with the default arguments
    Then the result status is "started"
    And the start response names the run id, the sandbox, the backend "ollama" and the model "qwen3.8:27b-mlx"
    And the start response lists the volumes and the network rules that were applied
    And the start response gives the run directory
    And the run directory holds "request.json" and "applied.json"

  Scenario: The request record holds the task only as a hash
    When I delegate with task "TASK-MARKER-4409"
    Then "request.json" in the run directory does not contain "TASK-MARKER-4409"
    And "request.json" in the run directory holds the SHA-256 of "TASK-MARKER-4409"

  Scenario: A finished run is recorded as completed
    Given the agent prints "done" and exits with code 0
    When I delegate with the default arguments
    And the run ends
    Then the completion record has the status "completed" and the exit code 0

  Scenario: A failing agent is recorded as failed with its exit code
    Given the agent prints "partial work" and exits with code 3
    When I delegate with the default arguments
    And the run ends
    Then the completion record has the status "failed" and the exit code 3

  Scenario: The tool does not judge the work
    Given the agent prints "TASK FAILED: nothing was done" and exits with code 0
    When I delegate with the default arguments
    And the run ends
    Then the completion record has the status "completed" and the exit code 0

  Scenario: The completion record lists the files changed in read-write volumes
    Given a synthetic documentation directory
    And the agent creates the file "notes.md" in the workspace and the file "extra.md" in the documentation, then exits with code 0
    When I delegate with the workspace in mode "rw" and the documentation in mode "ro"
    And the run ends
    Then the completion record lists "notes.md" as changed
    And the completion record does not list "extra.md"

  Scenario: The completion record names the branch of a clone
    Given a synthetic git repository
    And the agent commits to its clone and exits with code 0
    When I delegate with the repository as a "clone" volume
    And the run ends
    Then the completion record names the branch of the clone

  Scenario: What the agent printed is kept in the run directory
    Given the agent prints "OUTPUT-MARKER-7731" and exits with code 0
    When I delegate with the default arguments
    And the run ends
    Then "agent.log" in the run directory contains "OUTPUT-MARKER-7731"

  Scenario: A run that exceeds the timeout is stopped
    Given the agent prints "partial" and then keeps running
    When I delegate with timeout_seconds "1"
    And the run ends
    Then the completion record has the status "timeout"
    And the agent process was stopped

  Scenario Outline: The sandbox is removed when the run ends unless kept
    Given the agent <outcome>
    When I delegate with the default arguments
    And the run ends
    Then the sandbox was removed

    Examples:
      | outcome                        |
      | finishes normally              |
      | exits with code 3              |
      | keeps running past the timeout |

  Scenario: A kept sandbox is not removed
    When I delegate with keep "true"
    And the run ends
    Then the sandbox was not removed

  Scenario: A sandbox name that already exists is refused, never reused
    Given a sandbox named "taken" already exists
    When I delegate with name "taken"
    Then the result status is "refused" with reason "sandbox_exists"
    And the sandbox "taken" was neither reused nor removed

  Scenario: Each call appends one audit line outside the mounted volumes
    When I delegate with the default arguments
    Then one audit line was appended
    And the audit line holds the run id, the time, the backend, the model, the volumes, the network decisions and the outcome
    And the audit file is outside every mounted volume

  Scenario: A refused call is audited too
    When I delegate with backend "vllm" and model "qwen3.8:27b-mlx"
    Then one audit line was appended
    And the audit line holds the outcome "refused"

  Scenario: The task and the agent output are not in the audit line
    Given the agent prints "OUTPUT-MARKER-7731" and exits with code 0
    When I delegate with task "TASK-MARKER-4409"
    And the run ends
    Then the audit line does not contain "TASK-MARKER-4409"
    And the audit line does not contain "OUTPUT-MARKER-7731"

  Scenario: No secret value reaches the start response, the logs, the run files or the audit
    Given the host environment sets "OMG_CANARY_TOKEN" to "canary-value-5519"
    When I delegate with the default arguments
    And the run ends
    Then the start response does not contain "canary-value-5519"
    And the run files do not contain "canary-value-5519"
    And the tool log and the audit line do not contain "canary-value-5519"
