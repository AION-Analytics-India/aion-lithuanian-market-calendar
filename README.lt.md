# aion-lithuanian-market-calendar

**Lietuvos švenčių, banko ir rinkos darbo dienų kalendorius. Jo niekada nereikia atnaujinti.**

*In English: [README.md](README.md)*

```bash
pip install aion-lithuanian-market-calendar
```

```python
from aion_lithuanian_market_calendar import is_business_day, next_business_day, holiday_on

is_business_day()                       # ar šiandien darbo diena Lietuvoje
is_business_day("2026-12-25")           # False
next_business_day("2026-12-24")         # date(2026, 12, 28)

holiday_on("2026-06-24")
# Holiday(date=2026-06-24, name_en="St John's Day, Midsummer", name_lt="Rasos ir Joninės")
```

## Kodėl jo nereikia atnaujinti

Visos Lietuvos švenčių dienos yra **apskaičiuojamos**. Dvylika jų yra
fiksuotos datos. Dvi priklauso nuo Velykų. Dvi yra pirmasis mėnesio sekmadienis.

Todėl ši biblioteka jas apskaičiuoja, o ne saugo datų sąrašą, kuris kasmet
pasensta. Įdiekite vieną kartą ir ji veiks 2027, 2040 ir bet kuriais vėlesniais
metais, **be interneto ryšio ir be jokios priežiūros**.

**Velykos skaičiuojamos pagal Grigaliaus (Vakarų) kalendorių**, nes Lietuva yra
katalikiška šalis ir švenčia Vakarų, o ne stačiatikių Velykas. Suklydus čia,
kasmet nukryptų dvi šventės.

## Šešiolika švenčių dienų

| Data | Lietuviškai | English |
|---|---|---|
| Sausio 1 | Naujieji metai | New Year's Day |
| Vasario 16 | Lietuvos valstybės atkūrimo diena | Day of Restoration of the State |
| Kovo 11 | Lietuvos nepriklausomybės atkūrimo diena | Day of Restoration of Independence |
| *kintama* | Šv. Velykos | Easter Sunday |
| *kintama* | Antroji šv. Velykų diena | Easter Monday |
| Gegužės 1 | Tarptautinė darbo diena | International Labour Day |
| *pirmasis gegužės sekmadienis* | Motinos diena | Mother's Day |
| *pirmasis birželio sekmadienis* | Tėvo diena | Father's Day |
| Birželio 24 | Rasos ir Joninės | St John's Day, Midsummer |
| Liepos 6 | Valstybės diena | Statehood Day |
| Rugpjūčio 15 | Žolinė | Assumption Day |
| Lapkričio 1 | Visų šventųjų diena | All Saints' Day |
| Lapkričio 2 | Mirusiųjų atminimo diena, Vėlinės | All Souls' Day |
| Gruodžio 24 | Šv. Kūčios | Christmas Eve |
| Gruodžio 25 | Šv. Kalėdos | Christmas Day |
| Gruodžio 26 | Antroji šv. Kalėdų diena | Second Day of Christmas |

**Šventės neperkeliamos.** Jei šventė sutampa su savaitgaliu, ji į pirmadienį
neperkeliama. Pavyzdžiui, Žolinė 2026 m. rugpjūčio 15 d. yra šeštadienis.

## Funkcijos

```python
is_business_day(when=None)          # darbo diena bankams ir įstaigoms
is_public_holiday(when=None)        # šventės diena
is_weekend(when=None)               # savaitgalis

next_business_day(after=None)       # kita darbo diena
previous_business_day(before=None)  # ankstesnė darbo diena
business_days_between(start, end)   # darbo dienų skaičius

holidays(year)                      # visos šešiolika
holiday_on(day)                     # Holiday arba None
easter_sunday(year)                 # Velykų sekmadienis

is_market_open(at=None, market="XVIL")   # Nasdaq Vilnius
```

Datos priimamos kaip `date`, `datetime`, ISO tekstas arba `None` (šiandien).

## Apimtis

Apima šešiolika **nedarbo** dienų (*šventės*).

Lietuva taip pat turi **atmintinas dienas** ir vėliavos dienas. Jos yra
oficialios, bet lieka darbo dienomis, todėl darbo dienų skaičiavimo nekeičia ir
į šią biblioteką neįtrauktos.

## Patikra

Velykų data patikrinta 2024, 2025, 2026, 2027, 2030 ir 2035 metams. Motinos ir
Tėvo dienos patikrintos, kad visada būtų sekmadienis nuo 2024 iki 2040 metų.
Visas 2026 m. sąrašas įrašytas į testus.

Naudojant teisiniais ar finansiniais tikslais, datas rekomenduojame pasitikrinti
Darbo kodekse. Pastabas ir pataisymus mielai priimame.

MIT licencija. Sukūrė **AION Analytics (India)**.
