"""Blind teacher rating: export shuffled xlsx sheets, import them back to ratings.csv."""
from __future__ import annotations

import math
import random
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from .config import resolve
from .rubric import CRITERIA, RUBRIC_HU
from .scoring import latest_exams
from .util import read_jsonl

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
HU_COLS = {"correctness": "Helyesség (1-5)", "clarity": "Érthetőség (1-5)",
           "distractor_quality": "Disztraktorok (1-5)", "bloom_fit": "Szintillesztés (1-5)"}
WOULD_USE_COL = "Használnám (igen/nem)"
FIXED_COLS = ["Azonosító", "Dokumentum", "Nyelv", "Kért nehézség", "Forrásrészlet", "Kérdés",
              "Válaszlehetőségek", "Megjelölt helyes válasz"]
TAIL_COLS = [*(HU_COLS[c] for c in CRITERIA), WOULD_USE_COL, "Megjegyzés"]
DIFF_HU = {"easy": "könnyű", "medium": "közepes", "hard": "nehéz"}
LANG_HU = {"hu": "magyar", "en": "angol"}

EXCERPT_CHARS = 1600          # one passage per question; the full text is on the "Források" sheet

# --- look -----------------------------------------------------------------------------------------
NAVY, SLATE, AMBER, GREEN = "1F3864", "44546A", "7F6000", "375623"
FONT = "Calibri"
WHITE_BOLD = Font(name=FONT, bold=True, color="FFFFFF", size=10)
HEAD_FILLS = {"info": PatternFill("solid", fgColor=SLATE), "content": PatternFill("solid", fgColor=NAVY),
              "rating": PatternFill("solid", fgColor=AMBER)}
ZEBRA = PatternFill("solid", fgColor="F3F6FB")
INPUT_FILL = PatternFill("solid", fgColor="FFF4D6")
LINE = Side(style="thin", color="D0D7E5")
BOX = Border(left=LINE, right=LINE, top=LINE, bottom=LINE)
SCORE_FILLS = {"low": PatternFill("solid", fgColor="F8CBAD"), "mid": PatternFill("solid", fgColor="FFE699"),
               "high": PatternFill("solid", fgColor="C6E0B4")}
TAB_COLORS = {"Útmutató": NAVY, "Kalibráció": "7030A0", "Értékelés": "BF8F00", "Források": "7F7F7F"}


def _sample(rows: list[dict], n: int, rng: random.Random) -> list[dict]:
    """Round-robin over documents so every document is represented before any repeats."""
    by_doc = defaultdict(list)
    for r in rows:
        by_doc[r["doc_id"]].append(r)
    for v in by_doc.values():
        rng.shuffle(v)
    docs = sorted(by_doc)
    rng.shuffle(docs)
    out = []
    while len(out) < n and any(by_doc.values()):
        for d in docs:
            if by_doc[d] and len(out) < n:
                out.append(by_doc[d].pop())
    return out


# --- source passage ------------------------------------------------------------------------------
# The retrieved chunk can be a few words long (E0, B-doc), so the passage is picked from the full
# document instead, the same way for every arm: the window of sentences that shares the most rare
# words with the stem and *all* options (not only the key, so a wrong key is still checkable).

_WORD = re.compile(r"\w+", re.UNICODE)
_SENT = re.compile(r"(?<=[.!?…])\s+|\n+")


def _stems(text: str) -> list[str]:
    # 5-letter prefixes are a cheap stand-in for stemming Hungarian suffixes.
    return [w.lower()[:5] for w in _WORD.findall(text or "") if len(w) >= 4 or w.isdigit()]


def _passage(doc: str, query_weights: dict[str, float], budget: int = EXCERPT_CHARS) -> str:
    doc = (doc or "").strip()
    if len(doc) <= budget:
        return doc
    sents = [s.strip() for s in _SENT.split(doc) if s and s.strip()]
    if not sents:
        return doc[:budget] + " …"
    sets = [set(_stems(s)) for s in sents]
    df: dict[str, int] = defaultdict(int)
    for s in sets:
        for w in s:
            df[w] += 1
    n = len(sents)
    score = [sum(wt * math.log(1 + n / df[w]) for w, wt in query_weights.items() if w in s) for s in sets]
    best, best_i, best_j = -1.0, 0, 1
    for i in range(n):
        total, length, j = 0.0, 0, i
        while j < n and (j == i or length + len(sents[j]) + 1 <= budget):
            total += score[j]
            length += len(sents[j]) + 1
            j += 1
        if total > best:
            best, best_i, best_j = total, i, j
    text = " ".join(sents[best_i:best_j])
    if len(text) > budget:                      # a single over-long "sentence"
        text = text[:budget].rsplit(" ", 1)[0]
    return ("… " if best_i > 0 else "") + text + (" …" if best_j < n else "")


def excerpt_for(q: dict, doc: str) -> str:
    weights: dict[str, float] = defaultdict(float)
    for w in _stems(q.get("text", "")):
        weights[w] = 2.0
    for o in q.get("options", []):
        for w in _stems(o.get("text", "")):
            weights[w] = max(weights[w], 1.0)
    return _passage(doc, dict(weights))


def _excerpt(q: dict, exams: dict) -> str:
    ex = exams.get((q["doc_id"], q["seed"])) or {}
    return excerpt_for(q, ex.get("doc_text") or ex.get("context_text") or "")


# --- export --------------------------------------------------------------------------------------

# Placeholder text from Bifrost's JSON example (services/bifrost/prompts.py). A question that echoes it
# is a format failure the automatic metrics already count; rating it only costs the teachers time and
# inflates judge-teacher agreement (everyone gives it a 1), so it is left out of the sample.
TEMPLATE_ECHOES = ("A pontos és egyértelmű kérdés szövege", "Helyes válasz", "Helytelen válasz")


def _is_template_echo(q: dict) -> bool:
    texts = [q.get("text", "")] + [o.get("text", "") for o in q.get("options", [])]
    return any(t.strip().startswith(p) for t in texts for p in TEMPLATE_ECHOES)


def export_sheets(run_dirs: list[str], out_dir: str, n_per_run: int = 30, n_raters: int = 3,
                  n_calibration: int = 10, seed: int = 7, types: tuple = ("mcq", "tf", "open"),
                  only_docs: list[str] | None = None, judged_only: bool = False) -> Path:
    rng = random.Random(seed)
    out = resolve(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    items, calib, docs = [], [], {}
    base, extra = divmod(max(0, n_calibration), max(1, len(run_dirs)))
    for k, rd in enumerate(run_dirs):
        rd = resolve(rd)
        qs = [q for q in read_jsonl(rd / "questions.jsonl") if q.get("type") in types
              and (not only_docs or q["doc_id"] in only_docs)
              # judge-teacher agreement needs a judge score for every rated item
              and (not judged_only or q.get("judge_correctness") is not None)]
        echoes = [q for q in qs if _is_template_echo(q)]
        if echoes:
            print(f"[rate-export] {rd.name}: skipped {len(echoes)}/{len(qs)} template-echo questions")
            qs = [q for q in qs if not _is_template_echo(q)]
        if not qs:
            raise ValueError(f"{rd}: no scored questions (run `score` first)")
        exams = {(e["doc_id"], e["seed"]): e for e in latest_exams(read_jsonl(rd / "exams.jsonl"))}
        picked = _sample(qs, n_per_run, rng)
        if len(picked) < n_per_run:
            print(f"[rate-export] WARNING: {rd.name} has only {len(picked)} questions")
        rest = [q for q in qs if q["uid"] not in {p["uid"] for p in picked}]
        cal = _sample(rest, base + (1 if k < extra else 0), rng)
        for target, chosen in ((items, picked), (calib, cal)):
            for q in chosen:
                target.append({**q, "_excerpt": _excerpt(q, exams)})
                ex = exams.get((q["doc_id"], q["seed"])) or {}
                docs.setdefault(q["doc_id"], ex.get("doc_text") or "")
    rng.shuffle(items)
    rng.shuffle(calib)
    for i, q in enumerate(items, 1):
        q["item_id"] = f"Q{i:03d}"
    for i, q in enumerate(calib, 1):
        q["item_id"] = f"K{i:02d}"

    key = pd.DataFrame([{"item_id": q["item_id"], "uid": q["uid"], "arm": q["arm"], "run_id": q["run_id"],
                         "generator": q.get("model_used"),   # arms share names across models
                         "doc_id": q["doc_id"], "calibration": q["item_id"].startswith("K")}
                        for q in calib + items])
    key.to_csv(out / "rating_key.csv", index=False)

    for r in range(n_raters):
        rater = f"rater_{chr(ord('A') + r)}"
        order = items[:]
        random.Random(seed * 100 + r).shuffle(order)   # different order per rater
        write_workbook(out / f"{rater}.xlsx", rater, calib, order, docs)
    print(f"[rate-export] {len(items)} items (+{len(calib)} calibration) x {n_raters} raters -> {out}\n"
          f"             keep rating_key.csv away from the raters.")
    return out


# --- workbook ------------------------------------------------------------------------------------

RUBRIC_TITLES = {"correctness": "Helyesség", "clarity": "Érthetőség", "distractor_quality": "Disztraktorok",
                 "bloom_fit": "Szintillesztés", "would_use": "Használnám"}
_RUBRIC_RE = re.compile(r"^[^:]+:\s*(?P<what>.*?)\s*1 = (?P<s1>.*?);\s*3 = (?P<s3>.*?);\s*5 = (?P<s5>.*?)\.\s*(?P<note>.*)$")


def _rubric_parts(crit: str) -> dict:
    """Split a rubric line into what it checks and the 1/3/5 anchors (same text as rubric.py)."""
    m = _RUBRIC_RE.match(RUBRIC_HU[crit])
    if not m:
        return {"what": RUBRIC_HU[crit], "s1": "", "s3": "", "s5": ""}
    what = (m["what"] + (" " + m["note"] if m["note"] else "")).strip()
    return {"what": what[:1].upper() + what[1:], "s1": m["s1"], "s3": m["s3"], "s5": m["s5"]}


def _cell(ws, row, col, value=None, *, font=None, fill=None, align=None, border=None, merge_to=None):
    if merge_to:
        ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=merge_to)
    c = ws.cell(row=row, column=col, value=value)
    c.font = font or Font(name=FONT, size=10)
    c.alignment = align or Alignment(wrap_text=True, vertical="top")
    if fill:
        for k in range(col, (merge_to or col) + 1):
            ws.cell(row=row, column=k).fill = fill
    if border:
        for k in range(col, (merge_to or col) + 1):
            ws.cell(row=row, column=k).border = border
    return c


def _lines(text: str, width_chars: float) -> int:
    return sum(max(1, math.ceil(len(p) / max(1.0, width_chars))) for p in str(text or "").split("\n"))


def _write_guide(ws, rater: str, n_calib: int, n_items: int, first_score: int) -> None:
    ws.sheet_view.showGridLines = False
    widths = {"A": 6, "B": 22, "C": 52, "D": 30, "E": 30, "F": 30}
    for k, w in widths.items():
        ws.column_dimensions[k].width = w
    text_width = sum(widths.values()) * 1.05
    letter = rater.replace("rater_", "")
    minutes = round((n_calib + n_items) * 1.5 / 15) * 15
    row = 1

    _cell(ws, row, 1, "Mimir – oktatói értékelőlap", merge_to=6, fill=HEAD_FILLS["content"],
          font=Font(name=FONT, bold=True, size=20, color="FFFFFF"),
          align=Alignment(vertical="center", indent=1))
    ws.row_dimensions[row].height = 40
    row += 1
    _cell(ws, row, 1, f"TDK-kutatás  ·  „{letter}” értékelő  ·  {n_calib} kalibrációs + {n_items} értékelendő kérdés  ·  "
                      f"becsült idő: kb. {minutes // 60} óra {minutes % 60} perc",
          merge_to=6, fill=PatternFill("solid", fgColor="DCE6F2"),
          font=Font(name=FONT, size=11, color=NAVY), align=Alignment(vertical="center", indent=1))
    ws.row_dimensions[row].height = 24
    row += 2

    def para(text, size=11, height=None):
        nonlocal row
        _cell(ws, row, 1, text, merge_to=6, font=Font(name=FONT, size=size))
        ws.row_dimensions[row].height = height or 15.5 * _lines(text, text_width)
        row += 1

    def heading(text):
        nonlocal row
        row += 1
        bottom = Border(bottom=Side(style="medium", color=NAVY))
        _cell(ws, row, 1, text, merge_to=6, border=bottom, font=Font(name=FONT, bold=True, size=13, color=NAVY),
              align=Alignment(vertical="bottom"))
        ws.row_dimensions[row].height = 24
        row += 1

    def item(mark, text):
        nonlocal row
        _cell(ws, row, 1, mark, font=Font(name=FONT, bold=True, size=11, color=NAVY),
              align=Alignment(horizontal="right", vertical="top"))
        _cell(ws, row, 2, text, merge_to=6, font=Font(name=FONT, size=11))
        ws.row_dimensions[row].height = 15.5 * _lines(text, text_width - 6) + 3
        row += 1

    para("Köszönjük, hogy vállalta az értékelést! A Mimir rendszer tananyagokból automatikusan készít "
         "feleletválasztós vizsgakérdéseket. A kérdések minőségét egy nyelvi modell („bíró”) is pontozza; az Ön "
         "értékelése azt mutatja meg, mennyire egyezik a gépi pontozás a szakértői megítéléssel.")

    heading("Haladás")
    score_cols = [ws.cell(row=1, column=first_score + j).column_letter for j in range(len(CRITERIA) + 1)]
    for sheet, n in (("Kalibráció", n_calib), ("Értékelés", n_items)):
        if not n:
            continue
        rng = lambda col: f"'{sheet}'!${col}$2:${col}${n + 1}"   # noqa: E731
        formula = "=SUMPRODUCT(" + "*".join(f"({rng(c)}<>\"\")" for c in score_cols) + ")"
        _cell(ws, row, 2, sheet, font=Font(name=FONT, bold=True, size=11))
        done = _cell(ws, row, 3, formula, font=Font(name=FONT, bold=True, size=11, color=NAVY),
                     align=Alignment(horizontal="left", vertical="top"))
        done.number_format = f'0" / {n} kérdés kész"'
        ws.conditional_formatting.add(done.coordinate, CellIsRule(operator="equal", formula=[str(n)],
                                                                  fill=SCORE_FILLS["high"]))
        row += 1
    para("Egy kérdés akkor számít késznek, ha mind a négy pontszám és a „Használnám” mező ki van töltve.", size=10)

    heading("A feladat")
    item("1.", f"Először a „Kalibráció” lap {n_calib} kérdését pontozza. Ezeket minden értékelő ugyanebben a "
               "sorrendben kapja meg, így ezeken mérjük, mennyire egyezik az értékelők skálahasználata. Nem kell "
               "külön visszaküldeni, egyeztetni sem kell: folytassa az „Értékelés” lappal.")
    item("2.", f"Ezután az „Értékelés” lap {n_items} kérdését pontozza, kérjük, önállóan, a többi értékelővel való "
               "egyeztetés nélkül.")
    item("3.", "Minden kérdést a sorában lévő „Forrásrészlet” alapján értékeljen: a kérdésnek és a megjelölt válasznak "
               "ebből a tananyagból kell következnie. Ha a részlet nem elég (például annak ellenőrzéséhez, hogy más "
               "válasz nem helyes-e), a teljes szöveg a „Források” lapon található (Ctrl+F a dokumentum nevére).")
    item("4.", "A sárga cellákba írjon: a négy szempontra 1–5 közötti egész számot, a „Használnám” oszlopba igen/nem "
               "értéket. Mindkettő legördülő listából is választható, és a cellára kattintva megjelenik a skála "
               "rövid leírása. A „Megjegyzés” nem kötelező.")

    heading("Tudnivalók")
    for text in [
        "A kérdéseket különböző módszerek készítették. A lap nem jelöli, melyik kérdés melyik módszertől származik, "
        "a sorrend véletlenszerű; kérjük, minden kérdést önmagában ítéljen meg.",
        "A „Kért nehézség” a kérdés készítésekor kért szint; a Szintillesztés ehhez viszonyít.",
        "A „Megjelölt helyes válasz” az, amelyet a rendszer helyesnek jelölt (a válaszlehetőségek között zölddel "
        "kiemelve). A Helyesség azt méri, hogy ez valóban helyes-e, és egyedül helyes-e.",
        "Előfordulhatnak hibás formájú kérdések (például nincs megjelölt helyes válasz). Ezeket is kérjük pontozni; "
        "a hibás forma alacsony pontot érdemel.",
        "A kérdések nagyjából fele angol nyelvű, angol tankönyvi (OpenStax) forrásból; ezeket ugyanígy kérjük "
        "értékelni.",
        "A lap részletekben is kitölthető, a fájl közben menthető.",
        "Kérjük, ne módosítsa a lapok nevét, az oszlopok sorrendjét és az „Azonosító” oszlopot, mert a kiértékelés "
        "ezek alapján olvassa vissza a pontszámokat.",
    ]:
        item("•", text)

    heading("Pontozási útmutató")
    para("A szempontok megegyeznek azokkal, amelyek alapján a gépi bíró pontoz (a bíró ugyanezt a szöveget "
         "angolul kapja).", size=10)
    head = ["Szempont", "Mit vizsgál?", "1 – gyenge", "3 – közepes", "5 – kiváló"]
    fills = [HEAD_FILLS["content"]] * 2 + [PatternFill("solid", fgColor=c) for c in ("C55A11", "BF8F00", GREEN)]
    for j, (h, f) in enumerate(zip(head, fills)):
        _cell(ws, row, 2 + j, h, fill=f, border=BOX, font=WHITE_BOLD, align=Alignment(vertical="center", indent=1))
    ws.row_dimensions[row].height = 22
    row += 1
    for k, crit in enumerate(CRITERIA):
        p = _rubric_parts(crit)
        stripe = ZEBRA if k % 2 else None
        vals = [RUBRIC_TITLES[crit], p["what"], p["s1"], p["s3"], p["s5"]]
        for j, v in enumerate(vals):
            _cell(ws, row, 2 + j, v, fill=stripe, border=BOX,
                  font=Font(name=FONT, size=10, bold=(j == 0), color=NAVY if j == 0 else "000000"),
                  align=Alignment(wrap_text=True, vertical="top", indent=1 if j == 0 else 0))
        ws.row_dimensions[row].height = 14 * max(_lines(p["what"], 50), _lines(p["s1"], 28),
                                                 _lines(p["s3"], 28), _lines(p["s5"], 28)) + 6
        row += 1
    wu = RUBRIC_HU["would_use"]
    _cell(ws, row, 2, RUBRIC_TITLES["would_use"], border=BOX, font=Font(name=FONT, size=10, bold=True, color=NAVY),
          align=Alignment(vertical="top", indent=1))
    _cell(ws, row, 3, wu.replace(" (igen/nem)", ""), border=BOX)
    _cell(ws, row, 4, "igen / nem", merge_to=6, border=BOX, font=Font(name=FONT, size=10, italic=True),
          align=Alignment(horizontal="center", vertical="top"))
    ws.row_dimensions[row].height = 14 * _lines(wu, 50) + 6

    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


def write_workbook(path: Path, rater: str, calib: list[dict], items: list[dict],
                   docs: dict[str, str] | None = None) -> None:
    wb = Workbook()
    wb.properties.title = "Mimir – oktatói értékelőlap"
    wb.properties.creator = "Mimir TDK"
    first_score = len(FIXED_COLS) + 1
    guide = wb.active
    guide.title = "Útmutató"
    _write_guide(guide, rater, len(calib), len(items), first_score)
    if calib:
        _fill_sheet(wb.create_sheet("Kalibráció"), calib, rater)
    _fill_sheet(wb.create_sheet("Értékelés"), items, rater)
    if docs:
        _write_sources(wb.create_sheet("Források"), docs)
    for ws in wb.worksheets:
        ws.sheet_properties.tabColor = TAB_COLORS.get(ws.title)
    wb.active = 0
    wb.calculation.fullCalcOnLoad = True     # progress counters on the guide
    wb.save(path)


_write_workbook = write_workbook            # old name


def _options(q: dict) -> tuple[CellRichText | str, str, str]:
    """Options as rich text with the marked key in bold green; also the key letter(s) and plain text."""
    opts = (q.get("options") or [])[:len(LETTERS)]
    if q.get("type") == "open":
        return "(kifejtős kérdés)", str(q.get("key", "")), "(kifejtős kérdés)"
    correct = [LETTERS[i] for i, o in enumerate(opts) if o.get("correct")]
    normal = InlineFont(rFont=FONT, sz=10)
    key = InlineFont(rFont=FONT, sz=10, b=True, color=GREEN)
    blocks, plain = [], []
    for i, o in enumerate(opts):
        line = f"{LETTERS[i]})  {o.get('text', '')}" + ("\n" if i < len(opts) - 1 else "")
        blocks.append(TextBlock(key if o.get("correct") else normal, line))
        plain.append(line)
    return CellRichText(blocks), (", ".join(correct) if correct else "(nincs megjelölve)"), "".join(plain)


def _fill_sheet(ws, items: list[dict], rater: str = "") -> None:
    cols = FIXED_COLS + TAIL_COLS
    groups = ["info"] * 4 + ["content"] * 4 + ["rating"] * len(TAIL_COLS)
    widths = [9, 16, 8, 10, 70, 40, 52, 11] + [11] * len(CRITERIA) + [11, 28]
    ws.append(cols)
    for c, g in zip(ws[1], groups):
        c.font = WHITE_BOLD
        c.fill = HEAD_FILLS[g]
        c.border = Border(left=Side(style="thin", color="FFFFFF"), right=Side(style="thin", color="FFFFFF"))
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    ws.row_dimensions[1].height = 34
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

    first_score = len(FIXED_COLS) + 1
    n_scores = len(CRITERIA) + 1                       # four 1-5 scores + would-use
    for k, q in enumerate(items):
        rich, correct, plain = _options(q)
        lang = LANG_HU.get(q.get("language") or q["doc_id"][:2], q.get("language"))
        values = [q["item_id"], q["doc_id"], lang, DIFF_HU.get(q.get("difficulty"), q.get("difficulty")),
                  q["_excerpt"], q.get("text", ""), rich, correct]
        ws.append(values + [None] * len(TAIL_COLS))
        r = ws.max_row
        stripe = ZEBRA if k % 2 else None
        for c in ws[r]:
            c.border = BOX
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.font = Font(name=FONT, size=10)
            if c.column >= first_score and c.column < first_score + n_scores + 1:
                c.fill = INPUT_FILL
            elif stripe:
                c.fill = stripe
        ws.cell(row=r, column=1).font = Font(name=FONT, size=10, bold=True, color=NAVY)
        ws.cell(row=r, column=2).font = Font(name=FONT, size=9, color="595959")
        for col in (3, 4):
            ws.cell(row=r, column=col).alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
        ws.cell(row=r, column=5).font = Font(name=FONT, size=9, color="404040")
        ws.cell(row=r, column=6).font = Font(name=FONT, size=11, bold=True, color=NAVY)
        ws.cell(row=r, column=8).font = Font(name=FONT, size=14, bold=True, color=GREEN)
        ws.cell(row=r, column=8).alignment = Alignment(horizontal="center", vertical="top")
        for col in range(first_score, first_score + n_scores):
            ws.cell(row=r, column=col).font = Font(name=FONT, size=12, bold=True)
            ws.cell(row=r, column=col).alignment = Alignment(horizontal="center", vertical="center")
        # Row height from the longest wrapped cell (Excel does not auto-fit generated files reliably).
        lines = max(_lines(q["_excerpt"], widths[4] * 1.25) * 12, _lines(q.get("text", ""), widths[5] * 0.95) * 15,
                    _lines(plain, widths[6] * 1.1) * 13.5)
        ws.row_dimensions[r].height = min(409, max(60, lines + 8))

    n = len(items) + 1
    for j, crit in enumerate(CRITERIA):
        col = ws.cell(row=1, column=first_score + j).column_letter
        p = _rubric_parts(crit)
        dv = DataValidation(type="list", formula1='"1,2,3,4,5"', allow_blank=True, showErrorMessage=True,
                            errorTitle="Érvénytelen érték", error="1 és 5 közötti egész számot adjon meg.",
                            showInputMessage=True, promptTitle=RUBRIC_TITLES[crit][:32],
                            prompt=f"1 = {p['s1']}\n3 = {p['s3']}\n5 = {p['s5']}"[:250])
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{n}")
        rng = f"{col}2:{col}{n}"
        ws.conditional_formatting.add(rng, CellIsRule(operator="between", formula=["1", "2"], fill=SCORE_FILLS["low"]))
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=["3"], fill=SCORE_FILLS["mid"]))
        ws.conditional_formatting.add(rng, CellIsRule(operator="between", formula=["4", "5"], fill=SCORE_FILLS["high"]))
    yn = ws.cell(row=1, column=first_score + len(CRITERIA)).column_letter
    dvyn = DataValidation(type="list", formula1='"igen,nem"', allow_blank=True, showErrorMessage=True,
                          errorTitle="Érvénytelen érték", error="igen vagy nem", showInputMessage=True,
                          promptTitle="Használnám", prompt="Betenné egy valódi dolgozatba legfeljebb apró javítással?")
    ws.add_data_validation(dvyn)
    dvyn.add(f"{yn}2:{yn}{n}")
    ws.conditional_formatting.add(f"{yn}2:{yn}{n}", FormulaRule(formula=[f'LOWER({yn}2)="igen"'], fill=SCORE_FILLS["high"]))
    ws.conditional_formatting.add(f"{yn}2:{yn}{n}", FormulaRule(formula=[f'LOWER({yn}2)="nem"'], fill=SCORE_FILLS["low"]))

    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=len(cols)).column_letter}{n}"
    ws.sheet_view.zoomScale = 90
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins.left = ws.page_margins.right = 0.4
    ws.page_margins.top = ws.page_margins.bottom = 0.6
    ws.print_title_rows = "1:1"
    ws.oddHeader.left.text = "Mimir – oktatói értékelés"
    ws.oddHeader.right.text = f"Értékelő: {rater.replace('rater_', '')}" if rater else ""
    ws.oddFooter.center.text = "&A  ·  &P / &N"


def _write_sources(ws, docs: dict[str, str]) -> None:
    """Full source texts, one paragraph per row (an Excel cell holds at most 32,767 characters)."""
    ws.append(["Dokumentum", "Bekezdés", "Szöveg"])
    for c in ws[1]:
        c.font = WHITE_BOLD
        c.fill = HEAD_FILLS["content"]
        c.alignment = Alignment(vertical="center", horizontal="center")
    ws.row_dimensions[1].height = 24
    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 10
    ws.column_dimensions["C"].width = 130
    band = PatternFill("solid", fgColor="DCE6F2")
    for doc_id in sorted(docs):
        ws.append([doc_id, None, f"{doc_id}  ({LANG_HU.get(doc_id[:2], '')}, {len(docs[doc_id] or ''):,} karakter)"
                   .replace(",", " ")])
        r = ws.max_row
        for c in ws[r]:
            c.fill = band
            c.font = Font(name=FONT, size=11, bold=True, color=NAVY)
        ws.row_dimensions[r].height = 22
        paras = [p.strip() for p in re.split(r"\n\s*\n|\n", docs[doc_id] or "") if p.strip()]
        for i, p in enumerate(paras, 1):
            for k in range(0, len(p), 30000):
                ws.append([doc_id, i, p[k:k + 30000]])
                r = ws.max_row
                ws.cell(row=r, column=1).font = Font(name=FONT, size=8, color="A6A6A6")
                ws.cell(row=r, column=2).font = Font(name=FONT, size=9, color="808080")
                ws.cell(row=r, column=2).alignment = Alignment(horizontal="center", vertical="top")
                ws.cell(row=r, column=3).font = Font(name=FONT, size=10)
                ws.cell(row=r, column=3).alignment = Alignment(wrap_text=True, vertical="top")
                ws.row_dimensions[r].height = min(409, 13.5 * _lines(p[k:k + 30000], 150) + 3)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:C{ws.max_row}"


# --- import --------------------------------------------------------------------------------------

def import_sheets(sheets: list[str], key_csv: str, out_csv: str) -> Path:
    key = pd.read_csv(resolve(key_csv))
    rows = []
    rev = {v: k for k, v in HU_COLS.items()}
    for s in sheets:
        p = resolve(s)
        wb = load_workbook(p, data_only=True)
        rater = p.stem
        for sheet in ("Kalibráció", "Értékelés"):
            if sheet not in wb.sheetnames:
                continue
            ws = wb[sheet]
            header = [c.value for c in ws[1]]
            for vals in ws.iter_rows(min_row=2, values_only=True):
                rec = dict(zip(header, vals))
                if not rec.get("Azonosító"):
                    continue
                out = {"rater": rater, "item_id": rec["Azonosító"], "sheet": sheet}
                for hu, crit in rev.items():
                    v = rec.get(hu)
                    try:
                        out[f"h_{crit}"] = int(v) if v not in (None, "") else None
                    except (TypeError, ValueError):
                        out[f"h_{crit}"] = None
                wu = str(rec.get(WOULD_USE_COL) or "").strip().lower()
                out["h_would_use"] = True if wu == "igen" else False if wu == "nem" else None
                out["comment"] = rec.get("Megjegyzés")
                rows.append(out)
    df = pd.DataFrame(rows).merge(key, on="item_id", how="left")
    missing = df["uid"].isna().sum()
    if missing:
        print(f"[rate-import] WARNING: {missing} rows have unknown item ids")
    blank = df[[f"h_{c}" for c in ("correctness", "clarity", "bloom_fit")]].isna().all(axis=1).sum()
    out = resolve(out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"[rate-import] {len(df)} ratings from {len(sheets)} sheets ({blank} left blank) -> {out}")
    return out
