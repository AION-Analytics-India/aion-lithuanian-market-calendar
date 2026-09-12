"""Trading session rules for European venues.

**Rules only.** A venue entry here says what time the market opens and closes in
its own local time, which days of the week it trades, and whether it breaks for
lunch. It says nothing about holidays, because holidays are the part that changes
by announcement rather than by rule — those live in the holiday store, and for
venues other than Vilnius they are an optional data source (see ``store``).

That split is deliberate and it is the honest one. Session times and weekends are
derivable and will still be right in ten years with no maintenance. A holiday
table is wrong the moment a government declares a day of mourning, and a library
that bundles one silently rots. So the rules ship, the tables update.

**Accuracy caveat, stated plainly.** These are the standard continuous-trading
windows published by each venue. Auction phases, pre-open, post-close and
occasional schedule changes are not modelled, and a venue can change its hours by
announcement. If you are settling money on the answer, confirm against the venue.
``verified_on`` records when each entry was last checked by a human.

All times are local to the venue. Conversion is handled by ``zoneinfo``, so
daylight saving is correct by construction and no UTC offset is ever hardcoded.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time


@dataclass(frozen=True)
class Venue:
    """One trading venue's session rule."""

    mic: str
    name: str
    country: str
    #: IANA zone name. Never a fixed offset -- that is what breaks at DST.
    timezone: str
    opens: time
    closes: time
    #: Midday break, where the venue has one. Empty for most of Europe.
    break_start: time | None = None
    break_end: time | None = None
    #: Weekday numbers the venue trades. Monday is 0, matching date.weekday().
    trading_days: tuple[int, ...] = (0, 1, 2, 3, 4)
    #: When a human last checked this entry against the venue's own published
    #: schedule. An entry nobody has confirmed in two years should be treated as
    #: a guess, which is why the date is here rather than in a changelog.
    verified_on: str = "2026-09-12"
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def trades_on_weekday(self, weekday: int) -> bool:
        return weekday in self.trading_days


#: Venues, by MIC code. MIC (ISO 10383) rather than a friendly name, because a
#: friendly name is ambiguous -- "Milan" has meant three different operators --
#: and a MIC is what every downstream system already uses.
VENUES: dict[str, Venue] = {
    # --- Nasdaq Baltic ----------------------------------------------------
    "XVIL": Venue("XVIL", "Nasdaq Vilnius", "LT", "Europe/Vilnius",
                  time(10, 0), time(15, 55), aliases=("VILNIUS", "NASDAQ_VILNIUS")),
    "XRIS": Venue("XRIS", "Nasdaq Riga", "LV", "Europe/Riga",
                  time(10, 0), time(15, 55), aliases=("RIGA",)),
    "XTAL": Venue("XTAL", "Nasdaq Tallinn", "EE", "Europe/Tallinn",
                  time(10, 0), time(15, 55), aliases=("TALLINN",)),
    # --- Nasdaq Nordic ----------------------------------------------------
    "XSTO": Venue("XSTO", "Nasdaq Stockholm", "SE", "Europe/Stockholm",
                  time(9, 0), time(17, 25), aliases=("STOCKHOLM",)),
    "XCSE": Venue("XCSE", "Nasdaq Copenhagen", "DK", "Europe/Copenhagen",
                  time(9, 0), time(16, 55), aliases=("COPENHAGEN",)),
    "XHEL": Venue("XHEL", "Nasdaq Helsinki", "FI", "Europe/Helsinki",
                  time(10, 0), time(18, 25), aliases=("HELSINKI",)),
    # --- Euronext ---------------------------------------------------------
    "XPAR": Venue("XPAR", "Euronext Paris", "FR", "Europe/Paris",
                  time(9, 0), time(17, 30), aliases=("PARIS", "EURONEXT_PARIS")),
    "XAMS": Venue("XAMS", "Euronext Amsterdam", "NL", "Europe/Amsterdam",
                  time(9, 0), time(17, 30), aliases=("AMSTERDAM",)),
    "XBRU": Venue("XBRU", "Euronext Brussels", "BE", "Europe/Brussels",
                  time(9, 0), time(17, 30), aliases=("BRUSSELS",)),
    "XLIS": Venue("XLIS", "Euronext Lisbon", "PT", "Europe/Lisbon",
                  time(8, 0), time(16, 30), aliases=("LISBON",)),
    "XMIL": Venue("XMIL", "Euronext Milan", "IT", "Europe/Rome",
                  time(9, 0), time(17, 30), aliases=("MILAN", "BORSA_ITALIANA")),
    "XDUB": Venue("XDUB", "Euronext Dublin", "IE", "Europe/Dublin",
                  time(8, 0), time(16, 30), aliases=("DUBLIN",)),
    # --- Deutsche Boerse --------------------------------------------------
    "XETR": Venue("XETR", "Xetra (Deutsche Boerse)", "DE", "Europe/Berlin",
                  time(9, 0), time(17, 30), aliases=("XETRA", "FRANKFURT")),
    # --- Iberia, Alpine, Central and Eastern Europe -----------------------
    "XMAD": Venue("XMAD", "Bolsa de Madrid (BME)", "ES", "Europe/Madrid",
                  time(9, 0), time(17, 30), aliases=("MADRID", "BME")),
    "XWBO": Venue("XWBO", "Wiener Boerse", "AT", "Europe/Vienna",
                  time(9, 0), time(17, 30), aliases=("VIENNA",)),
    "XWAR": Venue("XWAR", "Warsaw Stock Exchange (GPW)", "PL", "Europe/Warsaw",
                  time(9, 0), time(17, 0), aliases=("WARSAW", "GPW")),
    "XPRA": Venue("XPRA", "Prague Stock Exchange", "CZ", "Europe/Prague",
                  time(9, 0), time(16, 20), aliases=("PRAGUE",)),
    "XBUD": Venue("XBUD", "Budapest Stock Exchange", "HU", "Europe/Budapest",
                  time(9, 0), time(17, 0), aliases=("BUDAPEST",)),
    "ASEX": Venue("ASEX", "Athens Stock Exchange", "GR", "Europe/Athens",
                  time(10, 15), time(17, 20), aliases=("ATHENS", "ATHEX")),
}

#: Alias -> MIC, built once. Lets a caller write "XETRA" or "Frankfurt" without
#: the registry carrying duplicate entries that can drift apart.
_ALIASES: dict[str, str] = {}
for _mic, _venue in VENUES.items():
    _ALIASES[_mic.upper()] = _mic
    for _alias in _venue.aliases:
        _ALIASES[_alias.upper()] = _mic


def resolve(market: str) -> Venue:
    """Look up a venue by MIC or alias, case-insensitively.

    Raises with the full list rather than a bare KeyError: a typo in a MIC code
    is the commonest way to use this wrong, and a message that names the
    alternatives costs nothing.
    """
    key = (market or "").strip().upper().replace(" ", "_")
    mic = _ALIASES.get(key)
    if mic is None:
        known = ", ".join(sorted(VENUES))
        raise ValueError(f"unknown venue {market!r}; known MICs: {known}")
    return VENUES[mic]


def venues() -> list[Venue]:
    """Every venue, ordered by MIC."""
    return [VENUES[m] for m in sorted(VENUES)]
