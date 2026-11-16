import json
from datetime import date
import pytest
from aion_lithuanian_market_calendar import store, checked_session_bounds_utc

def test_verified_venue_and_year_only(monkeypatch,tmp_path):
    monkeypatch.setenv('AION_LT_CALENDAR_OFFLINE','1')
    monkeypatch.setattr(store,'CACHE_DIR',tmp_path)
    assert checked_session_bounds_utc(date(2026,12,31),'XVIL') is None
    assert checked_session_bounds_utc(date(2026,11,18),'XVIL') is not None
    for day,mic in [(date(2026,2,16),'XPAR'),(date(2099,2,16),'XVIL'),(date(2027,2,16),'XVIL')]:
        with pytest.raises(ValueError,match='verified'): checked_session_bounds_utc(day,mic)

def test_damaged_new_generation_retains_previous(monkeypatch,tmp_path):
    monkeypatch.setenv('AION_LT_CALENDAR_OFFLINE','0')
    monkeypatch.setattr(store,'CACHE_DIR',tmp_path)
    manifest=json.loads((store.BUNDLED_DIR/'manifest.json').read_text());manifest['dataset_version']='2099.01.01';manifest['last_updated']='2099-01-01T00:00:00+00:00'
    def fetch(url):
        if url.endswith('/manifest.json'): return json.dumps(manifest).encode()
        return (store.BUNDLED_DIR/url.split('/')[-1].split('?')[0]).read_bytes()
    monkeypatch.setattr(store,'_fetch',fetch)
    assert store.refresh(force=True).startswith('updated to')
    old=(tmp_path/'ACTIVE').read_bytes();manifest['dataset_version']='2099.02.01';manifest['last_updated']='2099-02-01T00:00:00+00:00'
    manifest['files']['holidays_2026.json']='0'*64
    assert 'verification failed' in store.refresh(force=True)
    assert old==(tmp_path/'ACTIVE').read_bytes()
    assert checked_session_bounds_utc(date(2026,11,18),'XRIS') is None


@pytest.mark.parametrize("field", ["exchange_holidays_by_venue", "half_days_by_venue"])
def test_unattested_changed_or_missing_mic_maps_are_refused(monkeypatch, field):
    payload = json.loads((store.BUNDLED_DIR / "holidays_2026.json").read_bytes())
    payload[field].pop("XRIS")
    monkeypatch.setattr(store, "load", lambda: {2026: payload})
    with pytest.raises(ValueError, match="No verified"):
        checked_session_bounds_utc(date(2026, 11, 18), "XRIS")


@pytest.mark.parametrize("force", [False, True])
def test_older_manifest_cannot_replace_bundled_generation(monkeypatch, tmp_path, force):
    manifest = json.loads((store.BUNDLED_DIR / "manifest.json").read_bytes())
    manifest.update(dataset_version="2026.10.25", last_updated="2026-10-25T06:34:55+00:00")
    def fetch(url):
        assert url.endswith("/manifest.json"), "older generation should fetch no payload"
        return json.dumps(manifest).encode()
    monkeypatch.setenv("AION_LT_CALENDAR_OFFLINE", "0")
    monkeypatch.setattr(store, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(store, "_fetch", fetch)
    assert store.refresh(force=force) == "older generation refused"
    assert not (tmp_path / "ACTIVE").exists()
