"""Account Map page — maps per-company chart of accounts to canonical names."""
from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ...qb.account_map import AccountMapping
from .. import state


def router(render: Callable) -> APIRouter:
    r = APIRouter()

    @r.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        mapping = AccountMapping.load()
        return render(
            request,
            "account_map.html",
            mapping=mapping,
            companies=state.config.companies,
        )

    @r.post("/set")
    async def set_mapping(
        company_path: str = Form(...),
        raw_name: str = Form(...),
        canonical: str = Form(...),
    ):
        mapping = AccountMapping.load()
        mapping.set_mapping(company_path, raw_name, canonical)
        mapping.save()
        return RedirectResponse("/account-map/", status_code=303)

    return r
