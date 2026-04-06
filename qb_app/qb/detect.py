"""Detect the QB SDK / QBFC COM installation on the host machine.

Used by the Setup Wizard to decide whether the SDK needs to be installed
and which QBFC version to dispatch.
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class EnvironmentReport:
    is_windows: bool = False
    python_version: str = ""
    qbfc_progids: list[str] = field(default_factory=list)
    qbfc_installed: bool = False
    chosen_progid: Optional[str] = None
    chosen_qbxml_version: Optional[str] = None
    qb_running: bool = False
    qb_product_name: str = ""
    qb_major_version: str = ""
    company_file: str = ""
    issues: list[str] = field(default_factory=list)


def _probe_com() -> list[str]:
    """Probe winreg for installed QBFCnn.QBSessionManager ProgIDs."""
    if sys.platform != "win32":
        return []
    try:
        import winreg  # type: ignore
    except ImportError:
        return []

    found: list[str] = []
    for major in range(20, 5, -1):  # check QBFC20 down to QBFC6
        progid = f"QBFC{major}.QBSessionManager"
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, progid):
                found.append(progid)
        except FileNotFoundError:
            continue
        except OSError as e:
            log.debug("registry probe error for %s: %s", progid, e)
    return found


def _progid_to_qbxml_version(progid: str) -> str:
    # "QBFC16.QBSessionManager" -> "16.0"
    try:
        major = int(progid.split(".")[0].removeprefix("QBFC"))
        return f"{major}.0"
    except (ValueError, IndexError):
        return "16.0"


def probe_quickbooks(open_test_session: bool = False) -> EnvironmentReport:
    """Gather what we can about the host without requiring QuickBooks to be open.

    If open_test_session=True, additionally tries to open a read-only
    HostQueryRq to learn the QB product/version and the open company file.
    """
    report = EnvironmentReport(
        is_windows=(sys.platform == "win32"),
        python_version=sys.version.split()[0],
    )

    if not report.is_windows:
        report.issues.append("This app must run on Windows.")
        return report

    report.qbfc_progids = _probe_com()
    report.qbfc_installed = bool(report.qbfc_progids)
    if report.qbfc_installed:
        report.chosen_progid = report.qbfc_progids[0]
        report.chosen_qbxml_version = _progid_to_qbxml_version(report.chosen_progid)
    else:
        report.issues.append(
            "QuickBooks SDK (QBFC) not installed. Click 'Install QuickBooks SDK'."
        )
        return report

    if not open_test_session:
        return report

    # Try a lightweight HostQueryRq to confirm QB is running.
    try:
        from .request import quick_host_query  # local import to avoid cycles

        host = quick_host_query(report.chosen_progid, report.chosen_qbxml_version)
        report.qb_running = True
        report.qb_product_name = host.get("product_name", "")
        report.qb_major_version = host.get("major_version", "")
        report.company_file = host.get("company_file", "")
    except Exception as e:  # noqa: BLE001 — surfaced to UI as a soft issue
        log.info("HostQueryRq probe failed: %s", e)
        report.issues.append(f"QuickBooks is not responding: {e}")

    return report
