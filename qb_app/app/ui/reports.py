"""Reports UI."""
from __future__ import annotations

import io
from typing import Callable, Optional

import pandas as pd
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from ...qb import reports as qb_reports
from ...qb.account_map import AccountMapping, combine
from .. import state

REPORT_CHOICES = [
    ("ProfitAndLossStandard", "Profit & Loss"),
    ("BalanceSheetStandard", "Balance Sheet"),
    ("SalesByCustomerSummary", "Sales by Customer"),
    ("InventoryValuationSummary", "Inventory Valuation"),
    ("ARAgingSummary", "A/R Aging Summary"),
    ("APAgingSummary", "A/P Aging Summary"),
]


def _run(company, report_type, date_from, date_to):  # noqa: ANN001
    return qb_reports.run_report(
        company.path,
        state.config.quickbooks.qbfc_progid,
        company.qbxml_version,
        report_type,
        date_from,
        date_to,
    )


def router(render: Callable) -> APIRouter:
    r = APIRouter()

    @r.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return render(request, "reports_index.html", report_choices=REPORT_CHOICES, result=None)

    @r.get("/run", response_class=HTMLResponse)
    async def run(
        request: Request,
        report_type: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        all_companies: bool = False,
        merged: bool = False,
    ):
        if all_companies:
            per_company: list[tuple[str, str, qb_reports.ReportResult]] = []
            errors: dict[str, str] = {}
            for c in state.config.companies:
                if not c.authorized:
                    continue
                try:
                    per_company.append((c.nickname, c.path, _run(c, report_type, date_from, date_to)))
                except Exception as e:  # noqa: BLE001
                    errors[c.nickname] = str(e)
            mapping = AccountMapping.load()
            combined = combine(report_type, per_company, mapping) if merged else None
            return render(
                request,
                "reports_combined.html",
                per_company=per_company,
                errors=errors,
                report_type=report_type,
                date_from=date_from,
                date_to=date_to,
                combined=combined,
                merged=merged,
                mapping=mapping,
            )

        active = state.active_company()
        if not active or not active.authorized:
            return render(
                request,
                "reports_index.html",
                report_choices=REPORT_CHOICES,
                error="No authorized company.",
            )
        try:
            result = _run(active, report_type, date_from, date_to)
        except Exception as e:  # noqa: BLE001
            return render(
                request,
                "reports_index.html",
                report_choices=REPORT_CHOICES,
                error=str(e),
            )
        return render(
            request,
            "reports_index.html",
            report_choices=REPORT_CHOICES,
            result=result,
            report_type=report_type,
            date_from=date_from,
            date_to=date_to,
        )

    @r.get("/export.csv")
    async def export_csv(report_type: str, date_from: Optional[str] = None, date_to: Optional[str] = None):
        active = state.active_company()
        if not active:
            return HTMLResponse("No active company", status_code=400)
        result = _run(active, report_type, date_from, date_to)
        buf = io.StringIO()
        pd.DataFrame(result.rows).to_csv(buf, index=False)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{report_type}.csv"'},
        )

    @r.get("/export.xlsx")
    async def export_xlsx(report_type: str, date_from: Optional[str] = None, date_to: Optional[str] = None):
        active = state.active_company()
        if not active:
            return HTMLResponse("No active company", status_code=400)
        result = _run(active, report_type, date_from, date_to)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame(result.rows).to_excel(writer, index=False, sheet_name=report_type[:31])
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{report_type}.xlsx"'},
        )

    return r
