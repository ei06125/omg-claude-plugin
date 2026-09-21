"""Stage: check that the chosen backend is running and serves the model. The tool never starts a backend."""

import json
import urllib.error
import urllib.request

from .config import Config
from .models import Refusal

START_HINTS = {
    "ollama": "Start Ollama (`ollama serve`) and pull the model (`ollama pull <model>`).",
    "llama-server": "Start llama-server with the model, for example `llama-server -hf <repo> --alias <id>`.",
    "exo": (
        "Start exo (`uv run exo` in the exo checkout) and create an instance of the model. "
        "Or choose a model that does not need exo, or ask the end user whether they or you should start it."
    ),
}


def served_ids(probe_url: str, timeout: float = 2.0) -> list[str] | None:
    """The model ids an OpenAI-compatible endpoint lists, or None when nothing answers."""
    try:
        with urllib.request.urlopen(probe_url, timeout=timeout) as reply:
            data = json.load(reply)
    except (OSError, ValueError, urllib.error.URLError):
        return None
    return [
        entry["id"]
        for entry in data.get("data", [])
        if isinstance(entry, dict) and "id" in entry
    ]


def served_pairs(config: Config) -> list[dict]:
    """The supported backend and model pairs that are being served right now."""
    pairs = []
    for backend, spec in config.backends.items():
        ids = served_ids(spec.probe_url)
        if ids is None:
            continue
        pairs.extend(
            {"backend": backend, "model": model}
            for model, served in config.models.items()
            if served.get(backend) in ids
        )
    return pairs


def require(config: Config, backend: str, model: str) -> None:
    """Raise a refusal with a hint unless `backend` is running and serves `model`."""
    ids = served_ids(config.backends[backend].probe_url)
    if ids is None:
        raise Refusal(
            "backend_unreachable",
            f"{backend} is not running",
            hint=_hint(
                config, backend, f"{backend} is not running. {START_HINTS[backend]}"
            ),
        )
    if config.served_id(backend, model) not in ids:
        raise Refusal(
            "model_unavailable",
            f"{backend} does not serve {model}",
            hint=_hint(
                config,
                backend,
                f"{backend} is running but does not serve {model}. {START_HINTS[backend]}",
            ),
        )


def _hint(config: Config, backend: str, text: str) -> dict:
    return {"start": backend, "text": text, "served": served_pairs(config)}
