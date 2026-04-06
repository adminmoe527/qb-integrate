"""Configuration loading and persistence.

Config lives at %LOCALAPPDATA%\\QBLocalApp\\config.toml on Windows.
On non-Windows (dev machines), falls back to ~/.qb_local_app/config.toml.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import tomli
import tomli_w


def app_data_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "QBLocalApp"
    return Path.home() / ".qb_local_app"


CONFIG_PATH = app_data_dir() / "config.toml"
LOG_DIR = app_data_dir() / "logs"
CACHE_DB = app_data_dir() / "cache.db"
ACCOUNT_MAP_PATH = app_data_dir() / "account_map.toml"


@dataclass
class Company:
    path: str
    nickname: str
    authorized: bool = False
    qbxml_version: str = "16.0"
    last_refreshed: Optional[str] = None


@dataclass
class QuickBooksSettings:
    qbfc_progid: str = "QBFC16.QBSessionManager"
    qbxml_version: str = "16.0"
    integration_user: str = ""
    company_folder: str = ""


@dataclass
class ServerSettings:
    host: str = "127.0.0.1"
    port: int = 8765
    log_level: str = "info"


@dataclass
class AppConfig:
    quickbooks: QuickBooksSettings = field(default_factory=QuickBooksSettings)
    server: ServerSettings = field(default_factory=ServerSettings)
    companies: list[Company] = field(default_factory=list)
    setup_complete: bool = False

    @classmethod
    def load(cls) -> "AppConfig":
        if not CONFIG_PATH.exists():
            return cls()
        with CONFIG_PATH.open("rb") as fh:
            data = tomli.load(fh)
        qb = QuickBooksSettings(**data.get("quickbooks", {}))
        srv = ServerSettings(**data.get("server", {}))
        companies = [Company(**c) for c in data.get("companies", [])]
        return cls(
            quickbooks=qb,
            server=srv,
            companies=companies,
            setup_complete=data.get("setup_complete", False),
        )

    def save(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

        def _drop_none(d: dict) -> dict:
            return {k: v for k, v in d.items() if v is not None}

        payload = {
            "setup_complete": self.setup_complete,
            "quickbooks": _drop_none(asdict(self.quickbooks)),
            "server": _drop_none(asdict(self.server)),
            "companies": [_drop_none(asdict(c)) for c in self.companies],
        }
        with CONFIG_PATH.open("wb") as fh:
            tomli_w.dump(payload, fh)

    def active_company(self, nickname: Optional[str] = None) -> Optional[Company]:
        if not self.companies:
            return None
        if nickname:
            for c in self.companies:
                if c.nickname == nickname:
                    return c
        return self.companies[0]

    def upsert_company(self, company: Company) -> None:
        for i, c in enumerate(self.companies):
            if c.path.lower() == company.path.lower():
                self.companies[i] = company
                return
        self.companies.append(company)
