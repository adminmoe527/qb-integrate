"""App launcher.

Starts the uvicorn server on localhost and opens the default browser to
either the dashboard or the setup wizard. Run with ``--headless`` to skip
opening a browser (for scheduled/unattended invocations later).

Usage:
    python -m qb_app.launcher [--headless] [--port 8765]
"""
from __future__ import annotations

import argparse
import logging
import threading
import time
import webbrowser

import uvicorn

from . import APP_NAME
from .app import state
from .logging_setup import setup_logging

log = logging.getLogger(__name__)


def _open_browser(url: str, delay: float = 1.0) -> None:
    def _go() -> None:
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception as e:  # noqa: BLE001
            log.warning("Could not open browser: %s", e)

    threading.Thread(target=_go, daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser(prog="qb_app", description=f"{APP_NAME} launcher")
    parser.add_argument("--headless", action="store_true", help="Do not open a browser")
    parser.add_argument(
        "--port", type=int, default=None, help="Override server port (default from config)"
    )
    parser.add_argument(
        "--host", default=None, help="Override server host (default 127.0.0.1)"
    )
    args = parser.parse_args()

    setup_logging(state.config.server.log_level)

    host = args.host or state.config.server.host
    port = args.port or state.config.server.port

    url = f"http://{host}:{port}/"
    if not state.config.setup_complete:
        url = f"http://{host}:{port}/setup"

    log.info("Starting %s at %s", APP_NAME, url)
    if not args.headless:
        _open_browser(url)

    uvicorn.run(
        "qb_app.app.main:app",
        host=host,
        port=port,
        log_level=state.config.server.log_level,
        reload=False,
    )


if __name__ == "__main__":
    main()
