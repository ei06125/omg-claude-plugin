"""Stage: prove the boundary holds before the model starts, by asking sbx what it would allow."""

from .config import Config
from .models import Rules
from .sbx import Sbx


def verify(sbx: Sbx, name: str, config: Config, rules: Rules) -> str | None:
    """Return the first way the boundary does not hold, or None when every check passes.

    An unlisted host must be denied. That also catches a global default that allows everything, which sbx cannot
    narrow with a per-sandbox rule. Every literal rule must have the decision it was given.
    """
    if sbx.allowed(name, config.canary_host):
        return f"an unlisted host ({config.canary_host}) is reachable, so the default network policy is not deny-all"
    for host in rules.allow:
        if "*" not in host and not sbx.allowed(name, host):
            return f"{host} was allowed but the sandbox denies it"
    for host in rules.deny:
        if "*" not in host and sbx.allowed(name, host):
            return f"{host} was denied but the sandbox allows it"
    return None
