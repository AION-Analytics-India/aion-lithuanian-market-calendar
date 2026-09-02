from datetime import date
import pytest
from aion_lithuanian_market_calendar import (
    easter_sunday, holidays, holiday_on, observances, is_public_holiday,
    is_business_day, next_business_day, previous_business_day,
    business_days_between, is_market_open,
)

@pytest.mark.parametrize("year,expected", [
    (2024, "2024-03-31"), (2025, "2025-04-20"), (2026, "2026-04-05"),
    (2027, "2027-03-28"), (2030, "2030-04-21"), (2035, "2035-03-25"),
])
def test_western_easter(year, expected):
    assert easter_sunday(year).isoformat() == expected

def test_2026_has_sixteen_holidays():
    assert len(holidays(2026)) == 16

def test_2026_dates_exact():
    assert [h.date.isoformat() for h in holidays(2026)] == [
        "2026-01-01","2026-02-16","2026-03-11","2026-04-05","2026-04-06",
        "2026-05-01","2026-05-03","2026-06-07","2026-06-24","2026-07-06",
        "2026-08-15","2026-11-01","2026-11-02","2026-12-24","2026-12-25","2026-12-26",
    ]

def test_mothers_and_fathers_day_are_sundays():
    for year in range(2024, 2041):
        for h in holidays(year):
            if h.name_en in {"Mother's Day", "Father's Day"}:
                assert h.date.weekday() == 6, f"{h.name_en} {year} not a Sunday"

def test_names_in_both_languages():
    h = holiday_on(date(2026, 12, 25))
    assert h.name_en == "Christmas Day" and h.name_lt == "Šv. Kalėdos"

def test_business_day_logic():
    assert is_public_holiday("2026-12-25")
    assert not is_business_day("2026-12-25")      # Christmas, Friday
    assert not is_business_day("2026-12-26")      # holiday on a Saturday
    assert is_business_day("2026-12-29")          # Tuesday
    assert next_business_day("2026-12-24").isoformat() == "2026-12-28"  # Mon, after 3 holidays + weekend
    assert previous_business_day("2026-12-25").isoformat() == "2026-12-23"

def test_no_substitute_day_for_weekend_holiday():
    # Assumption Day 2026 falls on a Saturday and is simply absorbed.
    assert holiday_on(date(2026, 8, 15)) is not None
    assert date(2026, 8, 15).weekday() == 5
    assert is_business_day("2026-08-17")          # Monday is a normal working day

def test_works_for_any_future_year_without_update():
    assert len(holidays(2045)) == 16
    assert holiday_on(date(2045, 2, 16)) is not None

def test_business_days_between():
    assert business_days_between("2026-01-01", "2026-01-08") == 4

def test_market_rejects_unknown_venue():
    with pytest.raises(ValueError):
        is_market_open("2026-06-10", market="XETR")

def test_market_closed_on_holiday():
    assert not is_market_open("2026-02-16")
    assert is_market_open("2026-02-17")

def test_holiday_on_accepts_all_date_forms():
    from datetime import datetime
    for value in ("2026-06-24", date(2026, 6, 24), datetime(2026, 6, 24, 11, 30)):
        h = holiday_on(value)
        assert h is not None and h.name_lt == "Rasos ir Joninių diena"


# --- Names, verified against Labour Code article 123 and by a Lithuanian
# --- native speaker (2026-09-02). Each entry here is a name that was wrong in
# --- 0.1.0, so these assertions are regressions, not decoration.
STATUTORY_LT_2026 = {
    "2026-01-01": "Naujieji metai",
    "2026-02-16": "Lietuvos valstybės atkūrimo diena",
    "2026-03-11": "Lietuvos nepriklausomybės atkūrimo diena",
    "2026-04-05": "Šv. Velykos",
    "2026-04-06": "Velykų antroji diena",
    "2026-05-01": "Tarptautinė darbo diena",
    "2026-05-03": "Motinos diena",
    "2026-06-07": "Tėvo diena",
    "2026-06-24": "Rasos ir Joninių diena",
    "2026-07-06": "Valstybės (Lietuvos karaliaus Mindaugo karūnavimo) ir Tautiškos giesmės diena",
    "2026-08-15": "Žolinė (Švč. Mergelės Marijos ėmimo į dangų diena)",
    "2026-11-01": "Visų Šventųjų diena",
    "2026-11-02": "Mirusiųjų atminimo (Vėlinių) diena",
    "2026-12-24": "Šv. Kūčios",
    "2026-12-25": "Šv. Kalėdos",
    "2026-12-26": "Šv. Kalėdų antroji diena",
}


def test_lithuanian_names_match_article_123():
    assert {h.date.isoformat(): h.name_lt for h in holidays(2026)} == STATUTORY_LT_2026


def test_all_saints_day_capitalises_sventuju():
    # Article 123 writes "Visų Šventųjų dieną" with a capital Š; 0.1.0 did not.
    assert holiday_on(date(2026, 11, 1)).name_lt == "Visų Šventųjų diena"


def test_statehood_day_includes_the_anthem():
    # The full statutory name carries "ir Tautiškos giesmės diena"; 0.1.0 dropped it.
    assert "Tautiškos giesmės" in holiday_on(date(2026, 7, 6)).name_lt


def test_uzgavenes_is_an_observance_not_a_holiday():
    """Užgavėnės is printed on Lithuanian calendars but is not in article 123.

    Several commercial "nedarbo dienos" sites list it as a day off. It is not.
    """
    uzgavenes = date(2026, 2, 17)
    assert holiday_on(uzgavenes) is None
    assert not is_public_holiday(uzgavenes)
    assert is_business_day(uzgavenes)          # a Tuesday, and a working day
    assert [o.name_lt for o in observances(2026)] == ["Užgavėnės"]
    assert observances(2026)[0].date == uzgavenes


def test_observances_never_enter_business_day_arithmetic():
    for year in range(2024, 2041):
        for o in observances(year):
            assert holiday_on(o.date) is None, f"{o.name_lt} {year} leaked into holidays()"


def test_uzgavenes_tracks_easter():
    # Shrove Tuesday is Easter minus 47 days, and always a Tuesday.
    from datetime import timedelta
    for year in range(2024, 2041):
        o = observances(year)[0]
        assert o.date == easter_sunday(year) - timedelta(days=47)
        assert o.date.weekday() == 1
