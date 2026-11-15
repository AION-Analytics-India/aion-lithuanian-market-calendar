# AION Lietuvos finansų rinkų kalendorius

[English](README.md) | [PyPI: 1.2.1](https://pypi.org/project/aion-lithuanian-market-calendar/1.2.1/) | [Produkto puslapis](https://aionanalytics.in/open-source/lithuanian-market-calendar)

Kada Lietuvoje yra darbo diena? Kada biržoje vyksta nepertraukiama prekyba? Kada galimi atsiskaitymai eurais TARGET sistemoje? Ši MIT licencijuota „Python“ biblioteka į šiuos klausimus atsako atskirai. Jai nereikia AION paskyros ar API rakto.

**Paskelbta versija: 1.2.1. Bandomoji versija: 1.3.0, dar neišleista.** Kartu su 1.2.1 pateiktuose duomenyse nurodyta, kad 2026 m. gruodžio 31 d. prekybos sesija baigiama anksčiau. Pagal [oficialų „Nasdaq Baltic“ kalendorių](https://www.nasdaqbaltic.com/statistics/en/calendar?holidays=1) tą dieną Vilniuje, Rygoje ir Taline prekyba nevyksta. Lapkričio 18 d. iš šių trijų biržų nedirba tik Rygos birža. Pataisyti duomenys pateikti peržiūrai; kol jie nepaskelbti, vadovaukitės biržos pranešimais.

## Diegimas

```bash
python -m pip install --upgrade aion-lithuanian-market-calendar
```

Komandą vykdykite toje „Python“ aplinkoje, kurioje veikia jūsų programa. Reikia bent 3.10 versijos; bandomoji matrica apima 3.10-3.14 versijas. Sistemoje „Windows“ taip pat naudojamas paketas `tzdata`.

## Trys skirtingi kalendoriai

Pagal Darbo kodekso 123 straipsnį biblioteka apskaičiuoja 16 švenčių dienų įrašų: dvylika nustatytų datų, Velykų sekmadienį ir pirmadienį pagal Grigaliaus kalendorių, Motinos dieną (pirmasis gegužės sekmadienis) ir Tėvo dieną (pirmasis birželio sekmadienis). Pavadinimai pateikiami lietuviškai ir angliškai. Savaitgalį sutampanti šventė automatiškai neperkeliama į pirmadienį. Gruodžio 24-oji, Kūčios, yra švenčių diena.

Didysis penktadienis gali būti darbo diena Lietuvoje, nors Baltijos biržose prekyba nevyksta ir TARGET sistemoje įprasti atsiskaitymai eurais neatliekami. Vasario 16-oji Lietuvoje yra švenčių diena, tačiau TARGET sistema gali veikti. Tai nėra visų bankų darbo laiko, momentinių mokėjimų ar visų T2S valiutų kalendorius.

```python
from aion_lithuanian_market_calendar import is_business_day, is_settlement_day
assert is_business_day("2026-04-03") and not is_settlement_day("2026-04-03")
assert not is_business_day("2026-02-16") and is_settlement_day("2026-02-16")
```

## Prekybos vietos ir laiko juostos

Aprašytos 19 prekybos vietų. Baltijos šalys: XVIL, XRIS, XTAL. Šiaurės šalys: XSTO, XCSE, XHEL. „Euronext“: XPAR, XAMS, XBRU, XLIS, XMIL, XDUB. Kitos: XETR, XMAD, XWBO, XWAR, XPRA, XBUD, ASEX. [Visų vietų vietos laikas ir sesijų lentelė](README.md#venues-and-time). Vilniuje įprasta nepertraukiamos prekybos sesija prasideda 10:00 vietos laiku: žiemą 08:00 UTC, vasarą 07:00 UTC. Laiko momentas turi turėti laiko juostą. „Europe/Vilnius“ ir „Europe/Dublin“ vasaros laikas nustatomas pagal IANA duomenis.

Prekybos vietos aprašas neįrodo, kad patikrintos visos jos nedarbo dienos. Bandomosios versijos 2026 m. visos dienos uždarymo įrašai sutikrinti tik trims Baltijos biržoms. Kitų rinkų datas patvirtinkite atskirai. 1.2.1 versija nežinomiems metams gali grąžinti įprastą darbo dienos tvarkaraštį. Aukcionai ir prekyba prieš ar po nepertraukiamos sesijos nemodeliuojami.

## Duomenys ir programos naujinimas

Biržos pranešimas → šaltinio ir rinkos patikra → peržiūrėta duomenų versija → SHA-256 kontrolinių sumų patikra → vietinė duomenų kopija. Kontrolinė suma nėra skaitmeninis parašas. Biržų duomenis galima atnaujinti neperdiegiant paketo. Norėdami dirbti be tinklo, prieš paleisdami programą nustatykite `AION_LT_CALENDAR_OFFLINE=1`. Duomenų būseną rodo `data_status()`. Kasdienė oficialių pranešimų paieška dar nėra patvirtinta kaip veikianti visiems šaltiniams.

Įprasta `pip` komanda neįjungia foninės tarnybos. Bandomojoje versijoje naudotojas atskirai pasirenka pranešimus arba patvirtintų suderinamų pataisų diegimą valdomoje aplinkoje. Numatyta naudotojo „systemd“ laikmačio, „launchd“ arba „Windows Task Scheduler“ užduotis. Įprasta programos aplinka nekeičiama. Automatinis programos diegimas naudotojų įrenginiuose **neaktyvuotas**. „Windows 10“, „Windows 11“ x64 darbalaukio ir prisijungimo po tikro paleidimo iš naujo rezultatai nepatvirtinti. [Architektūros schemos ir platformų matrica](README.md) | [Bandomosios versijos instrukcijos](docs/UPDATES.md).

[Darbo kodeksas](https://e-seimas.lrs.lt/portal/legalAct/lt/TAD/10c6bfd07bd511e6a0f68fd135e6f40c/asr) | [ECB kalendorius](https://www.ecb.europa.eu/ecb/contacts/working-hours/html/index.en.html) | [Pranešti apie klaidą](https://github.com/AION-Analytics-India/aion-lithuanian-market-calendar/issues) | [Pakeitimai](CHANGELOG.md) | [Kaip prisidėti](CONTRIBUTING.md) | [MIT licencija](LICENSE).

Nauja lietuviška redakcija laukia gimtakalbio finansų ir teisės terminijos peržiūros.
