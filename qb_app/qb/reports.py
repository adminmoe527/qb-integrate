"""Report queries (P&L, Balance Sheet, aging, etc.)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from . import session as qbs
from .request import _as_value, run

SUMMARY_REPORTS = {
    "ProfitAndLossStandard",
    "BalanceSheetStandard",
    "SalesByCustomerSummary",
    "InventoryValuationSummary",
}
AGING_REPORTS = {"ARAgingSummary", "APAgingSummary"}


@dataclass
class ReportResult:
    title: str
    columns: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)


def _flatten(ret: Any, title: str) -> ReportResult:
    columns: list[str] = []
    try:
        cdl = ret.ColDescList
        for i in range(cdl.Count):
            columns.append(
                str(_as_value(getattr(cdl.GetAt(i), "ColTitle", "")) or f"col_{i}")
            )
    except Exception:  # noqa: BLE001
        pass

    rows: list[dict[str, Any]] = []
    try:
        rdl = ret.ReportData.ORReportDataList
        for i in range(rdl.Count):
            entry = rdl.GetAt(i)
            data_row = getattr(entry, "DataRow", None)
            if data_row is None:
                text_row = getattr(entry, "TextRow", None)
                if text_row is not None:
                    rows.append({"_label": str(_as_value(getattr(text_row, "value", "")) or "")})
                continue
            row: dict[str, Any] = {
                "_label": str(_as_value(getattr(data_row, "RowData", None)) or "")
            }
            cdl2 = getattr(data_row, "ColDataList", None)
            if cdl2 is not None:
                for j in range(cdl2.Count):
                    header = columns[j] if j < len(columns) else f"col_{j}"
                    row[header] = _as_value(getattr(cdl2.GetAt(j), "value", None))
            rows.append(row)
    except Exception:  # noqa: BLE001
        pass

    return ReportResult(title=title, columns=columns, rows=rows)


def run_report(
    company_path: str,
    progid: str,
    qbxml_version: str,
    report_type: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> ReportResult:
    """Dispatch to the right qbXML request based on report_type."""

    def build(rs):  # noqa: ANN001
        if report_type in AGING_REPORTS:
            q = rs.AppendAgingReportQueryRq()
            q.AgingReportType.SetValue(report_type)
            if date_to:
                q.ReportPeriod.ToReportDate.SetValue(date_to, True)
        elif report_type in SUMMARY_REPORTS:
            q = rs.AppendGeneralSummaryReportQueryRq()
            q.GeneralSummaryReportType.SetValue(report_type)
            if date_from:
                q.ReportPeriod.FromReportDate.SetValue(date_from, True)
            if date_to:
                q.ReportPeriod.ToReportDate.SetValue(date_to, True)
        else:
            raise ValueError(f"Unknown report: {report_type}")

    with qbs.use(company_path, progid, qbxml_version) as sm:
        detail = run(sm, qbxml_version, build, report_type)
        return _flatten(detail, title=report_type)
