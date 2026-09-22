"""Stage: render the agent configuration. It is the second layer; the sandbox mounts are the boundary."""

from .models import Volume


def agent_config(
    backend: str,
    model_id: str,
    endpoint: str,
    volumes: list[Volume],
    commands: list[str],
) -> dict:
    """The opencode configuration: endpoint, model and permissions.

    In a sandbox without a git root opencode matches paths relative to `/`, so each pattern is written both with and
    without the leading slash. The last matching rule wins.
    """
    clone = any(v.mode == "clone" for v in volumes)
    edit = {"*": "allow" if clone else "deny"}
    external = {"*": "deny"}
    for volume in volumes:
        root = volume.host_path.rstrip("/")
        rooted = root.lstrip("/")
        if volume.mode == "rw":
            edit[f"{root}/*"] = "allow"
            edit[f"{rooted}/*"] = "allow"
        elif volume.mode == "ro" and clone:
            edit[f"{root}/*"] = "deny"
            edit[f"{rooted}/*"] = "deny"
        external[f"{root}/*"] = "allow"
    return {
        "model": f"{backend}/{model_id}",
        "provider": {
            backend: {
                "npm": "@ai-sdk/openai-compatible",
                "name": backend,
                "options": {"baseURL": f"http://{endpoint}/v1"},
                "models": {model_id: {"name": model_id}},
            }
        },
        "permission": {
            "edit": edit,
            "bash": {"*": "deny", **dict.fromkeys(commands, "allow")},
            "webfetch": "deny",
            "external_directory": external,
        },
    }
