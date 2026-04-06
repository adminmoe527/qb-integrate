from qb_app.config import AppConfig
from qb_app.qb.companies import scan_folder, sync_companies_from_folder


def test_scan_folder(tmp_app_data, tmp_path):
    (tmp_path / "alpha.qbw").write_text("")
    (tmp_path / "beta.qbw").write_text("")
    (tmp_path / "notes.txt").write_text("")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "ignored.qbw").write_text("")

    found = scan_folder(tmp_path)
    names = sorted(p.name for p in found)
    assert names == ["alpha.qbw", "beta.qbw"]


def test_sync_adds_new_only(tmp_app_data, tmp_path):
    (tmp_path / "alpha.qbw").write_text("")
    cfg = AppConfig()
    added = sync_companies_from_folder(cfg, tmp_path)
    assert len(added) == 1
    assert len(cfg.companies) == 1

    # Second scan should add nothing.
    added2 = sync_companies_from_folder(cfg, tmp_path)
    assert added2 == []
    assert len(cfg.companies) == 1

    # New file appears → added.
    (tmp_path / "beta.qbw").write_text("")
    added3 = sync_companies_from_folder(cfg, tmp_path)
    assert len(added3) == 1
    assert len(cfg.companies) == 2
