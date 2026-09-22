"""The guardrail configuration. It is versioned with the plugin and no argument of a call can change it."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATH = (
    Path(__file__).resolve().parents[2] / "configs" / "delegate" / "guardrails.json"
)


@dataclass(frozen=True)
class Backend:
    endpoint: str
    probe_url: str
    experimental: bool = False


@dataclass(frozen=True)
class Config:
    image: str
    cpus: int
    memory_mib: int
    timeout_default: int
    timeout_max: int
    home: Path
    forbidden_paths: tuple[Path, ...]
    forbidden_hosts: tuple[str, ...]
    canary_host: str
    backends: dict[str, Backend]
    models: dict[str, dict[str, str]]
    agent_command: tuple[str, ...] | None = None

    @classmethod
    def from_dict(cls, data: dict, home: Path) -> "Config":
        home = Path(os.path.realpath(home))
        limits = data["limits"]
        return cls(
            image=data["image"],
            cpus=limits["cpus"],
            memory_mib=limits["memory_mib"],
            timeout_default=limits["timeout_seconds"]["default"],
            timeout_max=limits["timeout_seconds"]["maximum"],
            home=home,
            forbidden_paths=tuple(_expand(p, home) for p in data["forbidden_paths"]),
            forbidden_hosts=tuple(data["forbidden_hosts"]),
            canary_host=data["canary_host"],
            backends={name: Backend(**spec) for name, spec in data["backends"].items()},
            models=data["models"],
            agent_command=tuple(data["agent_command"])
            if data.get("agent_command")
            else None,
        )

    @classmethod
    def load(cls, env: dict, home: Path) -> "Config":
        path = Path(env.get("OMG_DELEGATE_CONFIG") or DEFAULT_PATH)
        return cls.from_dict(json.loads(path.read_text()), home)

    def pairs(self) -> list[tuple[str, str]]:
        return sorted(
            (backend, model)
            for model, served in self.models.items()
            for backend in served
        )

    def endpoints(self, backend: str) -> list[str]:
        """The endpoint as the sandbox spells it and as the sbx proxy evaluates it (`host.docker.internal` is `localhost`)."""
        endpoint = self.backends[backend].endpoint
        return [endpoint, endpoint.replace("host.docker.internal", "localhost")]

    def served_id(self, backend: str, model: str) -> str:
        return self.models[model][backend]


def _expand(entry: str, home: Path) -> Path:
    return Path(os.path.realpath(entry.replace("$HOME", str(home))))
