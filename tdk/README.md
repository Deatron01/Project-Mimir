# TDK dolgozat – MIMIR (ÓE 64. TDK, 2026 ősz)

Fordítás (TeX Live 2022+ vagy Overleaf, pdfLaTeX + Biber):

    latexmk -pdf main.tex
    # vagy: pdflatex main && biber main && pdflatex main && pdflatex main

Szükséges csomagok: babel-hungarian, biblatex + biber, algorithm2e, pgfplots, makecell, float.

- `main.tex` – preambulum, címlap (a `\Kar`, `\SzerzoA`, `\Konzulens` stb. makrókat ki kell tölteni), jegyzékek
- `fejezetek/` – fejezetek és függelékek
- `figures/` – a `tests/eval/report_pilot/pilot` ábrái
- Piros (`\tbd{}`) mezők: a 39 dokumentumos fő futás adataira várnak (7.12. szakasz, 7.10. táblázat)
