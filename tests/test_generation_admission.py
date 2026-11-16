"""Cross-process generation ordering and lock contention in the installed client."""
from datetime import date
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest
from aion_lithuanian_market_calendar import store


@pytest.mark.parametrize("force", [True, False])
@pytest.mark.parametrize("version,expected", [("2026.11.15.1", "conflicting generation refused"),
                                              ("2026.10.25", "older generation refused")])
def test_relabelled_timestamp_does_not_authorize_generation(monkeypatch, tmp_path, force, version, expected):
    m = json.loads((store.BUNDLED_DIR / "manifest.json").read_bytes())
    m.update(dataset_version=version, last_updated="2099-01-01T00:00:00+00:00")
    m["files"]["holidays_2026.json"] = "0" * 64
    def fetch(url):
        assert url.endswith("/manifest.json")
        return json.dumps(m).encode()
    monkeypatch.setattr(store, "_fetch", fetch)
    monkeypatch.setattr(store, "CACHE_DIR", tmp_path)
    monkeypatch.setenv("AION_LT_CALENDAR_OFFLINE", "0")
    assert store.refresh(force) == expected
    assert not (tmp_path / "ACTIVE").exists()


CHILD = """
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from aion_lithuanian_market_calendar import store
v, work = sys.argv[2], Path(sys.argv[3])
if v == 'read':
    print(store.status()['dataset_version'])
else:
    m = json.loads((store.BUNDLED_DIR/'manifest.json').read_bytes())
    m.update(dataset_version='2098.01.0'+v, last_updated='2098-01-0'+v+'T00:00:00+00:00')
    def fetch(url):
        if url.endswith('manifest.json'):
            return json.dumps(m).encode()
        if not (work / ('ready'+v)).exists():
            (work / ('ready'+v)).touch()
            deadline=time.monotonic()+15
            while not (work/('go'+v)).exists():
                if time.monotonic()>deadline: raise TimeoutError('test barrier')
                time.sleep(.01)
        return (store.BUNDLED_DIR / url.split('/')[-1].split('?')[0]).read_bytes()
    store._fetch=fetch
    print(store.refresh(True))
"""

def test_two_adopters_and_fresh_interpreter(tmp_path, monkeypatch):
    root = str(Path(store.__file__).resolve().parents[1])
    cache = tmp_path / "cache"; cache.mkdir()
    monkeypatch.setattr(store, "CACHE_DIR", cache)
    children = []
    def begin(v):
        env = dict(os.environ, AION_LT_CALENDAR_CACHE=str(cache),
                   AION_LT_CALENDAR_OFFLINE="1" if v == "read" else "0")
        p = subprocess.Popen([sys.executable, "-I", "-c", CHILD, root, v, str(tmp_path)],
                             env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        children.append(p)
        return p
    def result(p):
        out, err = p.communicate(timeout=18)
        assert p.returncode == 0, err
        return out.strip()
    try:
        with store._adoption_lock():
            older, newer = begin("1"), begin("2")
            deadline = time.monotonic() + 15
            while not all((tmp_path / key).exists() for key in ("ready1","ready2")):
                assert time.monotonic() < deadline
                time.sleep(.01)
            (tmp_path / "go2").touch()
            time.sleep(.15)
            assert not (cache / "ACTIVE").exists()
        assert result(newer).startswith("updated to")
        (tmp_path / "go1").touch()
        assert result(older) == "older generation refused"
        assert result(begin("read")) == "2098.01.02"
        assert not (cache / ".adoption.lock").exists()
    finally:
        for p in children:
            if p.poll() is None:
                p.kill(); p.wait()
