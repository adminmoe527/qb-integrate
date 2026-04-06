"""Customer read/write."""
from __future__ import annotations

from typing import Any, Optional

from . import session as qbs
from .request import _as_value, run


def _to_dict(c: Any) -> dict[str, Any]:
    g = lambda n: _as_value(getattr(c, n, None))  # noqa: E731
    return {
        "list_id": g("ListID"),
        "name": g("Name"),
        "is_active": g("IsActive"),
        "balance": g("Balance"),
        "phone": g("Phone"),
        "email": g("Email"),
        "company_name": g("CompanyName"),
        "edit_sequence": g("EditSequence"),
    }


def list_customers(
    company_path: str,
    progid: str,
    qbxml_version: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    def build(rs):  # noqa: ANN001
        q = rs.AppendCustomerQueryRq()
        if limit:
            q.MaxReturned.SetValue(int(limit))

    with qbs.use(company_path, progid, qbxml_version) as sm:
        detail = run(sm, qbxml_version, build, "CustomerQueryRq")
        return [_to_dict(detail.GetAt(i)) for i in range(detail.Count)]


def add_customer(
    company_path: str,
    progid: str,
    qbxml_version: str,
    name: str,
    company_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    def build(rs):  # noqa: ANN001
        a = rs.AppendCustomerAddRq()
        a.Name.SetValue(name)
        if company_name:
            a.CompanyName.SetValue(company_name)
        if email:
            a.Email.SetValue(email)
        if phone:
            a.Phone.SetValue(phone)

    with qbs.use(company_path, progid, qbxml_version) as sm:
        if dry_run:
            rs = qbs.create_msg_set_request(sm, qbxml_version)
            build(rs)
            return {"dry_run": True, "xml": rs.ToXMLString()}
        return _to_dict(run(sm, qbxml_version, build, "CustomerAddRq"))
