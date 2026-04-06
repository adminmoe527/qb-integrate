"""Invoice read/write."""
from __future__ import annotations

from typing import Any, Optional

from . import session as qbs
from .request import _as_value, run


def _to_dict(inv: Any) -> dict[str, Any]:
    g = lambda n: _as_value(getattr(inv, n, None))  # noqa: E731
    cref = getattr(inv, "CustomerRef", None)
    return {
        "txn_id": g("TxnID"),
        "ref_number": g("RefNumber"),
        "txn_date": str(g("TxnDate") or ""),
        "customer": _as_value(getattr(cref, "FullName", None)) if cref else None,
        "total": g("Subtotal"),
        "balance_remaining": g("BalanceRemaining"),
        "is_paid": g("IsPaid"),
        "edit_sequence": g("EditSequence"),
    }


def list_invoices(
    company_path: str,
    progid: str,
    qbxml_version: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    def build(rs):  # noqa: ANN001
        q = rs.AppendInvoiceQueryRq()
        if limit:
            q.MaxReturned.SetValue(int(limit))

    with qbs.use(company_path, progid, qbxml_version) as sm:
        detail = run(sm, qbxml_version, build, "InvoiceQueryRq")
        return [_to_dict(detail.GetAt(i)) for i in range(detail.Count)]


def add_invoice(
    company_path: str,
    progid: str,
    qbxml_version: str,
    customer_name: str,
    line_items: list[dict[str, Any]],
    ref_number: Optional[str] = None,
    memo: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    def build(rs):  # noqa: ANN001
        a = rs.AppendInvoiceAddRq()
        a.CustomerRef.FullName.SetValue(customer_name)
        if ref_number:
            a.RefNumber.SetValue(ref_number)
        if memo:
            a.Memo.SetValue(memo)
        for li in line_items:
            ol = a.ORInvoiceLineAddList.Append().InvoiceLineAdd
            ol.ItemRef.FullName.SetValue(str(li["item_name"]))
            if li.get("quantity") is not None:
                ol.Quantity.SetValue(float(li["quantity"]))
            if li.get("rate") is not None:
                ol.ORRatePriceLevel.Rate.SetValue(float(li["rate"]))

    with qbs.use(company_path, progid, qbxml_version) as sm:
        if dry_run:
            rs = qbs.create_msg_set_request(sm, qbxml_version)
            build(rs)
            return {"dry_run": True, "xml": rs.ToXMLString()}
        return _to_dict(run(sm, qbxml_version, build, "InvoiceAddRq"))
