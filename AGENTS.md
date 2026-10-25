# AGENTS.md - aion-lithuanian-market-calendar

Rules for any automated agent, and any contributor, working in this repository. This is a
public repository: everything here is published.

This is **aion-lithuanian-market-calendar**, an MIT-licensed Python package for Lithuanian public
holidays, TARGET settlement days, and timezone-correct trading sessions for 19 European venues.
It is maintained by AION Analytics. English and Lithuanian are both first-class.

- **Source of truth for structure and dependencies: [`SITE_MAP.md`](SITE_MAP.md).** Read it before
  adding anything.
- Release notes: [`CHANGELOG.md`](CHANGELOG.md). User documentation: [`README.md`](README.md)
  (English and Lithuanian) and [`README.lt.md`](README.lt.md) (Lithuanian).

## Repository Hygiene & Site Maps

1. **The Site Map is Law:** Every product repository must maintain a `SITE_MAP.md` at its root. Before creating a new script, folder, or dependency, you must check the `SITE_MAP.md` to ensure you are not duplicating existing logic or breaking architectural boundaries.
2. **Update on Change:** Any time you add a new script, modify a core dependency, or deprecate a file, you must update the `SITE_MAP.md` in the same commit/session.
3. **No Scattered Debris:** Never create ad-hoc scripts in the root directory. All new scripts must go into the appropriate `scripts/` or `src/` subdirectory.
4. **Cross-Repo Reading:** You may only read files from another AION repo if the dependency is explicitly documented in your repo's `SITE_MAP.md`.

## Rules specific to this package

- **Facts come from primary sources.** Lithuanian holidays from the Labour Code (article 123),
  TARGET closing days from the ECB, venue hours from the venue itself. Cite the source where the
  rule is written. Commercial "nedarbo dienos" websites are not a source: they list Užgavėnės,
  which is a working day.
- **Both languages.** Every user-facing name or text has an English and a Lithuanian form. Write
  Lithuanian with its diacritics. New Lithuanian text is reviewed by a native speaker before a
  release; until then the changelog says it is awaiting review.
- **Refuse rather than guess.** Naive datetimes raise. Phases that no primary source confirms are
  not returned.
- **Data does not change here.** The published data, and the `ingest` tool that edits it, live in
  [aion-market-calendar-data](https://github.com/AION-Analytics-India/aion-market-calendar-data).
  The bundled copy in `src/aion_lithuanian_market_calendar/data/` is the offline fallback. Never
  edit a `manifest.json` by hand, and never put a test date into published data.
- **No network unless a refresh is asked for, and no identifier ever.**
- **Information, not advice.** The package reports when venues trade and settle, nothing more.
- **Releases** go only through the tag-triggered workflow in `.github/workflows/publish.yml`.
  Never upload from a laptop, never force-push, never rewrite published history.
- **Nothing private.** No credentials, no internal paths, no server details, nothing about systems
  outside this repository.

Run the tests offline: `AION_LT_CALENDAR_OFFLINE=1 pytest -q`.
