# Changelog

## 1.2.0 (2026-11-02): daylight saving state and UTC session bounds

### Added

- `is_daylight_saving(day, venue="XVIL")`: whether the venue's zone is on daylight saving
  that day.
- `session_bounds_utc(day, venue="XVIL")`: the day's open and close as UTC datetimes, or
  `None` if the venue is closed. Venue hours are fixed in local time, so these move by an
  hour at each change.

Both read the IANA zone database, so no change date is written in the package. Session
answers do not change: `is_open` and `session_bounds` already converted through `zoneinfo`.
This package has no commodity venue, so the Indian commodity hours do not apply here.

The new Lithuanian text in `README.lt.md` is awaiting review by a native speaker.

## 1.1.0 (2026-10-25)

### Added — settlement days and intraday phase

New module `aion_lithuanian_market_calendar.microstructure`, also exported from the
package root. No new dependency, no network access, no change to the data or to how
it is fetched.

- `is_settlement_day(day)`, `next_settlement_day(after)` and
  `target_closing_days(year)`: euro settlement runs on TARGET (T2 and T2S), which
  closes on New Year's Day, Good Friday, Easter Monday, 1 May, 25 and 26 December,
  besides weekends (ECB, long-term calendar of December 2000, applying from 2002
  until further notice). Computed, not tabulated, so correct for any year from 2002.
  This is a different list from the Lithuanian public holidays in both directions:
  Good Friday 2026 is a business day in Lithuania and not a settlement day;
  16 February is a settlement day although offices are shut. Each closing day
  carries its English and Lithuanian name.
- `get_market_phase(at, venue="XVIL")`: `CONTINUOUS` or `CLOSED`, using the same
  holiday, half-day and break rules as `is_open`, with a half-open window (the
  closing minute is `CLOSED`). Auctions, pre-open and post-trading are still not
  modelled: the published sources found disagree on them, so no phase is returned
  for them rather than a guessed one. The phase strings match the Indian sibling
  package. `phase_name(phase, "lt")` gives the Lithuanian display name.

### Fixed

- CI: the `data` job ran `python -m ingest verify`, but the `ingest` tool moved to
  aion-market-calendar-data in 1.0.0, so the job could not pass. It now verifies
  the bundled data against its manifest with the package's own check.
- `CONTRIBUTING.md` now sends data changes to the data repository, where the tool
  is, and uses placeholder dates. Its example date, 17 November 2026, was once
  published there as a Nasdaq Baltic closure by mistake; the published data was
  corrected on 25 October 2026 and installed copies pick that up on their next
  daily refresh, with no release.
- This changelog listed 1.0.1 as unreleased and had no entry for 1.0.2; both are
  on PyPI and now dated below.

The new Lithuanian names and the Lithuanian README text added in this version were
reviewed and approved by a native speaker on 2026-10-25, against VLKK orthography and
Bank of Lithuania and Nasdaq Vilnius terminology. One wording change followed: "Atsako"
became "Tai nustato" in the settlement paragraph.

---

## 1.0.2 — 2026-10-12

**No functional change.** Package metadata and documentation: the homepage, the
author contact and the package discovery links now point to aionanalytics.in and
the GitHub repository, and the Lithuanian README was aligned with the release
versions.

---

## 1.0.1 — 2026-09-12

This entry said "unreleased" until 1.1.0; 1.0.1 was published to PyPI on 2026-09-12.

**No functional change.** This release exists only to establish the trusted
publishing path.

1.0.0 was uploaded manually with an API token, which means PyPI already holds
that version and no workflow can replace it — PyPI versions are immutable. So the
first release actually produced by GitHub Actions has to be a new number, and
this is it.

If you are on 1.0.0 there is nothing here for you. Upgrade when 1.1.0 arrives.

---

## 1.0.0 — 2026-09-12

First stable release. **It contains a correctness fix that changes answers**, so
read the first section before upgrading.

### Fixed — timezone correctness in `is_market_open` (breaking behaviour)

`is_market_open` did not convert timezones. It built the session bounds with
`at.replace(hour=10)`, which keeps whatever timezone the caller passed, so the
comparison asked *"is the local wall clock between 10:00 and 15:55"* — in any
zone at all. The same instant returned different answers depending on how it was
written:

| the same moment | 0.1.1 | 1.0.0 |
| --- | --- | --- |
| `12:00 Europe/Vilnius` | True | True |
| `09:00 UTC` | **False** | True |
| `14:30 Asia/Kolkata` | True *by coincidence* | True |

Anyone passing anything other than Lithuanian local time was getting wrong
answers, which is most users of a package published from India and installed
worldwide.

**If you worked around this** by shifting datetimes before calling, remove the
workaround — it will now double-count.

`is_market_open` is kept and fixed. It still accepts naive datetimes, interpreted
as venue-local, so 0.x code does not break on import. That interpretation is a
guess; `is_open` refuses instead.

### Added

- **`is_open(at, venue=...)`** — timezone-correct session check. Requires an
  aware datetime and raises on a naive one, with a message saying what to pass.
- **19 European venues**, rules only: Nasdaq Baltic and Nordic, Euronext, Xetra,
  Madrid, Vienna, Warsaw, Prague, Budapest, Athens. Identified by MIC (ISO
  10383) with friendly aliases. Under MiFID II passporting a Lithuanian investor
  can trade any of them, so a Vilnius-only calendar was incomplete for its users.
- **Self-updating holiday data.** A manifest with SHA-256 per file, checked at
  most daily against a published copy. A verified update is cached under
  `~/.cache/aion_lt_calendar/`. **A new holiday no longer needs a release.**
- **`data_status()`** and **`refresh_data()`**, so a caller can tell whether the
  answer is informed. `rule_only: True` means no verified data: weekends and
  computed public holidays still apply, exchange closures are unknown.
- **`is_trading_day`**, **`next_trading_day`**, **`session_bounds`**.
- **Half-day support.** New Year's Eve closes at 12:30 at Nasdaq Baltic.
- `AION_LT_CALENDAR_OFFLINE=1` for air-gapped use; `AION_LT_CALENDAR_URL` to
  self-host the data.

### Changed

- **Exchange holidays are now separate from public holidays.** They overlap and
  are not the same list. Good Friday closes Nasdaq Baltic and is not a Lithuanian
  public holiday; Christmas Eve *is* a statutory holiday and so is a full closure
  rather than an early close. `is_market_open` consults exchange holidays, not
  public ones.
- `is_market_open(market="XETR")` no longer raises. Until 1.0.0 this package
  covered XVIL alone and rejected every other code. Unknown codes still raise,
  and the error now names the alternatives.
- Development status is Production/Stable.
- `tzdata` is a dependency on Windows only, which has no system tz database.

### Unchanged

Lithuanian public holidays are still computed rather than tabulated, still
correct for any year, still offline, still zero-dependency. That property is the
reason this package exists and nothing here weakens it. The new data file carries
only what *cannot* be derived.

---

## 0.1.1

Lithuanian public, bank and market holidays. Computed, bilingual EN/LT.
