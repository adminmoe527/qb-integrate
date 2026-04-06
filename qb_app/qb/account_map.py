"""Canonical account map + combined-report merge logic.

Per-file reports never consult the map. Combined reports use it to merge
rows across files whose chart-of-accounts names differ.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

import tomli
import tomli_w

from ..config import ACCOUNT_MAP_PATH
from .reports import ReportResult


@dataclass
class AccountMapping:
    per_company: dict[str, dict[str, str]] = field(default_factory=dict)
    canonical_accounts: list[str] = field(default_factory=list)

    @classmethod
    def load(cls) -> "AccountMapping":
        if not ACCOUNT_MAP_PATH.exists():
            return cls()
        with ACCOUNT_MAP_PATH.open("rb") as fh:
            data = tomli.load(fh)
        return cls(
            per_company=data.get("per_company", {}),
            canonical_accounts=data.get("canonical_accounts", []),
        )

    def save(self) -> None:
        ACCOUNT_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        with ACCOUNT_MAP_PATH.open("wb") as fh:
            tomli_w.dump(asdict(self), fh)

    def canonical_for(self, company_path: str, raw_name: str) -> Optional[str]:
        return self.per_company.get(company_path, {}).get(raw_name)

    def set_mapping(self, company_path: str, raw_name: str, canonical: str) -> None:
        self.per_company.setdefault(company_path, {})[raw_name] = canonical
        if canonical and canonical not in self.canonical_accounts:
            self.canonical_accounts.append(canonical)


def _num(val) -> Optional[float]:  # noqa: ANN001
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(",", "").replace("$", ""))
    except (ValueError, TypeError):
        return None


@dataclass
class MergedRow:
    canonical: str
    values_by_company: dict[str, dict[str, float]] = field(default_factory=dict)
    total_by_column: dict[str, float] = field(default_factory=dict)


@dataclass
class CombinedReport:
    report_type: str
    companies: list[str]
    columns: list[str]
    merged_rows: list[MergedRow]
    unmapped_by_company: dict[str, list[str]] = field(default_factory=dict)


def combine(
    report_type: str,
    per_company: list[tuple[str, str, ReportResult]],  # (nickname, path, result)
    mapping: AccountMapping,
) -> CombinedReport:
    """Merge per-company ReportResults into one CombinedReport."""
    columns: list[str] = []
    seen: set[str] = set()
    for _, _, result in per_company:
        for col in result.columns:
            if col not in seen:
                columns.append(col)
                seen.add(col)

    merged: dict[str, MergedRow] = {}
    unmapped: dict[str, list[str]] = {}

    for nickname, company_path, result in per_company:
        per_unmapped: list[str] = []
        for row in result.rows:
            raw = str(row.get("_label") or "").strip()
            if not raw:
                continue
            canon = mapping.canonical_for(company_path, raw)
            if not canon:
                per_unmapped.append(raw)
                continue
            mr = merged.setdefault(canon, MergedRow(canonical=canon))
            vals: dict[str, float] = {}
            for col in columns:
                v = _num(row.get(col))
                if v is not None:
                    vals[col] = v
                    mr.total_by_column[col] = mr.total_by_column.get(col, 0.0) + v
            mr.values_by_company[nickname] = vals
        if per_unmapped:
            unmapped[nickname] = per_unmapped

    return CombinedReport(
        report_type=report_type,
        companies=[n for n, _, _ in per_company],
        columns=columns,
        merged_rows=[merged[k] for k in sorted(merged.keys())],
        unmapped_by_company=unmapped,
    )
