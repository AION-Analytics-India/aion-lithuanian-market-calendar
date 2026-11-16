
2026-11-15: review scope: LT-UPDATE and LT-CI: isolated consent, distribution, signed-metadata, scheduler, native validation and runtime boundaries. LT-STORE and LT-VENUE remain separate domains.

2026-11-15: Add optional Lithuanian supervisor, notification and acceptance paths; correct source -> venue map and atomic data generation boundary. No public runtime enabled.

Added checked_session_bounds_utc as an optional strict interface for venue/year coverage; existing functions remain available.

2026-11-15: LT-STORE -> LT-VENUE proof added for exactly three reviewed 2026 MIC mappings in legacy-shaped data. All 16 fallback MICs retain their historical contract. Verification is local or review CI only.

2026-11-16: verified public shared 2026.11.15.1 generation -> cache -> API. LT-STORE rejects reused IDs and reordered generations. LT-PUBLISH replaces tag rebuild with immutable CI archive selection and a separate publisher identity preflight.


2026-11-16: CAL-PUBLIC-DOCS publication evidence added at docs/PUBLICATION_STATUS_20261116.md; current release status in SITE_MAP.md reconciled to live PyPI. Historical release/candidate evidence retained. No runtime component, API, data-flow edge or automatic installer activated.
