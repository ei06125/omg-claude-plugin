---
name: delegate
description: Delegates a task to a local model (Ollama, llama-server or exo) inside an isolated Docker sbx sandbox, with the directories and network the task needs. Use when asked to run work on a local model, or invoke /omg:delegate.
argument-hint: "task, volumes, network, backend, model"
---

Call the `delegate` MCP tool of the omg plugin and pass the arguments to it unchanged. Do not do the task yourself.

Arguments:

- `task`: the prompt for the local model. Required.
- `volumes`: the directories the task needs. Required. Each is `{host_path, mode}` with an absolute path and the mode `ro`, `rw` or `clone`. The first volume is the workspace. `clone` is one git repository whose commits come back on the sandbox remote.
- `backend`: `ollama`, `llama-server` or `exo`. Required.
- `model`: `qwen3.8:27b-mlx`, `gemma4:12b`, `gpt-oss:20b` or `gpt-oss:120b`. Required. `gpt-oss:120b` needs `exo`.
- `network`: allow or deny rules, each `{action, host}`. Optional. By default only the model backend is reachable, so leave it out unless the task needs a host.
- `commands`, `timeout_seconds`, `name`, `keep`: optional.

Rules:

- Ask the user for any missing required argument. Never invent a value.
- Choose the smallest set of directories the task needs. Use mode "ro" unless the task must write, and mode "rw" only for the directories that must change.
- Do not widen the network, and do not add credentials or secrets to the task.

The call returns at once. Report the `run_id`, the `sandbox`, the `run_dir` and where the result will appear (the `results` field). Do not wait for the run, poll it or judge its output. When the agent ends, `completion.json` in the run directory says how it ended.

If the call is refused, report the `reason` and the `hint`. For `backend_unreachable` or `model_unavailable`, you may retry with a model from `hint.served`, or ask the user whether they or you should start the backend. Never start a backend without asking.
