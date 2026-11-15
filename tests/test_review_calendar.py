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
    manifest=json.loads((store.BUNDLED_DIR/'manifest.json').read_text());manifest['last_updated']='2099-01-01T00:00:00+00:00'
    def fetch(url):
        if url.endswith('/manifest.json'): return json.dumps(manifest).encode()
        return (store.BUNDLED_DIR/url.split('/')[-1].split('?')[0]).read_bytes()
    monkeypatch.setattr(store,'_fetch',fetch)
    assert store.refresh(force=True).startswith('updated to')
    old=(tmp_path/'ACTIVE').read_bytes();manifest['last_updated']='2099-02-01T00:00:00+00:00'
    manifest['files']['holidays_2026.json']='0'*64
    assert 'verification failed' in store.refresh(force=True)
    assert old==(tmp_path/'ACTIVE').read_bytes()
    assert checked_session_bounds_utc(date(2026,11,18),'XRIS') is None
