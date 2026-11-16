"""Regression contract, not certification of non-Baltic holiday correctness.

Reference: 1.2.1 from PyPI + public data 4e398c72846e52b30d89abf1af99a621f7dff275.
Source for Baltic closures: https://www.nasdaqbaltic.com/statistics/en/calendar?holidays=1
"""
import hashlib
import json
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import aion_lithuanian_market_calendar as cal
from aion_lithuanian_market_calendar import store

BALTIC = ("XVIL", "XRIS", "XTAL")
COMMON = "01-01 04-03 04-06 05-01 05-14 06-24 12-24 12-25 12-31".split()
EXTRA = {"XVIL": "02-16 03-11 07-06 11-02", "XRIS": "01-02 05-04 06-22 06-23 11-18",
         "XTAL": "02-24 06-23 08-20"}
FIELDS = ("is_exchange_holiday", "half_day_close", "is_trading_day", "session_bounds_utc",
          "next_trading_day", "is_open", "get_market_phase")
BASELINE = {
    "ASEX": "b037d1ddfc3e8cd9394a686e51216bc9b8f4b448643a077548cf1e93257c85e3",
    "XAMS": "f536a077ed8a5aa481fe996c69ffff512a2dbd589af5af45db3d559acdc9425b",
    "XBRU": "f536a077ed8a5aa481fe996c69ffff512a2dbd589af5af45db3d559acdc9425b",
    "XBUD": "fd646ea435029a836f9f273422db7a0fd7a1eaea898bdd9f68ce0ab436ac59f8",
    "XCSE": "ddf9a67dd0f8453bf69f5d717490ae549a127f02ecbf7fabbb4be7b3d87fb89e",
    "XDUB": "3ac26bc7ad58ea9b22e2e547b5d30213f2adba1857fb072709b6c65b73265802",
    "XETR": "f536a077ed8a5aa481fe996c69ffff512a2dbd589af5af45db3d559acdc9425b",
    "XHEL": "a4fbcf14c04f0d5fc0b197105c1f441e0f545b783d46b435a8395cb943285122",
    "XLIS": "3ac26bc7ad58ea9b22e2e547b5d30213f2adba1857fb072709b6c65b73265802",
    "XMAD": "f536a077ed8a5aa481fe996c69ffff512a2dbd589af5af45db3d559acdc9425b",
    "XMIL": "f536a077ed8a5aa481fe996c69ffff512a2dbd589af5af45db3d559acdc9425b",
    "XPAR": "f536a077ed8a5aa481fe996c69ffff512a2dbd589af5af45db3d559acdc9425b",
    "XPRA": "f4ca79a39780c1df649a2540b184333add7894757b7fc8c6529dd3282120dde1",
    "XSTO": "e6c1a3ec6dd6f8d2345d68655156bacd3c6c15d3c98e5d736526199d4af530af",
    "XWAR": "fd646ea435029a836f9f273422db7a0fd7a1eaea898bdd9f68ce0ab436ac59f8",
    "XWBO": "f536a077ed8a5aa481fe996c69ffff512a2dbd589af5af45db3d559acdc9425b"
}


def encode(x):
    return json.dumps(x, separators=(",", ":"), ensure_ascii=True).encode()


def measurements(verify_baltic):
    counts = Counter()
    digests, baltic, samples = {}, {}, {}
    for mic, venue in sorted(cal.VENUES.items()):
        digest = hashlib.sha256()
        zone = ZoneInfo(venue.timezone)
        closed = {"2026-" + md for md in COMMON + EXTRA.get(mic, "").split()}
        for offset in range(365):
            day = date(2026, 1, 1) + timedelta(days=offset)
            d = day.isoformat()
            holiday = store.is_exchange_holiday(day, mic)
            half = store.half_day_close(day, mic)
            trading = cal.is_trading_day(day, mic)
            bounds = cal.session_bounds_utc(day, mic)
            nxt = cal.next_trading_day(day, mic)
            if mic in BALTIC:
                if verify_baltic:
                    assert holiday == (d in closed), (mic, d, "closure", holiday)
                    assert half is None, (mic, d, "unexpected half-day", half)
                    assert trading == (day.weekday() < 5 and d not in closed), (mic, d)
                    assert (bounds is not None) == trading, (mic, d)
                if holiday:
                    baltic.setdefault(mic, []).append(d)
                if d in ("2026-02-16", "2026-11-18", "2026-12-31"):
                    samples[mic + " " + d] = [holiday, str(half) if half else None, trading,
                        [b.isoformat() for b in bounds] if bounds else None]
                continue
            counts.update(FIELDS[:5])
            # Sample both sides of every regular open/close, historic early close,
            # and configured lunch break. Include midnight and midday on closures.
            times = {venue.opens, venue.closes, time(12, 30)}
            times.update(t for t in (half, venue.break_start, venue.break_end) if t is not None)
            instants = {datetime.combine(day, t, zone).astimezone(timezone.utc)
                        for t in (time(0), time(12))}
            for clock in times:
                edge = datetime.combine(day, clock, zone).astimezone(timezone.utc)
                instants.update(edge + timedelta(microseconds=n) for n in (-1, 0, 1))
            edges = [(moment.isoformat(), cal.is_open(moment, mic), cal.get_market_phase(moment, mic))
                     for moment in sorted(instants)]
            counts.update({name: len(edges) for name in FIELDS[5:]})
            digest.update(encode([d, holiday, half.isoformat() if half else None, trading,
                                  [b.isoformat() for b in bounds] if bounds else None,
                                  nxt.isoformat(), edges]) + b"\n")
        if mic not in BALTIC:
            digests[mic] = digest.hexdigest()
    assert len(digests) == 16
    return dict(non_baltic_sha256=digests, answers=dict(counts), baltic=baltic, samples=samples)


def test_all_2026_dates_and_boundaries(monkeypatch, tmp_path):
    monkeypatch.setenv("AION_LT_CALENDAR_OFFLINE", "1")
    monkeypatch.setattr(store, "CACHE_DIR", tmp_path)
    actual = measurements(True)
    assert actual["non_baltic_sha256"] == BASELINE
    assert sum(map(len, actual["baltic"].values())) == 39
