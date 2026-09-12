#!/usr/bin/env python3
"""Add or correct a holiday, then regenerate the manifest.

Not shipped in the wheel. This is maintainer tooling: it edits the JSON that
users download, so it lives in the repository and runs from a checkout.

    python -m ingest add-holiday --date 2026-11-17 --type exchange \\
        --reason "National day of mourning (Seimas resolution XIV-1234)"

    python -m ingest add-half-day --date 2026-12-31 --close 12:30 --reason "..."
    python -m ingest show --year 2026
    python -m ingest verify

Every change records *why*, because a date with no reason cannot be checked by
the next person and cannot be defended when a user asks where it came from.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUNDLED = REPO / "src" / "aion_lithuanian_market_calendar" / "data"
PUBLISHED = REPO / "data"
VALID_TYPES = ("exchange", "public")


def _year_file(directory: Path, year: int) -> Path:
    return directory / f"lt-{year}.json"


def _load(directory: Path, year: int) -> dict:
    path = _year_file(directory, year)
    if not path.exists():
        sys.exit(f"no data file for {year} at {path}. Create it first.")
    return json.loads(path.read_text(encoding="utf-8"))


def _save(directory: Path, year: int, payload: dict) -> None:
    _year_file(directory, year).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _record_change(payload: dict, entry: str) -> None:
    """Append to an in-file changelog.

    The file is the record. A git history is fine for maintainers but the JSON is
    what users download, and a user who wants to know why their exchange was shut
    on a Tuesday should not have to clone a repository to find out.
    """
    payload.setdefault("changes", []).append({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "change": entry,
    })


def add_holiday(args: argparse.Namespace) -> int:
    day = date.fromisoformat(args.date)
    for directory in (BUNDLED, PUBLISHED):
        payload = _load(directory, day.year)
        key = "exchange_holidays" if args.type == "exchange" else "public_holidays"
        existing = set(payload.get(key) or [])
        if args.date in existing:
            print(f"  {args.date} is already in {key} ({directory.name}); nothing to do")
            continue
        existing.add(args.date)
        payload[key] = sorted(existing)
        if args.type == "exchange":
            for mic, dates in (payload.get("exchange_holidays_by_venue") or {}).items():
                if not args.venue or args.venue.upper() == mic:
                    payload["exchange_holidays_by_venue"][mic] = sorted(set(dates) | {args.date})
        # A full closure cannot also be a half-day. Silently leaving both would
        # make the data self-contradictory; the session logic would honour the
        # closure and the half-day would sit there looking authoritative.
        for table in ("half_days",):
            if args.date in (payload.get(table) or {}):
                del payload[table][args.date]
                print(f"  removed {args.date} from {table}: a closure cannot also be a half-day")
        for mic, tbl in (payload.get("half_days_by_venue") or {}).items():
            tbl.pop(args.date, None)
        _record_change(payload, f"added {args.date} to {key}: {args.reason}")
        _save(directory, day.year, payload)
        print(f"  {directory.name}: added {args.date} to {key}")
    return 0


def add_half_day(args: argparse.Namespace) -> int:
    day = date.fromisoformat(args.date)
    datetime.strptime(args.close, "%H:%M")          # validates, raises if not a time
    for directory in (BUNDLED, PUBLISHED):
        payload = _load(directory, day.year)
        if args.date in set(payload.get("exchange_holidays") or []):
            sys.exit(f"  {args.date} is already a full exchange closure; "
                     f"remove it from exchange_holidays before making it a half-day")
        payload.setdefault("half_days", {})[args.date] = args.close
        for mic, tbl in (payload.get("half_days_by_venue") or {}).items():
            if not args.venue or args.venue.upper() == mic:
                tbl[args.date] = args.close
        _record_change(payload, f"half-day {args.date} closing {args.close}: {args.reason}")
        _save(directory, day.year, payload)
        print(f"  {directory.name}: {args.date} closes {args.close}")
    return 0


def show(args: argparse.Namespace) -> int:
    payload = _load(BUNDLED, args.year)
    print(f"  year {payload['year']}  verified_on {payload.get('verified_on')}")
    print(f"  public holidays:   {len(payload.get('public_holidays') or [])}")
    print(f"  exchange holidays: {len(payload.get('exchange_holidays') or [])}")
    print(f"  half-days:         {payload.get('half_days') or '{}'}")
    only_exchange = sorted(set(payload.get("exchange_holidays") or [])
                           - set(payload.get("public_holidays") or []))
    print(f"  closed but not a public holiday: {only_exchange or 'none'}")
    for change in (payload.get("changes") or [])[-5:]:
        print(f"    [{change['at'][:10]}] {change['change']}")
    return 0


def _consistency(payload: dict) -> list[str]:
    """Internal contradictions a hash cannot catch.

    The manifest proves the file is the one the maintainer wrote. It says nothing
    about whether what they wrote makes sense. These are the three ways this data
    has actually been got wrong so far, each found by a failing test.
    """
    problems: list[str] = []
    year = payload.get("year")
    global_ex = set(payload.get("exchange_holidays") or [])
    by_venue = payload.get("exchange_holidays_by_venue") or {}

    # 1. A per-venue list is authoritative when present, so a date added only to
    #    the global list silently does nothing for that venue.
    for mic, dates in by_venue.items():
        missing = global_ex - set(dates)
        if missing:
            problems.append(f"{mic} is missing {sorted(missing)}, which are in "
                            f"exchange_holidays; the per-venue list wins, so those "
                            f"dates have no effect for {mic}")

    # 2. A full closure cannot also be a half-day.
    for table_name in ("half_days",):
        for day in (payload.get(table_name) or {}):
            if day in global_ex:
                problems.append(f"{day} is both a closure and a {table_name} entry")
    for mic, table in (payload.get("half_days_by_venue") or {}).items():
        for day in table:
            if day in set(by_venue.get(mic, global_ex)):
                problems.append(f"{day} is both a closure and a half-day for {mic}")

    # 3. Every date must belong to the year the file claims.
    for field in ("public_holidays", "exchange_holidays"):
        for day in (payload.get(field) or []):
            if not str(day).startswith(str(year)):
                problems.append(f"{day} in {field} is not in year {year}")
    return problems


def verify(args: argparse.Namespace) -> int:
    """Check manifests against their files, and files against themselves."""
    sys.path.insert(0, str(REPO / "src"))
    from aion_lithuanian_market_calendar.store import _verify  # noqa: PLC2701
    failed = False
    for directory in (BUNDLED, PUBLISHED):
        ok, reason = _verify(directory)
        label = "src/.../data" if directory == BUNDLED else "data"
        print(f"  {label}: manifest {'ok' if ok else 'FAILED - ' + reason}")
        failed |= not ok
        for path in sorted(directory.glob("lt-*.json")):
            problems = _consistency(json.loads(path.read_text(encoding="utf-8")))
            if problems:
                failed = True
                for problem in problems:
                    print(f"    {path.name}: {problem}")
            else:
                print(f"    {path.name}: consistent")
    if failed:
        print("\n  if only the manifest failed, run:")
        print("    python ingest/build_manifest.py src/aion_lithuanian_market_calendar/data")
        print("    python ingest/build_manifest.py data")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="python -m ingest", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add-holiday", help="add a full closure")
    a.add_argument("--date", required=True, help="YYYY-MM-DD")
    a.add_argument("--type", required=True, choices=VALID_TYPES)
    a.add_argument("--reason", required=True, help="the circular or announcement")
    a.add_argument("--venue", help="restrict to one MIC; default all Baltic venues")
    a.set_defaults(func=add_holiday)

    h = sub.add_parser("add-half-day", help="add an early close")
    h.add_argument("--date", required=True)
    h.add_argument("--close", required=True, help="HH:MM local")
    h.add_argument("--reason", required=True)
    h.add_argument("--venue")
    h.set_defaults(func=add_half_day)

    s = sub.add_parser("show", help="summarise a year")
    s.add_argument("--year", type=int, required=True)
    s.set_defaults(func=show)

    v = sub.add_parser("verify", help="check manifests against their files")
    v.set_defaults(func=verify)

    args = ap.parse_args()
    rc = args.func(args)
    if args.command in {"add-holiday", "add-half-day"}:
        print("\n  now regenerate the manifests:")
        print("    python ingest/build_manifest.py src/aion_lithuanian_market_calendar/data")
        print("    python ingest/build_manifest.py data")
    return rc


if __name__ == "__main__":
    sys.exit(main())
