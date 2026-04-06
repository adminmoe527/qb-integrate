"""Settings page."""
from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ...qb import companies as qb_companies
from .. import state


def router(render: Callable) -> APIRouter:
    r = APIRouter()

    @r.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return render(request, "settings.html")

    @r.post("/folder")
    async def update_folder(folder: str = Form(...)):
        qb_companies.sync_companies_from_folder(state.config, folder)
        state.config.save()
        return RedirectResponse("/settings/", status_code=303)

    @r.post("/rerun-wizard")
    async def rerun_wizard():
        state.config.setup_complete = False
        state.config.save()
        return RedirectResponse("/setup", status_code=303)

    @r.post("/companies/{nickname}/remove")
    async def remove_company(nickname: str):
        state.config.companies = [
            c for c in state.config.companies if c.nickname != nickname
        ]
        state.config.save()
        return RedirectResponse("/settings/", status_code=303)

    return r
