"""FastAPI application entry point."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .. import APP_NAME, __version__
from ..logging_setup import setup_logging
from . import state
from .ui import (
    account_map as account_map_ui,
    customers as customers_ui,
    dashboard as dashboard_ui,
    invoices as invoices_ui,
    reports as reports_ui,
    settings as settings_ui,
    setup as setup_ui,
)

setup_logging(state.config.server.log_level)

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app = FastAPI(title=APP_NAME, version=__version__)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.middleware("http")
async def setup_gate(request: Request, call_next):  # noqa: ANN001
    path = request.url.path
    if (
        not state.config.setup_complete
        and not path.startswith("/setup")
        and not path.startswith("/static")
        and path != "/healthz"
    ):
        return RedirectResponse("/setup")
    return await call_next(request)


def render(request: Request, template: str, **ctx) -> HTMLResponse:
    ctx.setdefault("app_name", APP_NAME)
    ctx.setdefault("version", __version__)
    ctx.setdefault("config", state.config)
    ctx.setdefault("active_company", state.active_company())
    return templates.TemplateResponse(request, template, ctx)


app.include_router(setup_ui.router(render), prefix="/setup")
app.include_router(dashboard_ui.router(render))
app.include_router(reports_ui.router(render), prefix="/reports")
app.include_router(customers_ui.router(render), prefix="/customers")
app.include_router(invoices_ui.router(render), prefix="/invoices")
app.include_router(settings_ui.router(render), prefix="/settings")
app.include_router(account_map_ui.router(render), prefix="/account-map")


@app.post("/companies/switch/{nickname}")
async def switch_company(nickname: str):
    state.active_nickname = nickname
    return RedirectResponse("/", status_code=303)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
