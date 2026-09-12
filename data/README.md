# Published holiday data

This directory is what the library downloads. It is served from GitHub raw, so
what users receive is exactly what is in this repository at that commit, and any
change is visible in the history.

## Why this exists when public holidays are computed

Lithuanian *public* holidays need no data file — they are derivable and the
library computes them. Nothing here changes that.

*Exchange* holidays are not derivable. A venue closes when it announces it will,
and a government can declare a day of mourning at a week's notice. A library that
bundled those and shipped them once a year would be quietly wrong for weeks at a
time. So they live here, and the library refreshes them without needing a release.

## Files

| file | what it is |
| --- | --- |
| `manifest.json` | schema version, dataset version, last updated, SHA-256 of every file, next review date |
| `lt-YYYY.json` | one year of exchange holidays and half-days |

**`manifest.json` is never edited by hand.** Its purpose is to prove the data
files are the ones the maintainer intended, and a hash typed by a person proves
nothing. Regenerate it:

```bash
python ingest/build_manifest.py src/aion_lithuanian_market_calendar/data
python ingest/build_manifest.py data
```

## Schema

```json
{
  "year": 2026,
  "timezone": "Europe/Vilnius",
  "public_holidays": ["2026-01-01", "..."],
  "exchange_holidays": ["2026-01-01", "2026-04-03", "..."],
  "exchange_holidays_by_venue": { "XVIL": ["..."], "XRIS": ["..."] },
  "half_days": { "2026-12-31": "12:30" },
  "half_days_by_venue": { "XVIL": { "2026-12-31": "12:30" } },
  "verified_on": "2026-09-12",
  "changes": [{ "at": "...", "change": "why this date is here" }]
}
```

`public_holidays` is present for cross-checking only. The library's computed rule
remains the authority, because a rule cannot go stale.

**`exchange_holidays_by_venue` wins where it is present.** A date added only to
the global `exchange_holidays` has no effect for a venue that has its own list.
`python -m ingest verify` reports that inconsistency — it is the easiest mistake
to make here.

## Update cadence

- **Annually, by 1 October** — exchanges publish the next year's calendar in the
  autumn. `next_review_date` in the manifest is the reminder.
- **Within a day, ad hoc** — a mourning day or an unscheduled closure. Use the
  CLI, regenerate both manifests, commit. Users pick it up within 24 hours
  without upgrading.

## Corrections

If a date here is wrong, that is a bug worth reporting. Open an issue with the
date, the venue, and the announcement it comes from — the announcement matters,
because a date with no source cannot be checked by the next person.
