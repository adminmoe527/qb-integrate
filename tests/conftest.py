"""Test configuration — isolate app-data paths per test."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_app_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    from qb_app import config as config_mod
    from qb_app.qb import account_map

    monkeypatch.setattr(config_mod, "CONFIG_PATH", tmp_path / "config.toml")
    monkeypatch.setattr(config_mod, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(config_mod, "ACCOUNT_MAP_PATH", tmp_path / "account_map.toml")
    monkeypatch.setattr(account_map, "ACCOUNT_MAP_PATH", tmp_path / "account_map.toml")
    return tmp_path
