# aion-lithuanian-market-calendar

**Lietuvos švenčių, banko ir rinkos darbo dienų kalendorius. Jo niekada nereikia atnaujinti.**

[![PyPI](https://img.shields.io/pypi/v/aion-lithuanian-market-calendar)](https://pypi.org/project/aion-lithuanian-market-calendar/)
[![Python](https://img.shields.io/pypi/pyversions/aion-lithuanian-market-calendar)](https://pypi.org/project/aion-lithuanian-market-calendar/)
[![Licencija: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

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
# Holiday(date=2026-06-24, name_en='Day of Dew and St John (Midsummer)',
#         name_lt='Rasos ir Joninių diena')
```

## Kodėl jo nereikia atnaujinti

Visos Lietuvos švenčių dienos yra **apskaičiuojamos**. Dvylika jų yra fiksuotos
datos. Dvi priklauso nuo Velykų. Dvi yra pirmasis mėnesio sekmadienis.

Todėl ši biblioteka jas apskaičiuoja, o ne saugo datų sąrašą, kuris kasmet
pasensta. Įdiekite vieną kartą ir ji veiks 2027, 2040 ir bet kuriais vėlesniais
metais, **be interneto ryšio ir be jokios priežiūros**.

**Velykos skaičiuojamos pagal Grigaliaus (Vakarų) kalendorių**, nes Lietuva yra
katalikiška šalis ir švenčia Vakarų, o ne stačiatikių Velykas. Suklydus čia,
kasmet nukryptų dvi šventės.

## Šešiolika švenčių dienų

Pavadinimai pateikti pagal **Darbo kodekso 123 straipsnį** („Švenčių dienos"),
vardininko linksniu. 123 straipsnyje yra keturiolika punktų; du iš jų apima po
dvi kalendorines dienas — Velykų sekmadienį kartu su pirmadieniu ir gruodžio 25
kartu su 26 — todėl iš keturiolikos punktų susidaro šešiolika dienų.

| Data | Lietuviškai | English |
|---|---|---|
| Sausio 1 | Naujieji metai | New Year's Day |
| Vasario 16 | Lietuvos valstybės atkūrimo diena | Day of Restoration of the State of Lithuania |
| Kovo 11 | Lietuvos nepriklausomybės atkūrimo diena | Day of Restoration of Independence of Lithuania |
| *kintama* | Šv. Velykos | Easter Sunday |
| *kintama* | Velykų antroji diena | Easter Monday |
| Gegužės 1 | Tarptautinė darbo diena | International Labour Day |
| *pirmasis gegužės sekmadienis* | Motinos diena | Mother's Day |
| *pirmasis birželio sekmadienis* | Tėvo diena | Father's Day |
| Birželio 24 | Rasos ir Joninių diena | Day of Dew and St John (Midsummer) |
| Liepos 6 | Valstybės (Lietuvos karaliaus Mindaugo karūnavimo) ir Tautiškos giesmės diena | Statehood Day and Day of the National Anthem |
| Rugpjūčio 15 | Žolinė (Švč. Mergelės Marijos ėmimo į dangų diena) | Assumption Day |
| Lapkričio 1 | Visų Šventųjų diena | All Saints' Day |
| Lapkričio 2 | Mirusiųjų atminimo (Vėlinių) diena | Day of Remembrance of the Dead (All Souls' Day) |
| Gruodžio 24 | Šv. Kūčios | Christmas Eve |
| Gruodžio 25 | Šv. Kalėdos | Christmas Day |
| Gruodžio 26 | Šv. Kalėdų antroji diena | Second Day of Christmas |

**Šventės neperkeliamos.** Jei šventė sutampa su savaitgaliu, ji į pirmadienį
neperkeliama. Pavyzdžiui, Žolinė 2026 m. rugpjūčio 15 d. yra šeštadienis, o
po jos einantis pirmadienis — įprasta darbo diena.

## Užgavėnės nėra nedarbo diena

Kai kurios Lietuvos kalendorių ir buhalterinės apskaitos svetainės skelbia
**septyniolikos** „nedarbo dienų" sąrašą 2026 metams; papildomas įrašas yra
**Užgavėnės** (2026 m. vasario 17 d.).

Užgavėnių Darbo kodekso 123 straipsnyje nėra. Tai tradicinė šventė prieš
gavėnią ir **įprasta darbo diena**. Laikant ją nedarbo diena, pasislinktų visos
po jos einančios atsiskaitymų ir atlyginimų datos.

Kadangi lyginant šią biblioteką su sieniniu kalendoriumi galėtų pasirodyti, jog
vienos dienos trūksta, Užgavėnės pateikiamos atskirai:

```python
from aion_lithuanian_market_calendar import observances, is_business_day

observances(2026)
# (Observance(date=2026-02-17, name_en='Shrove Tuesday (Carnival)',
#             name_lt='Užgavėnės'),)

is_business_day("2026-02-17")   # True — tai darbo diena
```

`observances()` niekada neveikia `is_business_day`, `is_market_open` ar bet
kurio kito darbo dienų skaičiavimo. Testai tai tikrina kiekvieniems metams nuo
2024 iki 2040.

## Funkcijos

```python
is_business_day(when=None)          # darbo diena bankams ir įstaigoms
is_public_holiday(when=None)        # šventės diena
is_weekend(when=None)               # savaitgalis

next_business_day(after=None)       # kita darbo diena
previous_business_day(before=None)  # ankstesnė darbo diena
business_days_between(start, end)   # darbo dienų skaičius

holidays(year)                      # visos šešiolika
holidays_between(start, end)        # šventės nurodytu laikotarpiu
holiday_on(day)                     # Holiday arba None
observances(year)                   # tradicinės dienos, kurios NĖRA nedarbo dienos
easter_sunday(year)                 # Velykų sekmadienis

is_market_open(at=None, market="XVIL")   # Nasdaq Vilnius
```

Datos priimamos kaip `date`, `datetime`, ISO tekstas arba `None` (šiandien).

## Apimtis

Apima šešiolika **nedarbo** dienų (*šventės*) pagal 123 straipsnį.

Lietuva taip pat turi **atmintinas dienas** ir vėliavos dienas. Jos yra
oficialios, bet lieka darbo dienomis, todėl darbo dienų skaičiavimo nekeičia ir
į šią biblioteką neįtrauktos. Tradicinės šventės taip pat nėra nedarbo dienos;
dažniausiai su jomis supainiojamos Užgavėnės aprašytos aukščiau.

Biržos prekybos valandos yra ta rinkos kalendoriaus dalis, kuri keičiasi ne
pagal taisyklę, o pagal pranešimą. `is_market_open` naudoja įprastas Nasdaq
Vilnius prekybos valandas; jei reikia tikslumo iki minutės, pasitikrinkite
biržoje.

## Patikra

Velykų data patikrinta 2024, 2025, 2026, 2027, 2030 ir 2035 metams. Motinos ir
Tėvo dienos patikrintos, kad visada būtų sekmadienis nuo 2024 iki 2040 metų.
Visas 2026 m. sąrašas ir visi lietuviški pavadinimai įrašyti į testus.

Švenčių sąrašas ir lietuviškos rašybos formos sutikrintos su Darbo kodekso 123
straipsnio tekstu ir atskirai peržiūrėtos gimtakalbio lietuvio 2026 m. rugsėjo
mėn. Ta peržiūra patvirtino tris dalykus, kurie bibliotekoje jau buvo įgyvendinti,
bet iki tol neturėjo šaltinio:

- šešiolikos dienų sąrašas yra **išsamus**;
- Tėvo diena yra **pirmasis birželio sekmadienis** (2026 m. birželio 7 d.), o ne
  birželio 1 d., kaip teigė vienas šaltinis — 2026 m. birželio 1 d. yra pirmadienis;
- su savaitgaliu sutampanti šventė **į kitą darbo dieną neperkeliama**.

0.1.1 versijoje pagal įstatymo formuluotę pataisyti šeši lietuviški pavadinimai;
svarbiausi — `Visų šventųjų` → **`Visų Šventųjų`** ir liepos 6 d. pavadinimui
grąžinta dalis `ir Tautiškos giesmės diena`. Nė viena data nepasikeitė.

Naudojant teisiniais ar finansiniais tikslais, datas rekomenduojame pasitikrinti
Darbo kodekse. Pastabas ir pataisymus mielai priimame.

## Susiję projektai

- [aion-indian-market-calendar](https://pypi.org/project/aion-indian-market-calendar/) — Indijos rinkos kalendorius
- [aion-indian-market-intelligence](https://pypi.org/project/aion-indian-market-intelligence/)

MIT licencija. Sukūrė **AION Analytics (India)**.
