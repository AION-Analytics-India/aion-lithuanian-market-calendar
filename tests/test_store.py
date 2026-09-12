"""The holiday store: verification, fail-safe fallback, and the update path.

The point of these tests is that nothing here may crash a caller's scheduler.
Every failure mode -- missing manifest, tampered file, dead host, no cache
directory -- must end at "use what we have and say so", never at an exception
thrown from inside a library at three in the morning.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from aion_lithuanian_market_calendar import store


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    """Every test gets a fresh cache and no network."""
    monkeypatch.setenv("AION_LT_CALENDAR_OFFLINE", "1")
    monkeypatch.setattr(store, "CACHE_DIR", tmp_path / "cache")
    store._state.update({"loaded": False, "data": {}, "source": "none", "warned": set()})
    yield
    store._state.update({"loaded": False, "data": {}, "source": "none", "warned": set()})


def _copy_bundled(into: Path) -> Path:
    into.mkdir(parents=True, exist_ok=True)
    for item in store.BUNDLED_DIR.glob("*.json"):
        (into / item.name).write_bytes(item.read_bytes())
    return into


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------
def test_the_bundled_data_verifies():
    ok, reason = store._verify(store.BUNDLED_DIR)
    assert ok, reason


def test_a_missing_manifest_fails_verification(tmp_path):
    (tmp_path / "holidays_2026.json").write_text("{}", encoding="utf-8")
    ok, reason = store._verify(tmp_path)
    assert not ok and "missing" in reason


def test_a_tampered_file_fails_verification(tmp_path):
    """The hash is the whole point: data that does not match its manifest is
    indistinguishable from data someone edited, and both are refused."""
    directory = _copy_bundled(tmp_path / "d")
    target = directory / "holidays_2026.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["exchange_holidays"].append("2026-07-04")
    target.write_text(json.dumps(payload), encoding="utf-8")
    ok, reason = store._verify(directory)
    assert not ok and "hash" in reason


def test_a_future_schema_is_refused(tmp_path):
    directory = _copy_bundled(tmp_path / "d")
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    manifest["schema_version"] = 99
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    ok, reason = store._verify(directory)
    assert not ok and "schema" in reason


# --------------------------------------------------------------------------
# Fail-safe
# --------------------------------------------------------------------------
def test_broken_data_falls_back_to_rule_only_without_raising(monkeypatch, tmp_path):
    """A scheduler that dies over a holiday table is worse than one that is
    slightly conservative."""
    empty = tmp_path / "nothing"
    empty.mkdir()
    monkeypatch.setattr(store, "BUNDLED_DIR", empty)
    data = store.load()
    assert data == {}
    assert store.source() == "rule-only"
    assert store.status()["rule_only"] is True


def test_rule_only_mode_answers_no_rather_than_inventing_a_closure(monkeypatch, tmp_path):
    """An invented closure makes a scheduler skip a real trading day, which is
    the more damaging error of the two."""
    empty = tmp_path / "nothing"
    empty.mkdir()
    monkeypatch.setattr(store, "BUNDLED_DIR", empty)
    assert store.is_exchange_holiday(date(2026, 4, 3)) is False
    assert store.half_day_close(date(2026, 12, 31)) is None


def test_an_unknown_year_is_not_a_holiday():
    assert store.is_exchange_holiday(date(2099, 4, 3)) is False


def test_the_warning_is_emitted_once_not_per_call(monkeypatch, tmp_path, caplog):
    """A per-call warning becomes noise, and noise is how a real warning goes
    unread."""
    empty = tmp_path / "nothing"
    empty.mkdir()
    monkeypatch.setattr(store, "BUNDLED_DIR", empty)
    with caplog.at_level("WARNING"):
        for _ in range(5):
            store._state["loaded"] = False
            store.load()
    assert sum("RULE-ONLY" in r.message for r in caplog.records) == 1


# --------------------------------------------------------------------------
# Offline and the network
# --------------------------------------------------------------------------
def test_offline_mode_makes_no_network_call(monkeypatch):
    def explode(*args, **kwargs):
        raise AssertionError("offline mode must not open a socket")
    monkeypatch.setattr(store, "_fetch", explode)
    assert "offline" in store.refresh(force=True)


def test_an_unreachable_host_is_not_an_error(monkeypatch):
    monkeypatch.delenv("AION_LT_CALENDAR_OFFLINE", raising=False)
    monkeypatch.setattr(store, "_fetch", lambda *a, **k: None)
    assert store.refresh(force=True) == "remote unreachable"
    assert store.load() != {}          # still serving bundled data


def test_remote_nonsense_is_refused(monkeypatch):
    monkeypatch.delenv("AION_LT_CALENDAR_OFFLINE", raising=False)
    monkeypatch.setattr(store, "_fetch", lambda *a, **k: b"<html>404</html>")
    assert "unparseable" in store.refresh(force=True)


def test_a_newer_remote_with_bad_hashes_is_refused(monkeypatch, tmp_path):
    """The remote host is a convenience, not a trusted input. It proves itself
    against the hashes every time or it is ignored."""
    monkeypatch.delenv("AION_LT_CALENDAR_OFFLINE", raising=False)
    manifest = json.loads((store.BUNDLED_DIR / "manifest.json").read_text(encoding="utf-8"))
    manifest["last_updated"] = "2099-01-01T00:00:00+00:00"

    def fake_fetch(url, timeout=5):
        if url.endswith("manifest.json"):
            return json.dumps(manifest).encode()
        return b'{"year": 2026}'        # real JSON, wrong content, wrong hash

    monkeypatch.setattr(store, "_fetch", fake_fetch)
    result = store.refresh(force=True)
    assert "verification failed" in result


def test_a_newer_remote_that_verifies_is_adopted(monkeypatch, tmp_path):
    """The whole point: a new holiday reaches users without a PyPI release."""
    monkeypatch.delenv("AION_LT_CALENDAR_OFFLINE", raising=False)
    published = _copy_bundled(tmp_path / "published")

    # Add a closure the bundled data does not have, then rebuild the manifest
    # exactly as the maintainer tooling would.
    target = published / "holidays_2026.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["exchange_holidays"] = sorted(set(payload["exchange_holidays"]) | {"2026-07-04"})
    # The per-venue list is authoritative when present, so a date added only to
    # the global list has no effect for XVIL. Writing this test wrong is how that
    # footgun was found; `python -m ingest verify` now reports the inconsistency.
    for mic, dates in payload["exchange_holidays_by_venue"].items():
        payload["exchange_holidays_by_venue"][mic] = sorted(set(dates) | {"2026-07-04"})
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    import hashlib
    manifest = json.loads((published / "manifest.json").read_text(encoding="utf-8"))
    manifest["files"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in published.glob("*.json") if p.name != "manifest.json"
    }
    manifest["last_updated"] = "2099-01-01T00:00:00+00:00"
    (published / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def fake_fetch(url, timeout=5):
        # Strip the cache-busting query, as any real host does when resolving a
        # path. The client appends ?v=<manifest last_updated> so that a payload
        # is always fetched against the manifest that asked for it -- GitHub raw
        # caches paths independently and will otherwise serve a fresh payload
        # beside a stale manifest for a few minutes after a push.
        name = url.rsplit("/", 1)[-1].split("?", 1)[0]
        return (published / name).read_bytes()

    monkeypatch.setattr(store, "_fetch", fake_fetch)
    assert "updated to" in store.refresh(force=True)
    assert store.source() == "cache"
    assert store.is_exchange_holiday(date(2026, 7, 4)) is True


# --------------------------------------------------------------------------
# Manifest content
# --------------------------------------------------------------------------
def test_the_manifest_carries_a_review_date():
    """So that next year's data is refreshed by a reminder rather than by a bug
    report."""
    manifest = json.loads((store.BUNDLED_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert date.fromisoformat(manifest["next_review_date"]) > date(2026, 1, 1)
    assert manifest["dataset_version"]
    assert manifest["years"]


def test_status_tells_a_caller_what_it_is_running_on():
    status = store.status()
    assert status["source"] in {"bundled", "cache", "rule-only"}
    assert status["rule_only"] is False
    assert 2026 in status["years"]


def test_a_stale_manifest_beside_a_fresh_payload_is_refused(monkeypatch, tmp_path):
    """GitHub raw caches paths independently.

    Observed 2026-09-12: minutes after a push, raw served holidays_2026.json
    from the new commit and manifest.json from the previous one. The pair does
    not verify, and refusing is correct -- adopting a payload whose hash nobody
    vouched for is exactly the 2026-06-26 failure.
    """
    monkeypatch.delenv("AION_LT_CALENDAR_OFFLINE", raising=False)
    stale = json.loads((store.BUNDLED_DIR / "manifest.json").read_text(encoding="utf-8"))
    stale["last_updated"] = "2099-01-01T00:00:00+00:00"      # newer, so it is tried
    stale["files"] = {k: "0" * 64 for k in stale["files"]}   # but hashes from nowhere

    def fake_fetch(url, timeout=5):
        if "manifest.json" in url:
            return json.dumps(stale).encode()
        name = url.rsplit("/", 1)[-1].split("?", 1)[0]
        return (store.BUNDLED_DIR / name).read_bytes()

    monkeypatch.setattr(store, "_fetch", fake_fetch)
    assert "verification failed" in store.refresh(force=True)
    # and the good bundled data is still what answers
    assert store.is_exchange_holiday(date(2026, 4, 3)) is True


def test_a_failed_verification_does_not_start_the_daily_clock(monkeypatch, tmp_path):
    """A transient CDN skew must be retried on the next call, not once tomorrow."""
    monkeypatch.delenv("AION_LT_CALENDAR_OFFLINE", raising=False)
    monkeypatch.setattr(store, "_fetch", lambda *a, **k: None)
    store.refresh(force=True)
    assert not (store.CACHE_DIR / ".last_check").exists(), (
        "an unreachable host marked the check as done, so the client would wait "
        "a day before trying again"
    )
