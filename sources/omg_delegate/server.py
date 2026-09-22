"""The MCP server. It exposes `delegate` to agents; `/omg:delegate` is the skill that calls it for humans."""

import os
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import BaseModel

from .harness import delegate as run_delegate
from .models import BACKENDS, MODELS, MODES

server = MCPServer("omg")


class VolumeArg(BaseModel):
    host_path: str
    mode: Literal[*MODES]


class PolicyArg(BaseModel):
    action: Literal["allow", "deny"]
    host: str


@server.tool(
    name="delegate",
    structured_output=True,
    annotations=ToolAnnotations(
        title="Delegate a task to a local model in an sbx sandbox",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def delegate(
    task: str,
    volumes: list[VolumeArg],
    backend: Literal[*BACKENDS],
    model: Literal[*MODELS],
    network: list[PolicyArg] | None = None,
    commands: list[str] | None = None,
    timeout_seconds: int | None = None,
    name: str | None = None,
    keep: bool = False,
) -> dict[str, Any]:
    """Run a task on a local model inside an isolated sbx sandbox, then return at once (fire and forget).

    volumes are the directories the task needs, each `ro` or `rw`, or one git repository as `clone`; the first is
    the workspace. network lists allow or deny rules; by default only the model backend is reachable. The result
    is not returned: it appears as file changes in `rw` volumes or as commits on the clone's remote, and the run
    directory named in the response holds completion.json once the agent has ended.
    """
    arguments = {
        "task": task,
        "volumes": [v.model_dump() for v in volumes],
        "backend": backend,
        "model": model,
        "keep": keep,
    }
    optional = {
        "network": [p.model_dump() for p in network] if network is not None else None,
        "commands": commands,
        "timeout_seconds": timeout_seconds,
        "name": name,
    }
    arguments.update(
        {key: value for key, value in optional.items() if value is not None}
    )
    return run_delegate(arguments, env=dict(os.environ))


if __name__ == "__main__":
    server.run()
