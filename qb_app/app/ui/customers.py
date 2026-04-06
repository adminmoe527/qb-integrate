"""Customers UI."""
from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from ...qb import customers as qb_customers
from .. import state


def router(render: Callable) -> APIRouter:
    r = APIRouter()

    def _list(limit: int) -> tuple[list, str | None]:
        active = state.active_company()
        if not active or not active.authorized:
            return [], "No authorized company."
        try:
            rows = qb_customers.list_customers(
                active.path, state.config.quickbooks.qbfc_progid, active.qbxml_version, limit=limit,
            )
            return rows, None
        except Exception as e:  # noqa: BLE001
            return [], str(e)

    @r.get("/", response_class=HTMLResponse)
    async def index(request: Request, limit: int = 100):
        rows, error = _list(limit)
        return render(request, "customers.html", rows=rows, error=error, limit=limit, result=None)

    @r.post("/new", response_class=HTMLResponse)
    async def create(
        request: Request,
        name: str = Form(...),
        company_name: str = Form(""),
        email: str = Form(""),
        phone: str = Form(""),
        dry_run: bool = Form(False),
    ):
        active = state.active_company()
        if not active or not active.authorized:
            return render(request, "customers.html", rows=[], error="No authorized company.", result=None)
        try:
            result = qb_customers.add_customer(
                active.path, state.config.quickbooks.qbfc_progid, active.qbxml_version,
                name=name, company_name=company_name or None,
                email=email or None, phone=phone or None, dry_run=dry_run,
            )
        except Exception as e:  # noqa: BLE001
            rows, _ = _list(100)
            return render(request, "customers.html", rows=rows, error=str(e), result=None)
        rows, _ = _list(100)
        return render(request, "customers.html", rows=rows, error=None, result=result)

    return r
