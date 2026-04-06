"""Combine logic (now lives in account_map.py)."""
from qb_app.qb.account_map import AccountMapping, combine
from qb_app.qb.reports import ReportResult


def _r(rows):
    return ReportResult(title="ProfitAndLossStandard", columns=["Total"], rows=rows)


def test_combine_merges_and_reports_unmapped(tmp_app_data):
    m = AccountMapping()
    m.set_mapping("C:/a.qbw", "Sales - Retail", "Revenue: Retail")
    m.set_mapping("C:/b.qbw", "Retail Revenue", "Revenue: Retail")

    per_company = [
        ("Alpha", "C:/a.qbw", _r([
            {"_label": "Sales - Retail", "Total": "100.00"},
            {"_label": "Sales - Wholesale", "Total": "50.00"},
        ])),
        ("Beta", "C:/b.qbw", _r([
            {"_label": "Retail Revenue", "Total": 200.00},
            {"_label": "Misc Income", "Total": 25.00},
        ])),
    ]

    c = combine("ProfitAndLossStandard", per_company, m)
    assert len(c.merged_rows) == 1
    assert c.merged_rows[0].canonical == "Revenue: Retail"
    assert c.merged_rows[0].total_by_column["Total"] == 300.00
    assert "Alpha" in c.unmapped_by_company
    assert "Sales - Wholesale" in c.unmapped_by_company["Alpha"]
    assert "Misc Income" in c.unmapped_by_company["Beta"]


def test_combine_with_no_mapping(tmp_app_data):
    m = AccountMapping()
    per_company = [("A", "C:/a.qbw", _r([{"_label": "Sales", "Total": 100.0}]))]
    c = combine("Rpt", per_company, m)
    assert c.merged_rows == []
    assert c.unmapped_by_company["A"] == ["Sales"]
