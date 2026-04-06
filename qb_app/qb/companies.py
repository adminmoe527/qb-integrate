"""Company file registry — scan a folder for .qbw files."""
from __future__ import annotations

from pathlib import Path

from ..config import AppConfig, Company


def scan_folder(folder: str | Path) -> list[Path]:
    p = Path(folder)
    if not p.is_dir():
        return []
    return sorted(f for f in p.glob("*.qbw") if f.is_file())


def sync_companies_from_folder(config: AppConfig, folder: str | Path) -> list[Company]:
    known = {Path(c.path).resolve() for c in config.companies}
    added: list[Company] = []
    for f in scan_folder(folder):
        if f.resolve() in known:
            continue
        c = Company(path=str(f), nickname=f.stem)
        config.companies.append(c)
        added.append(c)
    config.quickbooks.company_folder = str(folder)
    return added
