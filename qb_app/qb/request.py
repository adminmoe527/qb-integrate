"""Helpers for building and running qbXML requests."""
from __future__ import annotations

from typing import Any, Callable

from . import session as qbs
from .errors import QBError


def _as_value(obj: Any) -> Any:
    if obj is None:
        return None
    fn = getattr(obj, "GetValue", None)
    if callable(fn):
        try:
            return fn()
        except Exception:  # noqa: BLE001
            return None
    return obj


def run(
    sm,  # noqa: ANN001
    qbxml_version: str,
    builder: Callable[[Any], Any],
    request_name: str = "",
) -> Any:
    req_set = qbs.create_msg_set_request(sm, qbxml_version)
    req_set.Attributes.OnError = 1
    builder(req_set)
    resp_list = sm.DoRequests(req_set).ResponseList
    if resp_list is None or resp_list.Count == 0:
        raise QBError(-1, "No response returned from QuickBooks.", request_name)
    response = resp_list.GetAt(0)
    code = int(response.StatusCode)
    if code not in (0, 1):  # 1 = no records found
        raise QBError(code, str(response.StatusMessage or ""), request_name)
    return response.Detail


def quick_host_query(progid: str, qbxml_version: str) -> dict[str, str]:
    with qbs.use("", progid, qbxml_version) as sm:
        detail = run(sm, qbxml_version, lambda rs: rs.AppendHostQueryRq(), "HostQueryRq")
        host = detail.GetAt(0) if hasattr(detail, "GetAt") else detail
        return {
            "product_name": str(_as_value(getattr(host, "ProductName", "")) or ""),
            "major_version": str(_as_value(getattr(host, "MajorVersion", "")) or ""),
            "country": str(_as_value(getattr(host, "Country", "")) or ""),
            "company_file": str(_as_value(getattr(host, "CompanyFilePath", "")) or ""),
        }
