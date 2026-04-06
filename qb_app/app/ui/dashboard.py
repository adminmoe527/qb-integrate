"""Dashboard — minimal."""
from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse


def router(render: Callable) -> APIRouter:
    r = APIRouter()

    @r.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        return render(request, "dashboard.html")

    return r
