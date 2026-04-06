"""Setup Wizard — server-rendered, no JS."""
from __future__ import annotations

import datetime as _dt
import logging
import subprocess
import sys
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ...qb import companies as qb_companies
from ...qb import customers as qb_customers
from ...qb import invoices as qb_invoices
from ...qb import reports as qb_reports
from ...qb.detect import probe_quickbooks
from ...qb.errors import QBConnectionError, QBNotAuthorizedError
from ...qb.request import quick_host_query
from .. import state

log = logging.getLogger(__name__)
BUNDLED_SDK = Path(sys.prefix).parent / "vendor" / "QBSDK160.exe"


def router(render: Callable) -> APIRouter:
    r = APIRouter()

    @r.get("", response_class=HTMLResponse)
    async def welcome(request: Request):
        return render(request, "setup/welcome.html")

    @r.get("/check", response_class=HTMLResponse)
    async def check(request: Request):
        return render(request, "setup/check.html", report=probe_quickbooks())

    @r.post("/install-sdk")
    async def install_sdk():
        if not BUNDLED_SDK.exists():
            return {"ok": False, "error": f"SDK installer not found at {BUNDLED_SDK}"}
        try:
            subprocess.run([str(BUNDLED_SDK), "/S", "/v/qn"], check=True, timeout=600)
        except subprocess.CalledProcessError as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True}

    @r.get("/detect", response_class=HTMLResponse)
    async def detect(request: Request):
        report = probe_quickbooks(open_test_session=True)
        if report.chosen_progid:
            state.config.quickbooks.qbfc_progid = report.chosen_progid
        if report.chosen_qbxml_version:
            state.config.quickbooks.qbxml_version = report.chosen_qbxml_version
        state.config.save()
        return render(request, "setup/detect.html", report=report)

    @r.get("/folder", response_class=HTMLResponse)
    async def folder_get(request: Request):
        return render(
            request,
            "setup/folder.html",
            current_folder=state.config.quickbooks.company_folder,
            companies=state.config.companies,
        )

    @r.post("/folder")
    async def folder_post(folder: str = Form(...)):
        qb_companies.sync_companies_from_folder(state.config, folder)
        state.config.save()
        return RedirectResponse("/setup/authorize", status_code=303)

    @r.get("/authorize", response_class=HTMLResponse)
    async def authorize_get(request: Request):
        return render(request, "setup/authorize.html", companies=state.config.companies)

    @r.post("/authorize/{nickname}")
    async def authorize_one(request: Request, nickname: str):
        c = next((c for c in state.config.companies if c.nickname == nickname), None)
        if not c:
            return render(request, "setup/authorize.html", companies=state.config.companies, message=f"Unknown: {nickname}")
        try:
            info = quick_host_query(state.config.quickbooks.qbfc_progid, state.config.quickbooks.qbxml_version)
            if Path(info.get("company_file", "")).resolve() != Path(c.path).resolve():
                msg = f"Please open {c.nickname} in QuickBooks first."
            else:
                c.authorized = True
                state.config.upsert_company(c)
                state.config.save()
                msg = f"✅ {c.nickname} authorized."
        except (QBNotAuthorizedError, QBConnectionError) as e:
            msg = f"❌ {c.nickname}: {e}"
        return render(request, "setup/authorize.html", companies=state.config.companies, message=msg)

    @r.get("/test", response_class=HTMLResponse)
    async def test_get(request: Request):
        return render(request, "setup/test.html", results=None)

    @r.post("/test", response_class=HTMLResponse)
    async def test_post(request: Request):
        company = next((c for c in state.config.companies if c.authorized), None)
        if company is None:
            return render(request, "setup/test.html", results=None, error="No authorized company.")
        progid = state.config.quickbooks.qbfc_progid
        qbxml = company.qbxml_version
        results: dict[str, dict] = {}

        try:
            n = len(qb_customers.list_customers(company.path, progid, qbxml, limit=1))
            results["read"] = {"ok": True, "detail": f"Fetched {n} customer(s)."}
        except Exception as e:  # noqa: BLE001
            results["read"] = {"ok": False, "detail": str(e)}

        try:
            today = _dt.date.today()
            rep = qb_reports.run_report(
                company.path, progid, qbxml, "ProfitAndLossStandard",
                date_from=today.replace(day=1).isoformat(), date_to=today.isoformat(),
            )
            results["report"] = {"ok": True, "detail": f"P&L returned {len(rep.rows)} row(s)."}
        except Exception as e:  # noqa: BLE001
            results["report"] = {"ok": False, "detail": str(e)}

        try:
            dr = qb_invoices.add_invoice(
                company.path, progid, qbxml,
                customer_name="__SmokeTest__",
                line_items=[{"item_name": "__SmokeTest__", "quantity": 1, "rate": 1.0}],
                dry_run=True,
            )
            results["write"] = {"ok": True, "detail": f"qbXML validated ({len(dr.get('xml', ''))} bytes)."}
        except Exception as e:  # noqa: BLE001
            results["write"] = {"ok": False, "detail": str(e)}

        return render(request, "setup/test.html", results=results)

    @r.post("/finish")
    async def finish():
        state.config.setup_complete = True
        state.config.save()
        return RedirectResponse("/", status_code=303)

    return r
