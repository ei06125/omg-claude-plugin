"""Stage: turn the raw arguments into a Request, or refuse them with the values that are supported."""

import re

from .config import Config
from .models import ACTIONS, MODES, Policy, Refusal, Request, Volume

NAME = re.compile(r"^[a-z0-9][a-z0-9.-]{1,62}$")


def supported(config: Config) -> dict:
    return {
        "backends": sorted(config.backends),
        "models": sorted(config.models),
        "pairs": [{"backend": b, "model": m} for b, m in config.pairs()],
        "modes": list(MODES),
        "max_timeout_seconds": config.timeout_max,
    }


def parse(request: object, config: Config) -> Request:
    def bad(message: str):
        raise Refusal("invalid_argument", message, supported=supported(config))

    if not isinstance(request, dict):
        bad("the request must be an object")
    task = request.get("task")
    if not isinstance(task, str) or not task.strip():
        bad("task is required and must be a non-empty string")
    backend, model = request.get("backend"), request.get("model")
    if backend not in config.backends:
        bad(f"unknown backend {backend!r}")
    if model not in config.models:
        bad(f"unknown model {model!r}")
    if backend not in config.models[model]:
        bad(f"{backend} is not a supported backend for {model}")
    volumes = _list_of(request.get("volumes"), "volumes", bad)
    network = _list_of(request.get("network", []), "network", bad)
    commands = request.get("commands", [])
    if not isinstance(commands, list) or not all(
        isinstance(c, str) and c for c in commands
    ):
        bad("commands must be a list of non-empty strings")
    timeout = request.get("timeout_seconds", config.timeout_default)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
        bad("timeout_seconds must be a positive integer")
    if timeout > config.timeout_max:
        bad(f"timeout_seconds is above the ceiling of {config.timeout_max}")
    name = request.get("name")
    if name is not None and (not isinstance(name, str) or not NAME.match(name)):
        bad(
            "name must be lower-case letters, digits, dots and hyphens, starting with a letter or digit"
        )
    keep = request.get("keep", False)
    if not isinstance(keep, bool):
        bad("keep must be true or false")
    return Request(
        task=task,
        volumes=[_volume(v, bad) for v in volumes],
        network=[_policy(p, bad) for p in network],
        backend=backend,
        model=model,
        commands=commands,
        timeout_seconds=timeout,
        name=name,
        keep=keep,
    )


def _list_of(value, label, bad):
    if not isinstance(value, list):
        bad(f"{label} must be a list")
    return value


def _volume(raw, bad) -> Volume:
    if (
        not isinstance(raw, dict)
        or not isinstance(raw.get("host_path"), str)
        or not isinstance(raw.get("mode"), str)
    ):
        bad("each volume needs a host_path and a mode")
    return Volume(host_path=raw["host_path"], mode=raw["mode"])


def _policy(raw, bad) -> Policy:
    if (
        not isinstance(raw, dict)
        or raw.get("action") not in ACTIONS
        or not isinstance(raw.get("host"), str)
    ):
        bad("each network policy needs an action (allow or deny) and a host")
    if not raw["host"].strip():
        bad("a network policy host must not be empty")
    return Policy(action=raw["action"], host=raw["host"].strip())
