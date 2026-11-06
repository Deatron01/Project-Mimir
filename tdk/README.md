# TDK dolgozat – MIMIR (ÓE 64. TDK, 2026 ősz)

Fordítás (TeX Live 2022+, MiKTeX vagy Overleaf, pdfLaTeX + Biber):

    latexmk -pdf main.tex
    # vagy: pdflatex main && biber main && pdflatex main && pdflatex main

Szükséges csomagok: babel-hungarian, biblatex + biber, algorithm2e, pgfplots, makecell, float.

## Felépítés

A dolgozat a szakirodalom / módszertan / eredmények kb. harmadolását követi
(2026. októberi állapot: 17 / 19 / 21 oldal).

| Fejezet | Fájl | Tartalom |
| --- | --- | --- |
| Tartalmi összefoglaló | `fejezetek/osszefoglalo.tex` | magyar nyelvű absztrakt |
| 1. Bevezetés | `fejezetek/bevezetes.tex` | P1–P4, kutatási kérdések, hipotézisek |
| 2. Szakirodalmi áttekintés | `fejezetek/szakirodalom.tex` | tesztelmélet, AQG, LLM-alapok, feladatfelbontás, RAG, hosszú kontextus, ellenőrzés, kis modellek, LLM-bíró, mérési megbízhatóság, jog, magyar nyelv |
| 3. A rendszer és a generálási módszer | `fejezetek/modszertan.tex` | architektúra, zéró megőrzés, VRAM-becslés, csővezeték |
| 4. Kiértékelési módszertan | `fejezetek/kiertekeles.tex` | a tesztek menete, adatkészlet, a kísérleti karok leírása, mutatók, bíró, statisztika |
| 5. Eredmények | `fejezetek/eredmenyek.tex` | pilot (röviden), fő vizsgálat |
| 6. Az eredmények értékelése | `fejezetek/diszkusszio.tex` | hipotézisek, értelmezés, ajánlás, érvényesség |
| 7. Összefoglalás | `fejezetek/osszefoglalas.tex` | eredmények, további munka |
| Függelék | `fejezetek/fuggelek.tex` | promptok, rubrika, konfigurációk, adatforrások |

- `main.tex` – preambulum, címlap (a `\Kar`, `\SzerzoA`, `\Konzulens` stb. makrókat ki kell tölteni), jegyzékek
- `figures/` – a fő vizsgálat ábrái a `tests/eval/report_main/main` jelentésből (`fo_*.pdf`)
- A számok forrása: `tests/eval/results` (fő vizsgálat), `tests/eval/results_pilot` (pilot) és a
  `tests/eval/report_main/main` jelentés; a megfeleltetés a C. függelék táblázatában

## Nyitott pontok

- **Oktatói értékelés:** nem készült el; a H5 hipotézis ezért „nem dönthető el”. Ha elkészül
  (`rate-import`), a 4.7., 6.1. szakaszt és a hipotézistáblát frissíteni kell.
- **E2x kar:** a fő futásban a `llama3.1:8b` ellenőrző minden hívása hibával tért vissza
  (`blueprint.verifier_skipped`, `llm.errors` az `exams.jsonl`-ben), így a kar csak a szabályalapú
  ellenőrzéseket mérte. A dolgozat ezt így írja le; a független ellenőrző kérdéséhez újra kell futtatni.
- A fő vizsgálat a 39 dokumentumból kilencen futott (karonként hat); a teljes futás a további munka része.
