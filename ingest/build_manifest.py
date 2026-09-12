#!/usr/bin/env python3
"""Regenerate manifest.json from the holiday data files beside it.

The manifest must never be edited by hand. Its whole purpose is to prove that
the data files are the ones the maintainer intended, and a hash typed by a human
proves nothing. Run this after any change to a year file, in both the bundled
directory and the published data directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1


def build(directory: Path, dataset_version: str | None = None) -> dict:
    files = sorted(p for p in directory.glob("*.json") if p.name != "manifest.json")
    if not files:
        sys.exit(f"no data files in {directory}")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    years = sorted(int(json.loads(p.read_text(encoding="utf-8"))["year"]) for p in files)
    today = date.today()
    return {
        "schema_version": SCHEMA_VERSION,
        # Monotonic and human-readable. Comparison is string comparison, so the
        # format must sort correctly -- ISO does, a semver-ish one would not.
        "dataset_version": dataset_version or datetime.now(timezone.utc).strftime("%Y.%m.%d"),
        "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        # The reminder that upcoming-year data needs refreshing. Exchanges
        # publish the next year's calendar in the autumn; this lands before then.
        "next_review_date": date(today.year + (0 if today.month < 10 else 1), 10, 1).isoformat(),
        "years": years,
        "files": hashes,
        "source": "https://github.com/AION-Analytics-India/aion-lithuanian-market-calendar",
        "note": ("Public holidays are computed by the library and need no data. "
                 "This file carries exchange holidays and half-days, which are "
                 "announced rather than derived."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("directory", type=Path)
    ap.add_argument("--dataset-version")
    args = ap.parse_args()
    manifest = build(args.directory, args.dataset_version)
    (args.directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"  manifest for {args.directory}: {len(manifest['files'])} file(s), "
          f"years {manifest['years']}, version {manifest['dataset_version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
