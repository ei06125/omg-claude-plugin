"""Stage: decide which network policies are acceptable and turn them into the rules a sandbox gets."""

from .config import Config
from .models import Policy, Rules

LOCAL_NAMES = ("localhost", "127.0.0.1", "0.0.0.0", "::1", "host.docker.internal")


def host_matches(pattern: str, host: str) -> bool:
    """Match an sbx-style pattern (`name`, `name:port`, `*.domain`, `**`) against a host."""
    p_name, _, p_port = pattern.partition(":")
    h_name, _, h_port = host.partition(":")
    if p_port and h_port and p_port != h_port:
        return False
    if p_name in ("**", "*"):
        return True
    if p_name.startswith(("**.", "*.")):
        return h_name.endswith(p_name.lstrip("*"))
    return h_name == p_name


def forbidden_allow(host: str, config: Config, backend: str) -> str | None:
    """Return why an allow rule for `host` is refused, or None."""
    name = host.partition(":")[0]
    if name in ("**", "*") or name.startswith("**"):
        return "allowing every host would remove the network boundary"
    for forbidden in config.forbidden_hosts:
        representative = forbidden.replace("*", "x")
        if host_matches(forbidden, host) or host_matches(host, representative):
            return f"{host!r} covers {forbidden!r}, a host where the sandbox proxy would inject stored credentials"
    if name in LOCAL_NAMES and host not in config.endpoints(backend):
        return f"{host!r} is a port on the local machine other than the endpoint of {backend}"
    return None


def rules(
    policies: list[Policy], backend: str, kit_hosts: list[str], config: Config
) -> Rules:
    """The allow and deny rules for one sandbox.

    The backend endpoint is always allowed, spelled both ways. The agent kit's default allowed hosts are masked with denies unless the
    caller allowed them, because in sbx a deny beats an allow and the kit's list is long.
    """
    endpoints = config.endpoints(backend)
    requested = [
        p.host for p in policies if p.action == "allow" and p.host not in endpoints
    ]
    deny = [p.host for p in policies if p.action == "deny"]
    for kit_host in kit_hosts:
        if kit_host in deny or any(
            host_matches(allowed, kit_host) for allowed in requested
        ):
            continue
        deny.append(kit_host)
    return Rules(allow=[*endpoints, *requested], deny=deny)
