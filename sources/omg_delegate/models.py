"""Plain data types shared by the harness stages."""

from dataclasses import dataclass

BACKENDS = ("ollama", "llama-server", "exo")
MODELS = ("qwen3.8:27b-mlx", "gemma4:12b", "gpt-oss:20b", "gpt-oss:120b")
MODES = ("ro", "rw", "clone")
ACTIONS = ("allow", "deny")


@dataclass(frozen=True)
class Volume:
    host_path: str
    mode: str


@dataclass(frozen=True)
class Policy:
    action: str
    host: str


@dataclass(frozen=True)
class Rules:
    allow: list[str]
    deny: list[str]


@dataclass(frozen=True)
class Request:
    task: str
    volumes: list[Volume]
    network: list[Policy]
    backend: str
    model: str
    commands: list[str]
    timeout_seconds: int
    name: str | None
    keep: bool


class Refusal(Exception):
    """A call that must not start a run. `extra` carries the hint, the supported values or the sandbox name."""

    def __init__(self, reason: str, message: str, **extra):
        super().__init__(message)
        self.reason = reason
        self.message = message
        self.extra = extra

    def as_response(self, run_id: str) -> dict:
        return {
            "status": "refused",
            "run_id": run_id,
            "reason": self.reason,
            "message": self.message,
            **self.extra,
        }


@dataclass
class Run:
    """What the supervisor needs, written to run.json. It never holds the task text."""

    sbx: str
    sandbox: str
    agent_argv: list[str]
    agent_env: dict[str, str]
    workdir: str | None
    timeout_seconds: int
    keep: bool
    rw_paths: list[str]
    clone: dict | None
    state_dir: str
