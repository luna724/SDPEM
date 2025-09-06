from __future__ import annotations

import os
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from modules.utils.ui.register import RegisterComponent


# Simple, maintainable registry keyed by RegisterComponent.instance_name
_REGISTRY: dict[str, "RegisterComponent"] = {}


#@codex
def _norm(name: str) -> str:
    # Normalize to a consistent key: strip, convert backslashes to slashes, remove leading/trailing slashes
    n = os.fspath(name).strip().replace("\\", "/")
    if n.endswith(".py"):
        n = n[:-3]
    if n.startswith("modules/tabs/"):
        n = n[len("modules/tabs/") :]
    return n.strip("/")


def register_instance(instance_name: str, rc: Any) -> None:
    """Register a RegisterComponent under its instance_name."""
    key = _norm(instance_name)
    _REGISTRY[key] = rc


def get_instance(instance_name: str) -> "RegisterComponent":
    """Retrieve a RegisterComponent by instance_name."""
    return _REGISTRY[_norm(instance_name)]


# Backward-compatible helpers used by existing code
def register_current_tab(value: Any, instance_path: str | None = None, attr: str = "components") -> None:  # noqa: ARG001
    if not instance_path:
        return
    register_instance(instance_path, value)


def get_components(path_like: str | os.PathLike[str]) -> Any:
    return get_instance(os.fspath(path_like))
