# aion-lithuanian-market-calendar

**Lithuanian public holiday, bank and market calendar. Never needs updating.**
**Lietuvos švenčių, banko ir rinkos darbo dienų kalendorius. Jo niekada nereikia atnaujinti.**

[![PyPI](https://img.shields.io/pypi/v/aion-lithuanian-market-calendar)](https://pypi.org/project/aion-lithuanian-market-calendar/)
[![Downloads](https://static.pepy.tech/badge/aion-lithuanian-market-calendar)](https://pepy.tech/project/aion-lithuanian-market-calendar)
[![Python](https://img.shields.io/pypi/pyversions/aion-lithuanian-market-calendar)](https://pypi.org/project/aion-lithuanian-market-calendar/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**[English](#english)** · **[Lietuviškai](#lietuviškai)**

---

## Lietuviškai

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

Nereikia API rakto. Nereikia interneto ryšio. Nereikia jokių nustatymų. Jokių
priklausomybių.

### Kam ji skirta

Bet kam, kas turi atsakyti į klausimą *„ar ta diena Lietuvoje buvo darbo
diena?"* ir kaskart gauti tą patį atsakymą.

- **Mokėjimai ir atsiskaitymai.** Valiutavimo datos, SEPA terminai, T+2,
  sąskaitų apmokėjimo terminai ir delspinigiai skaičiuojami darbo dienomis.
  Lietuva yra didžiausias elektroninių pinigų ir mokėjimo įstaigų licencijavimo
  centras ES, todėl labai didelė dalis Europos mokėjimų infrastruktūros
  atsiskaito būtent pagal Lietuvos darbo dienų kalendorių.
- **Darbo užmokestis ir personalas.** Darbo laiko apskaita, atostogų kaupimas,
  įspėjimo terminai ir priemokos už darbą švenčių dienomis remiasi *šventėmis*.
  Suklydus dėl liepos 6 d., tai jau ne kosmetinė, o atlyginimo klaida.
- **Rinkos duomenys ir prekyba.** Nasdaq Vilnius sesijų tikrinimas, duomenų
  eilučių derinimas, tarpų aptikimas ir istorinis testavimas, kuris neturi
  palaikyti šventės trūkstamais duomenimis.
- **Planavimas ir SLA.** „Trys darbo dienos" sutartyje, naktinė užduotis, kuri
  neturi pasileisti per šventę, priminimas, kuris turi pasiekti žmogų darbo
  metu.
- **Ataskaitų terminai.** Mokestinės ir priežiūros ataskaitos, kurių terminas
  keliasi, kai jis išpuola ne darbo dieną.

### Kuo ji naudinga

**Ji teisinga be jokios priežiūros.** Visos Lietuvos švenčių dienos yra
apskaičiuojamos: dvylika yra fiksuotos datos, dvi priklauso nuo Velykų, dvi yra
pirmasis mėnesio sekmadienis. Todėl biblioteka jas *apskaičiuoja*, o ne saugo
sąrašą, kuris kasmet gruodį pasensta. Įdiekite vieną kartą ir ji veiks 2027,
2040 ir bet kuriais vėlesniais metais, be interneto ryšio.

Tuo ji skiriasi nuo rinkų, kurių šventės skelbiamos kasmet ir tikrai negali būti
apskaičiuotos — mūsų [Indijos rinkos
kalendorius](https://pypi.org/project/aion-indian-market-calendar/) būtent dėl
to platinamas su duomenų failu. Lietuvai jo nereikia, todėl jo ir nėra.

**Ji nesijungia į internetą.** Jokių tinklo užklausų, todėl ji veikia
izoliuotame atsiskaitymų serveryje ar CI aplinkoje be išorinio ryšio ir negali
sugesti dėl to, kad trečiosios šalies švenčių API neveikia ar apribojo užklausas.

**Ji dvikalbė, todėl tinka rodyti naudotojui.** Kiekviena šventė turi ir
`name_en`, ir `name_lt` pagal Darbo kodekso formuluotę, todėl lietuvis klientas
mato `Rasos ir Joninių diena`, o ne kieno nors susigalvotą vertimą.

**Velykos skaičiuojamos pagal Grigaliaus (Vakarų) kalendorių**, nes Lietuva yra
katalikiška šalis ir švenčia Vakarų, o ne stačiatikių Velykas. Suklydus čia,
kasmet nukryptų dvi šventės — tai dažniausia klaida pačių rašytame Europos
švenčių kode.

**Ji nespėlioja.** Kur įstatymas tyli, biblioteka taisyklės nesugalvoja, o kur
populiarūs kalendoriai nesutampa su įstatymu, ji laikosi įstatymo ir tai
pasako atvirai — žemiau.

### Šešiolika švenčių dienų

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
neperkeliama. Pavyzdžiui, Žolinė 2026 m. rugpjūčio 15 d. yra šeštadienis, o po
jos einantis pirmadienis — įprasta darbo diena.

### Užgavėnės nėra nedarbo diena

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

### Funkcijos

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

```python
from aion_lithuanian_market_calendar import business_days_between, holidays_between

business_days_between("2026-12-20", "2027-01-05")   # 8
[h.name_lt for h in holidays_between("2026-12-01", "2027-01-01")]
# ['Šv. Kūčios', 'Šv. Kalėdos', 'Šv. Kalėdų antroji diena']
```

### Apimtis

Apima šešiolika **nedarbo** dienų (*šventės*) pagal 123 straipsnį.

Lietuva taip pat turi **atmintinas dienas** ir vėliavos dienas. Jos yra
oficialios, bet lieka darbo dienomis, todėl darbo dienų skaičiavimo nekeičia ir
į šią biblioteką neįtrauktos. Tradicinės šventės taip pat nėra nedarbo dienos;
dažniausiai su jomis supainiojamos Užgavėnės aprašytos aukščiau.

Biržos prekybos valandos yra ta rinkos kalendoriaus dalis, kuri keičiasi ne
pagal taisyklę, o pagal pranešimą. `is_market_open` naudoja įprastas Nasdaq
Vilnius prekybos valandas; jei reikia tikslumo iki minutės, pasitikrinkite
biržoje.

Seimo paskelbta vienkartinė gedulo diena pagal apibrėžimą negali būti
apskaičiuota ir į biblioteką neįtraukta. Jei jos reikia, pridėkite ją atskirai,
o ne taisykite skaičiavimą.

### Patikra

Velykų data patikrinta 2024, 2025, 2026, 2027, 2030 ir 2035 metams. Motinos ir
Tėvo dienos patikrintos, kad visada būtų sekmadienis nuo 2024 iki 2040 metų.
Visas 2026 m. sąrašas ir visi lietuviški pavadinimai įrašyti į testus.

Švenčių sąrašas ir lietuviškos rašybos formos sutikrintos su Darbo kodekso 123
straipsnio tekstu ir atskirai peržiūrėtos gimtakalbio lietuvio 2026 m. rugsėjo
mėn. Ta peržiūra patvirtino tris dalykus, kurie bibliotekoje jau buvo
įgyvendinti, bet iki tol neturėjo šaltinio:

- šešiolikos dienų sąrašas yra **išsamus**;
- Tėvo diena yra **pirmasis birželio sekmadienis** (2026 m. birželio 7 d.), o ne
  birželio 1 d., kaip teigė vienas šaltinis — 2026 m. birželio 1 d. yra
  pirmadienis;
- su savaitgaliu sutampanti šventė **į kitą darbo dieną neperkeliama**.

0.1.1 versijoje pagal įstatymo formuluotę pataisyti šeši lietuviški pavadinimai;
svarbiausi — `Visų šventųjų` → **`Visų Šventųjų`** ir liepos 6 d. pavadinimui
grąžinta dalis `ir Tautiškos giesmės diena`. Nė viena data nepasikeitė.

Naudojant teisiniais ar finansiniais tikslais, datas rekomenduojame pasitikrinti
Darbo kodekse. Pastabas ir pataisymus mielai priimame — žr.
[CONTRIBUTING.md](CONTRIBUTING.md).

---

## Related · Susiję projektai

- [aion-indian-market-calendar](https://pypi.org/project/aion-indian-market-calendar/) — the Indian sibling · Indijos rinkos kalendorius
- [aion-indian-market-intelligence](https://pypi.org/project/aion-indian-market-intelligence/)
- Source · Kodas: [github.com/AION-Analytics-India/aion-lithuanian-market-calendar](https://github.com/AION-Analytics-India/aion-lithuanian-market-calendar)

MIT licensed. Built by **AION Analytics (India)**, an independent India-based
firm, not affiliated with Aion Analytics LLC (United States) or AION Labs
(Israel).

MIT licencija. Sukūrė **AION Analytics (India)**.

---

**Ieškome komunikacijos architekto.** Neskaitome CV — skaitome kodą. Iššūkis ir yra paraiška. [Visas iššūkis](https://dashboard.aiondashboard.site/careers).
