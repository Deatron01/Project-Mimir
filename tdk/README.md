# TDK dolgozat – MIMIR (ÓE 64. TDK, 2026 ősz)

Fordítás (TeX Live / BasicTeX / MiKTeX vagy Overleaf, pdfLaTeX + Biber):

    latexmk -pdf main.tex
    # vagy: pdflatex main && biber main && pdflatex main && pdflatex main

Szükséges csomagok: babel-hungarian, biblatex + biber, algorithm2e, pgfplots, makecell, float.

## Felépítés (főszöveg 47 oldal, teljes PDF 71 oldal; az írási terv: `elemzes/TERV.md`, 3. változat)

A TDK-változat csak a tudományos részt tartalmazza. A rendszerállapotot, a megfelelési megvalósítást és
a fejlesztési döntést is tartalmazó teljes változat a repó gyökerében, a `publikacio/` mappában van.

| Fejezet | Fájl | Tartalom |
| --- | --- | --- |
| Tartalmi összefoglaló | `fejezetek/osszefoglalo.tex` | magyar nyelvű absztrakt |
| Rövidítések és fogalmak | `fejezetek/jelolesek.tex` | egy oldal |
| 1. Bevezetés | `fejezetek/bevezetes.tex` | fejlesztési fázis és cél, P1–P4, RQ1–3, H1–H5, hozzájárulások |
| 2. Szakirodalmi áttekintés | `fejezetek/szakirodalom.tex` | MCQ és Bloom, kérdésgenerálás, LLM-alapok, RAG, felbontás és ellenőrzés, kis modellek, bíró és mérés, magyar nyelv és hazai előzmények, jogi keret (GDPR, MI-rendelet), kutatási rés |
| 3. A javasolt generálási módszer | `fejezetek/modszertan.tex` | tervezési elvek, helyi futtatás, memóriamodell, a generálási módszer lépései |
| 4. Kísérleti módszertan | `fejezetek/kiertekeles.tex` | keretrendszer, konfigurációk, a három vizsgálat, két összevetési szabály, mutatók, bíró, statisztika |
| 5. Eredmények: a módszer komponensei | `fejezetek/eredmenyek.tex` | komponensek, darabolás és robusztusság, ellenőrző, költség (relatív szorzók), a mérés megbízhatósága |
| 6. Eredmények: a generátormodellek | `fejezetek/modellek.tex` | azonos dokumentumokon, szervermodell, a PULI kudarca, erőforrás és GPU-szintek |
| 7. Az eredmények értékelése | `fejezetek/diszkusszio.tex` | hipotézisek, irodalmi összevetés, mikor éri meg, gyakorlati következmények, érvényesség |
| 8. Összefoglalás | `fejezetek/osszefoglalas.tex` | RQ-válaszok, további munka |
| Függelék | `fejezetek/fuggelek_modszer.tex`, `fuggelek_eredmeny.tex`, `fuggelek.tex` | a módszer és az eredmények részletei, a generátor promptja, rubrika, paraméterek (az OTDK kötelező függelékei: `publikacio/otdk_fuggelekek.tex`) |

## Számok, ábrák, diagramok

- `elemzes/elemzes.py` – a dolgozat **összes számának** forrása → `elemzes/szamok.md` és `szamok.json`.
- `elemzes/abrak.py` – az adatábrák (`figures/f1_*.pdf` … `f5_*.pdf`).
- `diagrams/*.mmd` – mermaid-diagramok (`figures/d1_*.pdf` … `d5_*.pdf`); renderelés:
  `npx -p @mermaid-js/mermaid-cli@11.4.2 mmdc -i diagrams/d1_architektura.mmd -o figures/d1_architektura.pdf -c diagrams/config.json -f -b white`
- `elemzes/TERV.md` – az írási terv: történet, szóhasználat, oldalkeret.

Futtatás a repó gyökeréből (Python 3.10+, `pip install -r tests/eval/requirements.txt`):

    python tdk/elemzes/elemzes.py && python tdk/elemzes/abrak.py

## Adatok

A nyers eredmények zipben vannak a tárolóban (a `results*/` mappákat a git kihagyja). Új gépen, a repó
gyökeréből egyszer ki kell bontani őket, mielőtt az `elemzes.py`-t futtatod:

    unzip -q tests/eval/results_fo_2026-10.zip -d tests/eval/                  # -> tests/eval/results/
    unzip -q "tests/new eval/results.zip" -d tmp_qwen && mv tmp_qwen/results tests/eval/results_qwen_2026-09 && rmdir tmp_qwen

| Vizsgálat | Mappa | Generátor | Dokumentum |
| --- | --- | --- | --- |
| pilot (szept. 23.) | `tests/eval/results_pilot` | Qwen2.5-7B | 1 |
| előzetes (szept. 27–28.) | `tests/eval/results_qwen_2026-09` | Qwen2.5-7B + szervermodell | 6 (+3) |
| fő (okt. 7. – nov. 1.) | `tests/eval/results` | PULI-LlumiX 8B, Gemma 3 12B | 30 |

## Nyitott pontok

- **Oktatói értékelés:** folyamatban. Ha elkészül (`rate-import`), az 5.10. szakasz piros helyőrzőjét,
  a H5 sorát a hipotézistáblában és az összefoglalót frissíteni kell.
- **Bírói hibák:** a fő vizsgálatban a bíró hívásainak egy része HTTP 400-zal tért vissza; a sikertelenek
  újrapontozhatók a futtató gépen `python -m mimir_eval score <run>` paranccsal (a sikeres ítéletek a
  bírói gyorsítótárból jönnek, csak a hiányzók futnak újra; a `--skip-scored` kapcsoló ezt kihagyná),
  utána `elemzes.py` újra.
- **E2x:** a Llama-3.1-8B ellenőrző hívásai mindhárom vizsgálatban hibáztak; a konfiguráció csak a
  szabályalapú ellenőrzést mérte.
- **Címlap:** a `main.tex` `\Kar`, `\SzerzoA` … makróit ki kell tölteni.
