# aion-lithuanian-market-calendar - Site Map & Architecture

Mapped 2026-10-25 from the tracked file list, README, CHANGELOG, `pyproject.toml`, module docstrings, both CI workflows and targeted greps; re-mapped the same day after bringing the local copy up to date with GitHub (it had been three commits behind, missing the 1.0.2 release) and updated for version 1.1.0. Anything not verified is marked as such. This is a public repository: this file holds repository-relative paths only and nothing about internal systems.

## 1. High-Level Purpose

An MIT-licensed Python package (PyPI: `aion-lithuanian-market-calendar`, version `1.2.0` in `pyproject.toml`, latest on PyPI `1.1.0` until 1.2.0 is published) for the Lithuanian and European market calendar: the sixteen Lithuanian statutory holidays computed from the Labour Code, TARGET settlement days, timezone-correct trading sessions and phase for 19 EU venues, and exchange holiday data that updates without a release. English and Lithuanian throughout. No runtime dependencies except `tzdata` on Windows. Python `>=3.9`. Part of AION Analytics' open-source infrastructure.

Git: independent public repository on GitHub (organisation `AION-Analytics-India`), branch `main`. Releases are published only by the tag-triggered workflow.

## 2. Directory Structure

Tracked files. Ignored local items: `dist/`, `src/*.egg-info/`, `.pytest_cache/`.

```
aion-lithuanian-market-calendar/
├── README.md (English and Lithuanian)  README.lt.md (Lithuanian)  CHANGELOG.md  CONTRIBUTING.md  LICENSE  pyproject.toml  .gitignore
├── AGENTS.md  CLAUDE.md  SITE_MAP.md   agent contract, agent entry point, this map
├── .github/workflows/  test.yml (push, PR, monthly cron)   publish.yml (tag v*)
├── src/aion_lithuanian_market_calendar/
│   ├── __init__.py        public API (holidays, business days, sessions, venues, settlement, phase)
│   ├── holidays.py        Lithuanian statutory holidays, derived rather than tabulated
│   ├── microstructure.py  TARGET settlement days and intraday phase (1.1.0)
│   ├── sessions.py        is this venue trading at this instant, timezone-correct
│   ├── venues.py          continuous-session rules for 19 European venues
│   ├── store.py           holiday data, its manifest, and the refresh that needs no release
│   └── data/              holidays_2026.json, holidays_2027.json, manifest.json
└── tests/                 test_calendar.py, test_sessions.py, test_store.py, test_microstructure.py, test_daylight_saving.py
```

## 3. Core Components & Scripts

| Path | Purpose | Dependencies (Internal/External) |
| :--- | :--- | :--- |
| `src/aion_lithuanian_market_calendar/__init__.py` | Public API: holidays and business days, `is_market_open`, sessions (`is_open`, `is_trading_day`, `next_trading_day`, `session_bounds`), venues, and from 1.2.0 `is_daylight_saving`, `session_bounds_utc`, from 1.1.0 `is_settlement_day`, `next_settlement_day`, `target_closing_days`, `get_market_phase`, `phase_name` | Internal: all modules below |
| `holidays.py` | Lithuanian statutory holidays computed from rules (article 123 of the Labour Code), English and Lithuanian names | Standard library |
| `microstructure.py` | TARGET closing days (ECB rule from 2002) with English and Lithuanian names; settlement-day checks; `CONTINUOUS`/`CLOSED` phase | Internal: `holidays.easter_sunday`, `sessions`, `venues`. No data, no network |
| `sessions.py` | Session check per venue, converting to the venue's zone; naive datetimes raise | Internal: `venues.py`, `store.py`. External: `tzdata` on Windows only |
| `venues.py` | Continuous-trading windows for 19 EU venues; auctions not modelled | |
| `store.py` | Holiday data, manifest verification (`_verify`) and the optional refresh; falls back to bundled data or rule-only mode | External (only on a refresh): the public data repository `aion-market-calendar-data` over HTTPS. Env: `AION_LT_CALENDAR_URL`, `AION_LT_CALENDAR_CACHE`, `AION_LT_CALENDAR_OFFLINE` |
| `data/holidays_2026.json`, `holidays_2027.json`, `manifest.json` | Bundled exchange holiday data (offline fallback) | Verified before use |
| `tests/test_microstructure.py` | 18 tests: TARGET days equal the ECB's 2026 and 2027 lists, Good Friday and 16 February, names in both languages, phase boundaries, same instant in any zone, 17 November 2026 trades, naive datetimes refused | Isolated store (offline, empty cache) |
| `tests/test_calendar.py`, `test_sessions.py`, `test_store.py` | Holiday rules; session correctness and the 0.x timezone regression; store verification, fallback and refresh | `pytest` |
| `.github/workflows/test.yml` | Tests on three OSes with Python 3.9, 3.11, 3.13; a `data` job that verifies the bundled manifest with `store._verify` (fixed in 1.1.0) and forbids hard-coded UTC offsets | GitHub Actions |
| `.github/workflows/publish.yml` | On tag `v*`: test matrix, then publish | GitHub Actions |

## 4. External Repo Dependencies

Reads from other AION repositories: **only one, and it is public.**

| Repository | What | Direction | Where |
| :--- | :--- | :--- | :--- |
| `AION-Analytics-India/aion-market-calendar-data` (public, GitHub) | The verified holiday data the optional refresh downloads; also the home of the `ingest` tool that edits it | read over HTTPS on a refresh | `store.py`; referenced in `CONTRIBUTING.md` |

No tracked file refers to a private repository or to a local filesystem path. No database.

## 5. Scheduled Jobs

| Job | Where | What it triggers |
| :--- | :--- | :--- |
| GitHub Actions cron `0 6 1 * *` (06:00 UTC on the 1st of each month) | `.github/workflows/test.yml` | The test matrix and the bundled-data verification |
| Tag push `v*` | `.github/workflows/publish.yml` | Test matrix, then publish |

No launchd, crontab or local scheduler.

## 6. Legacy & Cleanup Candidates

### Resolved (2026-10-25)

| Item | Resolution |
| :--- | :--- |
| CI `data` job ran `python -m ingest verify`, a tool that moved to the data repository in 1.0.0 | Verifies the bundled manifest with the package's own check |
| `CONTRIBUTING.md` pointed at the same missing tool and used 2026-11-17 as its example date | Points to the data repository; placeholder dates. That date had been published there as a Nasdaq Baltic closure by mistake and was removed from the published data on 2026-10-25 |
| CHANGELOG said 1.0.1 was unreleased and had no 1.0.2 entry | Both dated (PyPI: 2026-09-12 and 2026-10-12) |
| Domain `aiondashboard.site` in metadata | Already corrected upstream in 1.0.2 (`aionanalytics.in`) before this session |
| No `AGENTS.md`, `CLAUDE.md` | Added, public-safe |
| Lithuanian text added in 1.1.0 (`README.md`, `README.lt.md`, `microstructure.py` names) | Reviewed and approved by a native speaker on 2026-10-25; one wording change applied ("Tai nustato") |

### Still open

| Path | Note |
| :--- | :--- |
| `venues.py` auction phases | Not modelled; Nasdaq Baltic pre-open and auction times were found only in secondary sources that disagree |
| `dist/`, `src/*.egg-info/` (local) | Git-ignored build output; the local egg-info was built from older metadata and is regenerated by any build |

Mapping gaps: `venues.py` and `store.py` were not read in full; CI history was not checked.
