"""Holiday data, its manifest, and the update that does not need a release.

Why this exists at all
----------------------
Lithuanian *public* holidays are computed, not tabulated — twelve fixed dates,
two from the Easter computus, two from a first-Sunday rule — so they need no data
file and no update, ever. That property is worth keeping and this module does not
touch it.

Exchange holidays are a different animal. A venue closes when it says it closes,
and governments declare days of mourning with a week's notice. Nothing derives
them. So they live in JSON, and the JSON can be refreshed without anyone
publishing a new wheel — because the alternative is a library that is silently
wrong for three weeks until a maintainer notices.

The manifest
------------
``manifest.json`` records a schema version, a dataset version, when the data was
last updated, a SHA-256 of every data file, and a ``next_review_date``.

It is **mandatory**: if it is missing, unparseable, or its hashes disagree with
the files beside it, the library says so loudly and falls back to **rule-only
mode** — weekends and computed public holidays, no exchange data. It does not
crash, because a scheduler that dies at 03:00 over a holiday table is worse than
one that is slightly conservative, and it does not carry on quietly, because
silently-stale holiday data is the failure this whole design exists to prevent.

Updating
--------
On first use in a process, and at most once a day, the library compares its
bundled manifest against a remote one. If the remote is newer *and* its files
hash correctly, they are cached under ``~/.cache/aion_lt_calendar/`` and used
from then on. No release required.

Every part of that is fail-safe. Offline, behind a proxy, air-gapped, DNS broken,
remote serving nonsense — all end the same way: use what is bundled, log once,
carry on. Set ``AION_LT_CALENDAR_OFFLINE=1`` to skip the network entirely.

**A hash is checked before anything downloaded is trusted.** The remote host is
not a trusted input; it is a convenience that must prove itself each time.
"""
from __future__ import annotations

import hashlib
import re
import errno
import tempfile
import shutil
from contextlib import contextmanager
import json
import logging
import os
import time as _time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1

#: Shipped inside the wheel. Always present, always the fallback.
BUNDLED_DIR = Path(__file__).resolve().parent / "data"

def _default_cache_dir() -> Path:
    """Where refreshed data lands. Per-user; a library must never need root.

    Honours XDG_CACHE_HOME, because that is the documented way for a user to say
    where caches go and ignoring it is how a library ends up writing somewhere
    the user did not expect.

    Falls back to a temp directory when the preferred location cannot be
    created. That is not hypothetical: on the machine this was developed on,
    ``~/.cache`` is owned by root -- something ran under sudo once -- so nothing
    running as the user can create a directory inside it. Without a fallback,
    auto-update would be permanently and *silently* off on that machine, which is
    precisely the failure this design exists to prevent. A temp directory loses
    the cache on reboot, which costs one extra fetch and is strictly better than
    never updating.
    """
    override = os.environ.get("AION_LT_CALENDAR_CACHE")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    preferred = base / "aion_lt_calendar"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        probe = preferred / ".writable"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        return preferred
    except OSError:
        import tempfile
        fallback = Path(tempfile.mkdtemp(prefix="aion_lt_calendar-"))
        log.warning(
            "Cannot write to %s, so refreshed holiday data will be cached in %s "
            "and lost on reboot. Auto-update still works; it just re-fetches more "
            "often. Set AION_LT_CALENDAR_CACHE to choose somewhere writable.",
            preferred, fallback,
        )
        return fallback


CACHE_DIR = _default_cache_dir()

#: Default remote. GitHub raw rather than a vanity domain: it is free, it is
#: versioned in the same repository as the code, anyone can audit what changed
#: and when, and it does not quietly expire the way a domain registration does.
#: Override with AION_LT_CALENDAR_URL to serve from a CDN later.
REMOTE_BASE = os.environ.get(
    "AION_LT_CALENDAR_URL",
    "https://raw.githubusercontent.com/AION-Analytics-India/"
    "aion-market-calendar-data/main/lt",
).rstrip("/")

#: How long a refresh check is considered fresh. A holiday announced today is
#: not needed within the hour, and hammering a static host from every process
#: start is rude.
CHECK_INTERVAL_SECONDS = 24 * 60 * 60
NETWORK_TIMEOUT_SECONDS = 5

_state: dict[str, Any] = {"loaded": False, "data": {}, "source": "none", "warned": set()}


def _warn_once(key: str, message: str, *args: Any) -> None:
    """Warn, but not on every call. A per-request warning becomes noise, and
    noise is how a real warning goes unread."""
    if key not in _state["warned"]:
        _state["warned"].add(key)
        log.warning(message, *args)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


_ACTIVE_POINTER = "ACTIVE"
_DATASETS_DIR = "generations"
def _read_manifest(directory):
    return json.loads((directory/'manifest.json').read_text('utf-8'))

def _version_key(doc):
    stamp=datetime.fromisoformat(doc['last_updated'].replace('Z','+00:00'))
    if stamp.utcoffset() is None: raise ValueError('Source generation requires an aware timestamp')
    return stamp.astimezone(timezone.utc)

def _shape(doc):
    if not isinstance(doc,dict) or doc.get('schema_version')!=1: return False
    files=doc.get('files')
    if not isinstance(files,dict) or not 1 <= len(files) <= 64: return False
    if not all(re.fullmatch(r'holidays_[0-9]{4}\.json',n) and isinstance(h,str) and re.fullmatch('[a-f0-9]{64}',h) for n,h in files.items()): return False
    try: return sorted(doc['years'])==sorted(int(n[9:13]) for n in files) and bool(_version_key(doc))
    except (ValueError,TypeError,KeyError,AttributeError): return False

def _active_pointer_dir() -> Path | None:
    try:
        name = (CACHE_DIR / _ACTIVE_POINTER).read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not name or "/" in name or "\\" in name or name.startswith("."):
        return None
    return CACHE_DIR / _DATASETS_DIR / name


def _candidates() -> list[tuple[str, Path]]:
    """Every place verified data may live, in tie-break order."""
    found: list[tuple[str, Path]] = []
    pointed = _active_pointer_dir()
    if pointed is not None:
        found.append(("cache", pointed))
    found.append(("cache", CACHE_DIR))          # flat layout, also written by older versions
    found.append(("bundled", BUNDLED_DIR))
    return found


def _verified_candidates() -> list[tuple[str, Path, dict[str, Any]]]:
    """Every verified dataset, newest first (ties keep the tie-break order of _candidates)."""
    found: list[tuple[str, Path, dict[str, Any]]] = []
    for label, directory in _candidates():
        if not (directory / "manifest.json").exists():
            continue
        ok, reason = _verify(directory)
        if not ok:
            _warn_once(f"verify-{label}-{directory.name}",
                       "Holiday data in the %s directory failed verification (%s); "
                       "ignoring it.", label, reason)
            continue
        found.append((label, directory, _read_manifest(directory)))
    found.sort(key=lambda item: _version_key(item[2]), reverse=True)   # stable sort
    return found


def _select() -> tuple[str, Path, dict[str, Any]] | None:
    """The newest verified dataset. A cache never beats a newer bundled copy."""
    found = _verified_candidates()
    return found[0] if found else None


def _signature() -> tuple:
    """Cheap fingerprint of what is on disk: stat calls only, no hashing."""
    parts: list[Any] = []
    for name in (_ACTIVE_POINTER, "manifest.json"):
        try:
            st = (CACHE_DIR / name).stat()
            parts.append((name, st.st_mtime_ns, st.st_size))
        except OSError:
            parts.append((name, None))
    parts.append(str(CACHE_DIR))
    return tuple(parts)


# --------------------------------------------------------------------------
# Refresh
# --------------------------------------------------------------------------
def _atomic_write_bytes(target: Path, body: bytes) -> None:
    """Write a temp file unique to this call (process *and* thread), then rename over the target."""
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, target)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _lock_contention(error: OSError, *, windows: bool | None = None) -> bool:
    """Only retry bounded lock contention; never grant access or steal a lock.

    Windows CRT _wopen reports sharing denial as errno EACCES without a
    winerror attribute. The same errno on POSIX remains an immediate refusal.
    A persistent Windows permission denial still expires at the same deadline.
    """
    if isinstance(error, FileExistsError):
        return True
    native = getattr(error, 'winerror', None)
    if native in (5, 32, 33):
        return True
    if windows is None:
        windows = os.name == 'nt'
    return windows and native is None and error.errno == errno.EACCES


@contextmanager
def _adoption_lock():
    """Serialize the version check and pointer switch across processes.

    A crashed writer's lock is not silently stolen. Refresh fails closed until
    its owner explicitly verifies and removes the abandoned lock.
    """
    lock = CACHE_DIR / ".adoption.lock"
    deadline = _time.monotonic() + 5
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except OSError as exc:
            # NTFS can report a delete-pending/sharing state as access denied
            # instead of EEXIST. Retry only known native contention errors;
            # never steal the marker or weaken directory permissions.
            if not _lock_contention(exc):
                raise
            if _time.monotonic() >= deadline:
                raise TimeoutError("another data adopter owns the cache lock")
            _time.sleep(0.01)
    try:
        os.write(fd, str(os.getpid()).encode())
        yield
    finally:
        os.close(fd)
        deadline = _time.monotonic() + 5
        while True:
            try:
                lock.unlink()
                break
            except OSError as exc:
                if not _lock_contention(exc) or _time.monotonic() >= deadline:
                    raise
                _time.sleep(0.01)



def _verify(directory: Path) -> tuple[bool, str]:
    """Does this directory hold a manifest whose hashes match its files?"""
    manifest_path = directory / "manifest.json"
    if not manifest_path.exists():
        return False, "manifest.json is missing"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"manifest.json is unreadable ({exc})"
    if not isinstance(manifest,dict): return False, "invalid manifest"
    if manifest.get("schema_version") != SCHEMA_VERSION:
        return False, (f"manifest schema {manifest.get('schema_version')!r} is not "
                       f"the {SCHEMA_VERSION} this library understands")
    if not _shape(manifest): return False, "invalid manifest file list or timestamps"
    files = manifest.get("files") or {}
    if not files:
        return False, "manifest lists no data files"
    for name, expected in files.items():
        candidate = directory / name
        if candidate.is_symlink() or not candidate.is_file():
            return False, f"{name} is listed in the manifest but missing"
        actual = _sha256(candidate)
        if actual != expected:
            return False, f"{name} does not match its manifest hash"
    return True, "ok"


def _read_dataset(directory: Path) -> dict[int, dict[str, Any]]:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    years: dict[int, dict[str, Any]] = {}
    for name in manifest.get("files", {}):
        payload = json.loads((directory / name).read_text(encoding="utf-8"))
        year = int(payload["year"])
        if name != f"holidays_{year}.json" or not isinstance(payload.get("exchange_holidays"),list): raise ValueError("Inconsistent year or missing closure list")
        years[year] = payload
    return years


# --------------------------------------------------------------------------
# Refresh
# --------------------------------------------------------------------------
def _offline() -> bool:
    return os.environ.get("AION_LT_CALENDAR_OFFLINE", "").strip().lower() in {"1", "true", "yes"}


def _fetch(url: str, timeout: int = NETWORK_TIMEOUT_SECONDS) -> bytes | None:
    try:
        from .software_updates import fetch_bytes
        return fetch_bytes(url,max_bytes=2097152,network_authorized=True,
                           allow_test_http=urllib.parse.urlsplit(REMOTE_BASE).hostname=="127.0.0.1")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as exc:
        log.debug("holiday data fetch failed for %s: %s", url, exc)
        return None


def _due_for_check() -> bool:
    stamp = CACHE_DIR / ".last_check"
    try:
        return (_time.time() - stamp.stat().st_mtime) > CHECK_INTERVAL_SECONDS
    except OSError:
        return True


def _mark_checked() -> None:
    """Start the daily clock. Called only on a conclusive outcome.

    Deliberately NOT called when a download fails verification or a host is
    unreachable. GitHub raw caches paths independently and can serve a stale
    manifest beside a fresh payload for a few minutes after a push -- observed
    on 2026-09-12. Marking that as "checked today" made a client wait a full day
    for data that was already published. A transient failure should be retried
    on the next call, not once tomorrow.
    """
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / ".last_check").write_text(
            datetime.now(timezone.utc).isoformat(timespec="seconds"), encoding="utf-8")
    except OSError:
        pass


def refresh(force: bool = False) -> str:
    """Fetch newer holiday data if there is any. Returns what happened.

    Never raises. Every failure path ends at "keep using what we have", because
    a calendar that throws on a DNS hiccup is worse than one that is a week out
    of date.
    """
    if _offline():
        return "offline: AION_LT_CALENDAR_OFFLINE is set"
    if not force and not _due_for_check():
        return "checked recently"

    raw = _fetch(f"{REMOTE_BASE}/manifest.json")
    if raw is None:
        _warn_once("unreachable", "Holiday data host unreachable; using bundled data.")
        return "remote unreachable"
    try:
        remote = json.loads(raw)
    except (ValueError,UnicodeError):
        _warn_once("badjson", "Remote holiday manifest is not valid JSON; using bundled data.")
        return "remote manifest unparseable"
    if not isinstance(remote,dict) or remote.get("schema_version") != SCHEMA_VERSION:
        return "remote uses a different schema"

    if not _shape(remote): return "invalid manifest contract"
    selected=_select()
    if selected and _version_key(remote)<_version_key(selected[2]):
        return "older generation refused"
    staging=None
    try:
        CACHE_DIR.mkdir(parents=True,exist_ok=True)
        staging=Path(tempfile.mkdtemp(prefix=".stage-",dir=CACHE_DIR))
        # Fetch each payload keyed to the manifest we just read.
        #
        # GitHub raw caches per path for a few minutes and the paths expire
        # independently, so immediately after a push it will happily serve a
        # fresh payload alongside a stale manifest -- observed on 2026-09-12,
        # manifest two minutes behind its own data. The hash check caught it and
        # refused, which is correct but means a client hitting that window waits
        # a day for data that is already published.
        #
        # Appending the manifest's own version pins the payload to the manifest
        # that asked for it: a stale manifest now fetches its matching stale
        # payload, which verifies and is merely a little old, instead of a
        # mismatched pair that verifies against nothing. Consistent-and-behind
        # beats inconsistent-and-refused.
        version = str(remote.get("last_updated") or remote.get("dataset_version") or "")
        suffix = f"?v={urllib.parse.quote(version)}" if version else ""
        for name in remote.get("files", {}):
            body = _fetch(f"{REMOTE_BASE}/{name}{suffix}")
            if body is None:
                return f"could not download {name}"
            (staging / name).write_bytes(body)
        (staging / "manifest.json").write_bytes(raw)
        ok, reason = _verify(staging)
        if not ok:
            _warn_once("badhash", "Downloaded holiday data failed verification (%s); "
                                  "keeping existing data.", reason)
            return f"verification failed: {reason}"
        _read_dataset(staging)
        generation=hashlib.sha256(raw).hexdigest()
        with _adoption_lock():
            selected=_select()
            if selected and _version_key(remote)<=_version_key(selected[2]):
                if remote!=selected[2]: return "older or conflicting generation refused"
                _mark_checked();return "already current"
            dest=CACHE_DIR/_DATASETS_DIR/generation
            dest.parent.mkdir(exist_ok=True)
            if not dest.exists(): staging.rename(dest)
            if not _verify(dest)[0]: return "verification failed: generation"
            _atomic_write_bytes(CACHE_DIR/_ACTIVE_POINTER,generation.encode())
        _mark_checked()
        _state["loaded"] = False          # force a reload on next read
        log.info("Holiday data updated to %s", remote.get("last_updated"))
        return f"updated to {remote.get('last_updated')}"
    except OSError as exc:
        # Loud, not debug. A cache that cannot be written means auto-update is
        # off, and an update that is silently off is the thing this module was
        # written to prevent.
        _warn_once("nocache",
                   "Could not write refreshed holiday data to %s (%s); continuing "
                   "with the bundled data. Set AION_LT_CALENDAR_CACHE to a "
                   "writable path to enable updates.", CACHE_DIR, exc)
        return f"could not write cache: {exc}"
    except (ValueError,KeyError,TypeError):
        return "invalid payload"
    finally:
        if staging and staging.is_dir(): shutil.rmtree(staging,ignore_errors=True)


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------
def load(auto_refresh: bool = True) -> dict[int, dict[str, Any]]:
    """The holiday dataset, refreshing at most once a day.

    Falls back to rule-only mode -- an empty dataset -- if nothing verifies. The
    caller then still has weekends and computed public holidays, which is the
    part that cannot go stale.
    """
    if _state["loaded"] and _state.get("signature")==_signature():
        return _state["data"]

    if auto_refresh:
        refresh()

    for label,directory,manifest in _verified_candidates():
        if not (directory / "manifest.json").exists():
            continue
        ok, reason = _verify(directory)
        if not ok:
            _warn_once(f"verify-{label}",
                       "Holiday data in the %s directory failed verification (%s); "
                       "ignoring it.", label, reason)
            continue
        try:
            _state["data"] = _read_dataset(directory)
            _state["dir"] = directory
            _state["signature"] = _signature()
            _state["source"] = label
            _state["loaded"] = True
            return _state["data"]
        except (OSError, KeyError, ValueError) as exc:
            _warn_once(f"read-{label}", "Could not read holiday data from %s: %s", label, exc)

    _warn_once("ruleonly",
               "No verified holiday data; running in RULE-ONLY mode. Weekends and "
               "computed Lithuanian public holidays still apply, but exchange "
               "holidays and half-days are unknown.")
    _state["data"] = {}
    _state["source"] = "rule-only"
    _state["loaded"] = True
    return _state["data"]


def source() -> str:
    """Where the data in use came from: cache, bundled, or rule-only."""
    load()
    return _state["source"]


def status() -> dict[str, Any]:
    """Everything a caller needs to decide whether to trust the answer.

    Exposed because a library that quietly degrades is the thing this module was
    written to avoid: if it is in rule-only mode, the caller should be able to
    find that out without reading the logs.
    """
    load()
    directory = _state.get("dir", BUNDLED_DIR) if _state["source"] != "rule-only" else BUNDLED_DIR
    manifest: dict[str, Any] = {}
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    return {
        "source": _state["source"],
        "rule_only": _state["source"] == "rule-only",
        "dataset_version": manifest.get("dataset_version"),
        "last_updated": manifest.get("last_updated"),
        "next_review_date": manifest.get("next_review_date"),
        "years": sorted(_state["data"]),
        "offline": _offline(),
        "remote": REMOTE_BASE,
    }


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------
def _year(day: date) -> dict[str, Any]:
    return load().get(day.year, {})


def is_exchange_holiday(day: date, mic: str = "XVIL") -> bool:
    """Is the venue closed all day?

    Unknown years answer False, not True. A library that invents a closure would
    make a scheduler skip a real trading day, which is the more damaging error --
    and ``status()['rule_only']`` tells a caller when the answer is uninformed.
    """
    payload = _year(day)
    key = day.isoformat()
    by_venue = payload.get("exchange_holidays_by_venue") or {}
    if mic.upper() in by_venue:
        return key in by_venue[mic.upper()]
    return key in (payload.get("exchange_holidays") or [])


def is_public_holiday_listed(day: date) -> bool:
    """Whether the data file lists this as a public holiday.

    Only useful for cross-checking the computed rule; ``holidays.py`` remains the
    authority for Lithuanian public holidays, because a rule cannot go stale.
    """
    return day.isoformat() in (_year(day).get("public_holidays") or [])


def half_day_close(day: date, mic: str = "XVIL") -> time | None:
    """The early close for a half-day, or None on a normal day."""
    payload = _year(day)
    key = day.isoformat()
    by_venue = payload.get("half_days_by_venue") or {}
    table = by_venue.get(mic.upper()) if mic.upper() in by_venue else payload.get("half_days") or {}
    value = (table or {}).get(key)
    if not value:
        return None
    try:
        hour, _, minute = str(value).partition(":")
        return time(int(hour), int(minute or 0))
    except (TypeError, ValueError):
        log.debug("half-day close %r for %s is not a time", value, key)
        return None
