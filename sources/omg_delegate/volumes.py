"""Stage: decide whether the requested directories may be mounted, and how."""

import os
from pathlib import Path

from .config import Config
from .models import MODES, Volume


def check_volumes(volumes: list[Volume], config: Config) -> str | None:
    """Return why the volumes are refused, or None when they are acceptable."""
    if not volumes:
        return "at least one volume is required"
    for index, volume in enumerate(volumes):
        problem = _check_one(volume, index, config)
        if problem:
            return problem
    return None


def _check_one(volume: Volume, index: int, config: Config) -> str | None:
    path = volume.host_path
    if volume.mode not in MODES:
        return f"the mode of {path!r} must be one of {', '.join(MODES)}"
    if not os.path.isabs(path):
        return f"{path!r} is not an absolute path"
    if not os.path.exists(path):
        return f"{path!r} does not exist"
    real = Path(os.path.realpath(path))
    if real == Path("/") or real == config.home or real in config.home.parents:
        return f"{path!r} is too broad: the home directory and its parents cannot be mounted"
    for forbidden in config.forbidden_paths:
        if real == forbidden or forbidden in real.parents:
            return f"{path!r} resolves to {str(real)!r}, which is inside the forbidden path {str(forbidden)!r}"
    if volume.mode == "clone":
        if index != 0:
            return f"{path!r}: a clone is only allowed as the first volume"
        if not (real / ".git").exists():
            return f"{path!r} is not a git repository, so it cannot be cloned"
    return None
