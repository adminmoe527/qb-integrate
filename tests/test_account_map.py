from qb_app.qb.account_map import AccountMapping


def test_set_and_lookup(tmp_app_data):
    m = AccountMapping()
    m.set_mapping("C:/a.qbw", "Sales - Retail", "Revenue: Retail")
    m.set_mapping("C:/b.qbw", "Retail Revenue", "Revenue: Retail")
    m.save()

    loaded = AccountMapping.load()
    assert loaded.canonical_for("C:/a.qbw", "Sales - Retail") == "Revenue: Retail"
    assert loaded.canonical_for("C:/b.qbw", "Retail Revenue") == "Revenue: Retail"
    assert loaded.canonical_for("C:/a.qbw", "Unknown") is None
    assert "Revenue: Retail" in loaded.canonical_accounts
