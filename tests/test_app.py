"""FastAPI smoke tests via TestClient."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_app_data):
    from qb_app.app import state
    state.reload()
    from qb_app.app.main import app
    return TestClient(app)


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_redirects_to_setup_when_not_complete(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/setup"


def test_setup_pages_render(client):
    for path in ["/setup", "/setup/check", "/setup/folder", "/setup/authorize", "/setup/test"]:
        r = client.get(path)
        assert r.status_code == 200, f"{path} -> {r.status_code}"


def test_main_pages_render_after_setup_complete(client):
    from qb_app.app import state
    state.config.setup_complete = True
    state.config.save()
    for path in ["/", "/reports/", "/customers/", "/invoices/", "/settings/", "/account-map/"]:
        r = client.get(path)
        assert r.status_code == 200, f"{path} -> {r.status_code}"


def test_rerun_wizard_flips_flag(client):
    from qb_app.app import state
    state.config.setup_complete = True
    state.config.save()
    r = client.post("/settings/rerun-wizard", follow_redirects=False)
    assert r.status_code == 303
    from qb_app.config import AppConfig
    assert AppConfig.load().setup_complete is False
