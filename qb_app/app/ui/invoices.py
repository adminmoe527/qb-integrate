"""Invoices UI."""
from __future__ import annotations

import json
from typing import Callable

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from ...qb import invoices as qb_invoices
from .. import state


def router(render: Callable) -> APIRouter:
    r = APIRouter()

    def _list(limit: int) -> tuple[list, str | None]:
        active = state.active_company()
        if not active or not active.authorized:
            return [], "No authorized company."
        try:
            rows = qb_invoices.list_invoices(
                active.path, state.config.quickbooks.qbfc_progid, active.qbxml_version, limit=limit,
            )
            return rows, None
        except Exception as e:  # noqa: BLE001
            return [], str(e)

    @r.get("/", response_class=HTMLResponse)
    async def index(request: Request, limit: int = 100):
        rows, error = _list(limit)
        return render(request, "invoices.html", rows=rows, error=error, limit=limit, result=None)

    @r.post("/new", response_class=HTMLResponse)
    async def create(
        request: Request,
        customer_name: str = Form(...),
        line_items_json: str = Form(...),
        ref_number: str = Form(""),
        memo: str = Form(""),
        dry_run: bool = Form(False),
    ):
        active = state.active_company()
        if not active or not active.authorized:
            return render(request, "invoices.html", rows=[], error="No authorized company.", result=None)
        try:
            line_items = json.loads(line_items_json)
        except json.JSONDecodeError as e:
            rows, _ = _list(100)
            return render(request, "invoices.html", rows=rows, error=f"Invalid JSON: {e}", result=None)
        try:
            result = qb_invoices.add_invoice(
                active.path, state.config.quickbooks.qbfc_progid, active.qbxml_version,
                customer_name=customer_name, line_items=line_items,
                ref_number=ref_number or None, memo=memo or None, dry_run=dry_run,
            )
        except Exception as e:  # noqa: BLE001
            rows, _ = _list(100)
            return render(request, "invoices.html", rows=rows, error=str(e), result=None)
        rows, _ = _list(100)
        return render(request, "invoices.html", rows=rows, error=None, result=result)

    return r
