from qb_app.config import AppConfig, Company


def test_roundtrip(tmp_app_data):
    cfg = AppConfig()
    cfg.quickbooks.qbfc_progid = "QBFC16.QBSessionManager"
    cfg.companies.append(Company(path=r"C:\qb\a.qbw", nickname="Alpha", authorized=True))
    cfg.save()

    loaded = AppConfig.load()
    assert loaded.quickbooks.qbfc_progid == "QBFC16.QBSessionManager"
    assert len(loaded.companies) == 1
    assert loaded.companies[0].nickname == "Alpha"
    assert loaded.companies[0].authorized is True


def test_upsert(tmp_app_data):
    cfg = AppConfig()
    cfg.upsert_company(Company(path="C:/a.qbw", nickname="A"))
    cfg.upsert_company(Company(path="C:/a.qbw", nickname="A-renamed"))
    assert len(cfg.companies) == 1
    assert cfg.companies[0].nickname == "A-renamed"


def test_active_company(tmp_app_data):
    cfg = AppConfig()
    cfg.companies.extend([
        Company(path="C:/a.qbw", nickname="A"),
        Company(path="C:/b.qbw", nickname="B"),
    ])
    assert cfg.active_company().nickname == "A"
    assert cfg.active_company("B").nickname == "B"
    assert cfg.active_company("nonexistent").nickname == "A"
