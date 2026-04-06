"""Module-level app state."""
from __future__ import annotations

from typing import Optional

from ..config import AppConfig, Company

config: AppConfig = AppConfig.load()
active_nickname: Optional[str] = None


def active_company() -> Optional[Company]:
    return config.active_company(active_nickname)


def reload() -> None:
    """For tests: refresh config from disk."""
    global config, active_nickname
    config = AppConfig.load()
    active_nickname = None
