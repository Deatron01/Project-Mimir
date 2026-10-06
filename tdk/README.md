# TDK dolgozat – MIMIR (ÓE 64. TDK, 2026 ősz)

Fordítás (TeX Live 2022+ vagy Overleaf, pdfLaTeX + Biber):

    latexmk -pdf main.tex
    # vagy: pdflatex main && biber main && pdflatex main && pdflatex main

Szükséges csomagok: babel-hungarian, biblatex + biber, algorithm2e, pgfplots, makecell, float.

- `main.tex` – preambulum, címlap (a `\Kar`, `\SzerzoA`, `\Konzulens` stb. makrókat ki kell tölteni), jegyzékek
- `fejezetek/` – fejezetek és függelékek
- `figures/` – `abra3_mutatok.pdf`: a `tests/eval/report_pilot/pilot` ábrája; `fo_*.pdf`: a fő vizsgálat
  ábrái a `tests/eval/report_main/main` jelentésből
- A fő vizsgálat (2026. szept. 27–28., 14 kar, 9 dokumentum, karonként 6) eredményei a 7.11. szakaszban, a
  hipotézisek értékelése a 7.12. szakaszban; a számok forrása a `tests/eval/report_main/main` jelentés
  (`eredmenyek.md`, `latex/`, `peldak.md`), a megfeleltetés a C. függelék táblázatában
- Piros (`\tbd{}`) mezők: az oktatói értékelés (`rate-import` után) és a fő futás GPU-ja (`run.json`,
  `hardware.gpus`)
