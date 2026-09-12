# Changelog

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
