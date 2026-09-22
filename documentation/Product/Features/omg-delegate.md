# omg-delegate

- **Status:** In development, awaiting owner acceptance
- **Executable spec:** `tests/acceptance/features/omg-delegate.feature` (fake sbx, runs in CI) and
  `tests/acceptance/features/omg-delegate-sbx.feature` (real sbx, tagged `@sbx`, local only)
- **Implementation:** `sources/omg_delegate/`, `.mcp.json`, `.claude/skills/delegate/SKILL.md` and
  `configs/delegate/guardrails.json`
- **Issue:** <https://github.com/ei06125/omg-claude-plugin/issues/31>

## Summary

`/omg:delegate` is the entrypoint of a delegation harness. A human or an agent calls it with volumes, network
policies, a backend, a model and a task. The harness, written as plain Python with no orchestration framework,
validates the request, writes the configuration files, creates an isolated Docker sbx sandbox, proves the
boundary holds, starts the model detached and returns at once: fire and forget.

The call does not return the result. The result appears where the work lands: as file changes in a mounted
worktree, as commits on a branch that an sbx clone hands back, or on GitHub if the agent pushed. Validating it is
the caller's job.

## Problem

Delegating to a local model by hand takes a dozen steps: create the sandbox, mount folders, write network rules,
point the agent at the backend, write its permission config, run, watch, clean up. Every step can widen the
boundary by mistake. The traps found so far are not obvious:

- In sbx, a deny rule beats an allow rule, so "deny all, then allow the model" cannot be expressed per sandbox.
- The built-in agent kit adds about 30 allowed hosts to every sandbox, including model providers that can carry
  stored OAuth credentials.
- A folder is only read-only if it was mounted read-only. An agent-level permission is a second layer, not the
  boundary.
- Runs are slow: a review by a 27B model took about 20 minutes, too long for a call that blocks its caller.

## User story

As the owner of the omg plugin, or an agent acting for them, I want to call `/omg:delegate` with the directories
a task needs, the network it may reach, a backend, a model and a task, so that a local model works inside an
enforced boundary while I carry on, and I find its work where I asked for it.

## How it works

The tool is the entrypoint. Each stage is a plain Python function that writes files or runs `sbx`:

1. Validate the arguments against the guardrails and refuse early.
2. Check that the backend is running and serves the model.
3. Write the files: the agent configuration (endpoint, model, permissions), the network rule set and the run
   record.
4. Create the sandbox from the pinned image, with the volumes, or as a clone.
5. Apply the per-sandbox network rules and mask the agent kit's default allowed hosts.
6. Verify the boundary. On any mismatch remove the sandbox and refuse.
7. Start the agent detached under a supervisor and return the start response.
8. The supervisor enforces the timeout, writes the completion record and removes the sandbox unless `keep`.

## Arguments

| Name | Type | Required | Meaning |
|---|---|---|---|
| `task` | string | yes | The prompt sent to the model |
| `volumes` | list of Volume | yes | `{host_path, mode}`; `host_path` is absolute; `mode` is `ro`, `rw` or `clone`; the first volume is the workspace |
| `network` | list of Policy | no | `{action, host}`; `action` is `allow` or `deny`; `host` is `name[:port]` or `*.domain[:port]`; default: nothing allowed |
| `backend` | enum | yes | `ollama`, `llama-server` or `exo` (`exo` is experimental) |
| `model` | enum | yes | `qwen3.8:27b-mlx`, `gemma4:12b`, `gpt-oss:20b`, `gpt-oss:120b` |
| `commands` | list of string | no | Shell command patterns the model may run; default: none |
| `timeout_seconds` | integer | no | Default and maximum come from the guardrail configuration |
| `name` | string | no | Sandbox name; default: generated |
| `keep` | boolean | no | Keep the sandbox after the run; default `false` |

The model endpoint of the chosen backend is always allowed by the tool and needs no policy from the caller.

The caller chooses the smallest set of directories the task needs and uses `ro` unless the task must write. The
tool has no fixed list of roots; it refuses only what is forbidden or too broad (see Guardrails).

Mode `clone` is for a git repository: the agent works on a private clone inside the sandbox, the host directory
is not writable, and the agent's commits come back through the sbx git remote `sandbox-<name>`.

## Start response

`status` (`started` or `refused`), `run_id`, `sandbox`, `backend`, `model`, `run_dir`, the volumes and network
rules that were actually applied, and `results`: where the work will appear (the `rw` paths, and for a clone the
remote `sandbox-<name>`; the branch is only known once the agent has committed, so it is in the completion
record).

A refusal carries `reason` and a `hint`. Reasons: `invalid_argument`, `forbidden_volume`, `forbidden_network`,
`backend_unreachable`, `model_unavailable`, `boundary_check_failed`, `sandbox_exists` or `sandbox_failed` (sbx could
not create or configure the sandbox; whatever was created is removed).

## Run record

The tool keeps a directory per run under the plugin's state directory, outside every mounted volume:

- `request.json`: the arguments, with the task replaced by its hash.
- `applied.json`: the volumes and network decisions in force.
- `agent.log`: what the agent printed.
- `completion.json`, written by the supervisor when the agent ends: `status` (`completed`, `failed` or
  `timeout`), `exit_code`, `duration_seconds`, and the files changed in `rw` volumes or the branch of a clone.

There is also one append-only audit line per call, kept apart from the run directories.

## Behaviour

| # | Acceptance criterion | Checked by | Runs in CI |
|---|---|---|---|
| 1 | The server exposes a tool `delegate` whose input schema names `task`, `volumes`, `network`, `backend`, `model`, `commands`, `timeout_seconds`, `name` and `keep`, with `backend`, `model` and the volume `mode` as enums | Structural scenario | Yes |
| 2 | `/omg:delegate` exists as a skill that the model can invoke as well as the human, and tells the caller to pass the arguments to the `delegate` tool unchanged, to ask for a missing required one, to invent none, and to choose the smallest set of directories with `ro` unless the task must write | Structural scenario | Yes |
| 3 | An unknown backend, an unknown model, a backend and model pair the registry does not list, or a `timeout_seconds` above the ceiling is refused with reason `invalid_argument` and the supported values, and no sandbox is created | Behavioural scenario | Yes |
| 4 | A volume is refused with reason `forbidden_volume` when its path is relative, does not exist, is or resolves (also through a symlink) to a forbidden or too broad path, or when mode `clone` is used on a directory that is not a git repository or on any volume but the first; no sandbox is created | Behavioural scenario | Yes |
| 5 | A network policy is refused with reason `forbidden_network` when it allows `**`, allows a host that injects stored credentials, or allows a port on the local machine other than the backend's; a `deny` policy is always accepted | Behavioural scenario | Yes |
| 6 | When the backend is not running or does not serve the model, the call is refused with `backend_unreachable` or `model_unavailable` and a hint that says what to start and lists the other supported pairs that are currently served; the tool never starts a backend and never substitutes another | Behavioural scenario | Yes |
| 7 | The sandbox is created from the pinned image with shared skills off and the configured resource limits; the first volume is the workspace, every `ro` volume is mounted read-only and every `rw` volume is writable | Behavioural scenario | Yes |
| 8 | A `clone` volume creates the sandbox with `--clone`, and the start response names the remote `sandbox-<name>` where the commits will appear | Behavioural scenario | Yes |
| 9 | With no network policy only the backend endpoint is reachable; the agent kit's default allowed hosts are masked with per-sandbox denies unless the caller allowed them and the guardrails permit it | Behavioural scenario | Yes |
| 10 | Before the model starts, the tool checks the boundary: an unlisted host is denied, the backend endpoint is allowed, and every requested rule has the expected decision. Any mismatch, including a global default that allows everything, ends in `boundary_check_failed`, the sandbox is removed and the model is never started | Behavioural scenario | Yes |
| 11 | The agent is started with the backend endpoint and the model; it may write only inside `rw` volumes, may run only the caller's `commands`, and may not fetch web pages | Behavioural scenario | Yes |
| 12 | The call returns `started` while the agent is still running, and the agent keeps running after the call has returned | Behavioural scenario | Yes |
| 13 | The start response carries every field listed under Start response, and the run directory holds `request.json` and `applied.json` | Behavioural scenario | Yes |
| 14 | When the agent ends, `completion.json` records `completed` with exit code 0, or `failed` with the exit code, whatever the agent printed; it lists the changed files of `rw` volumes or the branch of a clone; the tool does not judge the work | Behavioural scenario | Yes |
| 15 | A run that exceeds `timeout_seconds` is stopped by the supervisor and recorded as `timeout` | Behavioural scenario | Yes |
| 16 | The sandbox is removed when the run ends, whether it completed, failed or timed out, unless `keep` is true; a name that already exists is refused with reason `sandbox_exists`, never reused | Behavioural scenario | Yes |
| 17 | Each call, refused ones included, appends one audit line (run id, time, backend, model, volumes, network decisions, outcome); the task text and the agent output are not in it | Behavioural scenario | Yes |
| 18 | No start response, log line, run file or audit line contains the value of an environment variable or a secret | Behavioural scenario | Yes |
| 19 | Against a real sbx and a real backend: a write to a read-only volume fails, a write to a read-write volume succeeds, an unlisted host is blocked, the backend answers, and a clone hands its commits back through the sandbox remote without touching the host working tree | Real sandbox scenario | No |

Criteria 1 to 18 run against a fake `sbx` program and a fake OpenAI-compatible endpoint, so CI needs neither
Docker, sbx nor a model. Criterion 19 needs the real thing, so it is tagged `@sbx` and runs locally only.

## Guardrails

The caller is untrusted: another model can call this tool. The limits live in a versioned configuration that no
argument can change, with paths written as `$HOME` placeholders:

- Forbidden paths: the home directory, its ancestors and the filesystem root; credential directories such as
  `.ssh`, `.aws`, `.gnupg` and `.docker`; the container runtime socket.
- Hosts that must never be allowed: model providers and code hosts whose stored credentials the sbx proxy would
  inject.
- The registry of supported backend and model pairs, and each backend's endpoint.
- The pinned image digest, resource limits and the timeout ceiling.

## Out of scope

- Validating or scoring the result. The caller does that from where the work landed.
- Getting the result to GitHub. It needs a sandbox-scoped GitHub secret and allowed hosts, so it is a later
  feature. The first version passes no secrets into the sandbox.
- Starting backends, pulling models and creating `exo` instances. The tool reports what to start.
- Status or result tools, and any polling.
- Agents other than opencode, and cloud sandboxes.
- Changing global sbx policy or global secrets. The tool only adds sandbox-scoped rules.

## Constraints and notes

- The stages are plain Python functions, and the tool writes the files and creates the sandboxes itself. No
  orchestration framework.
- The supervisor is a detached host process, so it outlives the call that started it.
- The tool never changes the global network policy. It verifies that the global default denies traffic and
  refuses to run otherwise, because a per-sandbox allowlist cannot be expressed when deny beats allow.
- Refusals happen before any sandbox exists, and a failed boundary check removes the sandbox it created.
- `exo` must already be running with the model served. When it is not, the refusal tells the caller to try a
  model that does not need it, or to ask the end user whether the user or the caller should start it.
- The sbx proxy evaluates `host.docker.internal:<port>` as `localhost:<port>`, so the tool allows the backend
  endpoint under both names and refuses every other local port.
- `sbx policy check` exits 1 for a denied target and still prints its JSON decision. The tool reads the decision, not
  the exit code.
- The registry maps each model to the identifier its backend serves, so `llama-server` aliases and Ollama names
  can differ.
- A model is not deterministic, so the real-sandbox check (criterion 19) replaces the agent command with a probe
  script through the guardrail configuration. Only the server's configuration can do that, never a caller.
- The agent's output goes to `agent.log` in the run directory, readable by the owner only, and never to the audit
  line.
- At the time of writing Ollama serves `qwen3.8:27b-mlx` and `gemma4:12b` but not the `gpt-oss` models.
  `llama-server` is installed and a GGUF of `gpt-oss-20b` is in the Hugging Face cache. `exo` is installed
  (`uv run exo`, API at `localhost:52415`) with the `gpt-oss-120b` MXFP4 weights downloaded. None of the three
  backends is guaranteed to be running.

## Direction

- **Tickets.** The `task` is a plain string today. It will become a Jira ticket or a GitHub issue, and the result
  will then come back to that ticket as status updates, comments or a pull request. This version does not talk to
  any tracker. The run record is structured (`request.json`, `applied.json`, `completion.json`) so a later
  reporter can read it and post it. Until then the caller reads `completion.json` in the run directory.
- **`clone` on a real sandbox.** The `sandbox-<name>` remote is documented by sbx but untested here. Criterion 19
  covers it, and it runs locally once the harness exists.

## How to verify

```bash
uv run pytest                    # criteria 1-18, fake sbx and fake endpoint, same as CI
uv run pytest -m sbx             # criterion 19, needs sbx, Docker Desktop signed in, a running backend
```

## Acceptance

Done by the owner only: review the feature and check the CI result. The author does not tick these.

- [ ] CI is green
- [ ] Feature review passed
