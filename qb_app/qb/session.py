"""Single-session QBFC wrapper. One file open at a time — QB's hard limit."""
from __future__ import annotations

import logging
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .. import APP_NAME
from .errors import QBConnectionError, QBNotAuthorizedError

log = logging.getLogger(__name__)

CT_LOCAL_QBD = 1            # QB must already be running
CT_LOCAL_QBD_LAUNCH_UI = 3  # App can launch QB itself
OM_DONT_CARE = 2            # required for multi-user attach

_lock = threading.RLock()
_sm = None
_open_path: str = ""
_open_progid: str = ""
_open_qbxml: str = "16.0"


def _norm(p: str) -> str:
    return str(Path(p)).lower() if p else ""


def _close() -> None:
    global _sm, _open_path, _open_progid
    if _sm is None:
        return
    try:
        _sm.EndSession()
    except Exception as e:  # noqa: BLE001
        log.warning("EndSession: %s", e)
    try:
        _sm.CloseConnection()
    except Exception as e:  # noqa: BLE001
        log.warning("CloseConnection: %s", e)
    _sm = None
    _open_path = ""
    _open_progid = ""


def _open(company_path: str, progid: str, qbxml_version: str) -> None:
    global _sm, _open_path, _open_progid, _open_qbxml
    if sys.platform != "win32":
        raise QBConnectionError("QuickBooks integration only works on Windows.")
    try:
        import pythoncom  # type: ignore
        import win32com.client  # type: ignore
    except ImportError as e:
        raise QBConnectionError("pywin32 is not installed.") from e
    try:
        pythoncom.CoInitialize()
    except Exception:  # noqa: BLE001
        pass
    try:
        _sm = win32com.client.Dispatch(progid)
    except Exception as e:  # noqa: BLE001
        raise QBConnectionError(f"Could not create {progid}. SDK installed?") from e
    try:
        _sm.OpenConnection2("", APP_NAME, CT_LOCAL_QBD)
    except Exception as e:  # noqa: BLE001
        raise QBConnectionError(f"OpenConnection2 failed: {e}") from e
    try:
        _sm.BeginSession(company_path or "", OM_DONT_CARE)
    except Exception as e:  # noqa: BLE001
        try:
            _sm.CloseConnection()
        except Exception:  # noqa: BLE001
            pass
        _sm = None
        msg = str(e)
        if "not authorized" in msg.lower() or "0x80040420" in msg:
            raise QBNotAuthorizedError(
                "This app is not authorized for this company file yet."
            ) from e
        raise QBConnectionError(f"BeginSession failed: {msg}") from e
    _open_path = company_path
    _open_progid = progid
    _open_qbxml = qbxml_version
    log.info("QB session opened: %s", company_path or "<active>")


@contextmanager
def use(company_path: str, progid: str, qbxml_version: str) -> Iterator:
    """Borrow the single QB session, switching files if needed.

    Yields the raw COM SessionManager; callers use it to build requests via
    ``create_msg_set_request()`` / ``do_requests()``.
    """
    global _sm
    with _lock:
        if _sm is not None and (
            _norm(_open_path) != _norm(company_path) or _open_progid != progid
        ):
            _close()
        if _sm is None:
            _open(company_path, progid, qbxml_version)
        try:
            yield _sm
        except Exception:
            _close()
            raise


def create_msg_set_request(sm, qbxml_version: str):  # noqa: ANN001
    major, minor = (qbxml_version.split(".") + ["0"])[:2]
    return sm.CreateMsgSetRequest("US", int(major), int(minor))


def close_all() -> None:
    with _lock:
        _close()
