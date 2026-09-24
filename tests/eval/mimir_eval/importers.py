"""Build evaluation documents + gold questions from public datasets.

- EduQG (English, OpenStax textbooks, CC BY 4.0): 3,397 expert-written MCQs with the source
  sentences that prove each answer and, for part of them, Bloom levels.
  https://github.com/hadifar/question-generation  (raw_data/qg_{train,valid}_v0.json)
- MILQA (Hungarian, Wikipedia, CC BY-SA 4.0): 23,700 questions over 142 articles, SQuAD 2.0
  style with short and long answer spans. https://huggingface.co/datasets/SzegedAI/MILQA

Each importer writes dataset/docs/<name>/<doc_id>.txt, dataset/gold/<doc_id>.json and
dataset/manifest_<name>.yaml; add that file to `include:` in dataset/manifest.yaml.
Documents come in three length bands so latency, coverage and chunking effects can be shown:
short (<= 6,000 chars, ~1-2 pages), medium (6,000-25,000), long (whole chapter/article, <= 90,000).
"""
from __future__ import annotations

import json
import random
import re
import time
import unicodedata
from pathlib import Path

import httpx
import yaml

from .config import EVAL_ROOT, resolve
from .util import Haystack

EDUQG_URLS = {
    "valid": "https://raw.githubusercontent.com/hadifar/question-generation/main/raw_data/qg_valid_v0.json",
    "train": "https://raw.githubusercontent.com/hadifar/question-generation/main/raw_data/qg_train_v0.json",
}
MILQA_URL = "https://huggingface.co/datasets/SzegedAI/MILQA/resolve/main/test.MILQA-2023-03-27.squad.s.json"

EDUQG_SUBJECT = {
    "biology": "life_sciences", "anatomy_and_physiology": "life_sciences", "microbiology": "life_sciences",
    "introduction_to_sociology": "humanities", "psychology": "humanities", "u.s._history": "humanities",
    "american_government": "humanities", "business_law_i_essentials": "law", "business_ethics": "law",
    "introduction_to_intellectual_property": "law",
    "principles_of_accounting,_volume_1:_financial_accounting": "economics",
    "principles_of_accounting,_volume_2:_managerial_accounting": "economics",
}
BANDS = {"short": (800, 6000), "medium": (6000, 25000), "long": (25000, 90000)}
DIFFICULTIES = ["easy", "medium", "hard"]
BLOOM_EDUQG = {"1": "Emlékezés", "2": "Megértés", "3": "Alkalmazás", "4": "Elemzés", "5": "Értékelés",
               "6": "Alkotás"}


def load_json_source(src: str) -> object:
    """Local path or URL. Downloads are cached in dataset/raw/ so a failed import can be rerun
    (and inspected) without downloading again."""
    if src.startswith("http"):
        cache = EVAL_ROOT / "dataset" / "raw" / src.rstrip("/").split("/")[-1]
        if not cache.exists():
            print(f"[import] downloading {src}")
            with httpx.Client(timeout=120, follow_redirects=True) as c:
                r = c.get(src)
                r.raise_for_status()
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(r.content)
        else:
            print(f"[import] using cached {cache}")
        return json.loads(cache.read_text(encoding="utf-8"))
    return json.loads(resolve(src, Path.cwd()).read_text(encoding="utf-8"))


def detok(s: str) -> str:
    """EduQG evidence is tokenised ('the skin ) .'); undo the extra spaces."""
    s = re.sub(r"\s+([.,;:!?)\]’”%])", r"\1", s)
    s = re.sub(r"([(\[“‘$])\s+", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def split_sentences(s: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÖŐÚÜŰ0-9“\"])", detok(s))
    return [p for p in parts if len(p) > 15]


def evidence_paragraphs(paras: list[str], gold: list[dict]) -> list[tuple[dict, int, int]]:
    """For each gold question, the paragraph span [first, last] that holds all its evidence."""
    hs = [Haystack(p) for p in paras]
    pairs = [Haystack(paras[i] + " " + paras[i + 1]) for i in range(len(paras) - 1)]
    out = []
    for g in gold:
        spans = []
        for e in g["evidence"]:
            hit = next(((i, i) for i, h in enumerate(hs) if h.contains(e)), None) or \
                  next(((i, i + 1) for i, h in enumerate(pairs) if h.contains(e)), None)
            if hit is None:
                break
            spans.append(hit)
        else:
            if spans:
                out.append((g, min(a for a, _ in spans), max(b for _, b in spans)))
    return out


def best_window(paras: list[str], lo: int, hi: int, gold: list[dict]) -> tuple[str, list[dict]]:
    """Consecutive paragraphs with lo <= length <= hi that contain the most gold evidence."""
    located = evidence_paragraphs(paras, gold)
    best, best_q = (0, 0), []
    best_len = 0
    for i in range(len(paras)):
        size = -2
        for j in range(i, len(paras)):
            size += len(paras[j]) + 2
            if size > hi:
                break
            if size >= lo:
                qs = [g for g, a, b in located if a >= i and b <= j]
                if len(qs) > len(best_q) or (len(qs) == len(best_q) and size > best_len):
                    best, best_q, best_len = (i, j), qs, size
    if not best_q and best_len == 0:
        return "", []
    return "\n\n".join(paras[best[0]:best[1] + 1]), best_q


def write_dataset(name: str, docs: list[dict], license_: str, public: bool, source_note: str) -> Path:
    ds_dir = EVAL_ROOT / "dataset"
    (ds_dir / "docs" / name).mkdir(parents=True, exist_ok=True)
    (ds_dir / "gold").mkdir(parents=True, exist_ok=True)
    entries = []
    for d in docs:
        (ds_dir / "docs" / name / f"{d['id']}.txt").write_text(d["text"], encoding="utf-8")
        gold = {"teszt_metaadatok": {"tema": d["title"], "nehezseg": d["difficulty"], "nyelv": d["language"],
                                     "forras": d["source"]},
                "kerdesek": d["gold"]}
        (ds_dir / "gold" / f"{d['id']}.json").write_text(json.dumps(gold, ensure_ascii=False, indent=2),
                                                         encoding="utf-8")
        entries.append({"id": d["id"], "path": f"docs/{name}/{d['id']}.txt", "language": d["language"],
                        "subject": d["subject"], "difficulty": d["difficulty"], "length": d["band"],
                        "license": license_, "public": public, "gold": f"gold/{d['id']}.json",
                        "title": d["title"], "source": d["source"], "chars": len(d["text"]),
                        "n_gold": len(d["gold"])})
    manifest = ds_dir / f"manifest_{name}.yaml"
    header = f"# Generated by `python -m mimir_eval import {name}`. {source_note}\n"
    manifest.write_text(header + yaml.safe_dump({"documents": entries}, allow_unicode=True, sort_keys=False),
                        encoding="utf-8")
    print(f"[import] {len(entries)} documents -> {manifest}")
    for e in entries:
        print(f"   {e['id']:34s} {e['language']} {e['subject']:13s} {e['length']:6s} {e['difficulty']:6s} "
              f"{e['chars']:6d} chars  {e['n_gold']:2d} gold")
    print(f"[import] add '{manifest.name}' to `include:` in dataset/manifest.yaml")
    return manifest


def _plan(n: int) -> list[str]:
    bands = ["short", "medium", "long"]
    return [bands[i % 3] for i in range(n)]


def _scarce_first(plan: list[str], order: tuple = ("long", "medium", "short")) -> list[int]:
    rank = {b: k for k, b in enumerate(order)}
    return sorted(range(len(plan)), key=lambda i: (rank[plan[i]], i))


def slugify(title: str, n: int = 24) -> str:
    """ASCII slug that keeps Hungarian letters readable (Törökország -> torokorszag)."""
    t = unicodedata.normalize("NFKD", title or "doc")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", t)[:n].strip("-")


WIKI_API = "https://{lang}.wikipedia.org/w/api.php"


def fetch_wikipedia(title: str, lang: str = "hu") -> str:
    """Plain text of the current full Wikipedia article (cached in dataset/raw/wiki/)."""
    cache = EVAL_ROOT / "dataset" / "raw" / "wiki" / f"{lang}-{slugify(title, 80)}.txt"
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    params = {"action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1, "format": "json",
              "titles": title}
    headers = {"User-Agent": "MimirEval/0.1 (TDK research, Obuda University; contact via GitHub Deatron01/Project-Mimir)"}
    with httpx.Client(timeout=60, headers=headers, follow_redirects=True) as c:
        r = c.get(WIKI_API.format(lang=lang), params=params)
        r.raise_for_status()
        pages = (r.json().get("query") or {}).get("pages") or {}
    text = next((p.get("extract", "") for p in pages.values() if p.get("extract")), "")
    # drop the reference-style tail sections, which are lists rather than prose
    text = re.split(r"\n==+ ?(Jegyzetek|Források|Források és jegyzetek|További információk|Kapcsolódó szócikkek|"
                    r"Irodalom|Külső hivatkozások|Lásd még|References|External links|See also|Notes) ?==+", text)[0]
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    return text


# ------------------------------------------------------------------------- EduQG
def eduqg_gold(ch: dict) -> list[dict]:
    out = []
    for q in ch.get("questions", []):
        qq, ans = q.get("question", {}), q.get("answer", {})
        choices = qq.get("question_choices") or []
        idx = ans.get("ans_choice")
        if not choices or idx is None or not (0 <= idx < len(choices)):
            continue
        ev = split_sentences(q.get("hl_sentences") or "")
        if not ev:
            continue
        g = {"id": qq.get("question_id"), "kerdes": qq.get("normal_format") or qq.get("question_text"),
             "helyes_valasz": choices[idx], "disztraktorok": [c for i, c in enumerate(choices) if i != idx],
             "evidence": ev}
        if q.get("bloom"):
            g["bloom_szint"] = BLOOM_EDUQG.get(str(q["bloom"]), str(q["bloom"]))
        out.append(g)
    return out


def eduqg_sections(ch: dict) -> list[tuple[str, str]]:
    t = ch["chapter_text"]
    parts = re.split(r"(?:^|\n\n| )(?=%d\.\d+ {2,}[A-Z])" % ch["chapter"], t)
    out = []
    for p in parts:
        m = re.match(r"\s*(\d+\.\d+) {2,}(.{3,80}?)(?: Learning Objectives| \n|\n)", p)
        if m and len(p) > 800:
            out.append((f"{m.group(1)} {m.group(2).strip()}", p.strip()))
    return out


def import_eduqg(source: str = "valid", n: int = 12, seed: int = 1, min_gold: int = 4,
                 max_gold: int = 10, name: str = "eduqg") -> Path:
    raw = []
    for split in (["valid", "train"] if source == "all" else [source] if source in EDUQG_URLS else []):
        raw += load_json_source(EDUQG_URLS[split])
    if not raw:
        raw = load_json_source(source)
    rng = random.Random(seed)
    by_subject: dict[str, list[dict]] = {}
    for ch in raw:
        by_subject.setdefault(EDUQG_SUBJECT.get(ch["bname"], "other"), []).append(ch)
    subjects = sorted(s for s in by_subject if s != "other")
    plan = _plan(n)
    placed, used_chapters = {}, set()
    for i in _scarce_first(plan):   # long documents first: only a few chapters qualify
        band = plan[i]
        subject = subjects[i % len(subjects)]
        chapters = by_subject[subject][:]
        rng.shuffle(chapters)
        for ch in chapters:
            key = (ch["bname"], ch["chapter"])
            if key in used_chapters:
                continue
            gold = eduqg_gold(ch)
            title = f"{ch['bname'].replace('_', ' ')} ch. {ch['chapter']}"
            lo, hi = BANDS[band]
            if band == "long":
                text = ch["chapter_text"].strip()
                if not (lo <= len(text) <= hi):
                    continue
                h = Haystack(text)
                qs = [g for g in gold if all(h.contains(e) for e in g["evidence"])]
            else:
                secs = eduqg_sections(ch)
                rng.shuffle(secs)
                text, qs = "", []
                for sec_title, sec in secs:
                    paras = [p.strip() for p in sec.split("\n\n") if p.strip()]
                    t, q = best_window(paras, lo, hi, gold)
                    if len(q) >= min_gold:
                        text, qs, title = t, q, f"{title}, {sec_title}"
                        break
            if len(qs) < min_gold:
                continue
            used_chapters.add(key)
            rng.shuffle(qs)
            placed[i] = ({"id": f"en-{subject.replace('_', '')}-{band}-{i + 1:02d}", "text": text,
                         "gold": qs[:max_gold], "title": title, "language": "en", "subject": subject,
                         "band": band, "difficulty": DIFFICULTIES[(i // len(subjects)) % 3],
                         "source": f"EduQG / OpenStax {ch['bname']} chapter {ch['chapter']}"})
            break
        else:
            print(f"[import] WARNING: no {band} document with >= {min_gold} gold questions for {subject}")
    docs = [placed[i] for i in sorted(placed)]
    return write_dataset(name, docs, "CC-BY-4.0 (OpenStax via EduQG)", True,
                         "Source: EduQG (Hadifar et al., IEEE Access 2023), OpenStax textbooks, CC BY 4.0.")


# ------------------------------------------------------------------------- MILQA
def _int(v) -> int | None:
    """Offsets arrive as int, "123", ["123"] or None depending on the file."""
    if isinstance(v, (list, tuple)):
        v = v[0] if v else None
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def _text(v) -> str:
    if isinstance(v, (list, tuple)):
        v = v[0] if v else ""
    if isinstance(v, dict):
        v = v.get("text", "")
    return str(v or "").strip()


def _span(x) -> dict:
    """One answer entry as {text, start, modanswer}; entries may be dicts or plain strings."""
    if isinstance(x, dict):
        mod = x.get("modanswer")
        mod = mod if isinstance(mod, list) else [mod] if mod else []
        return {"text": _text(x.get("text")), "start": _int(x.get("start", x.get("answer_start"))),
                "modanswer": [_text(m) for m in mod if _text(m)]}
    return {"text": _text(x), "start": None, "modanswer": []}


def _answers(qa: dict) -> tuple[list[dict], list[dict]]:
    a = qa.get("answers")
    if isinstance(a, dict):
        longs, shorts = a.get("long") or [], a.get("short") or []
        longs = longs if isinstance(longs, list) else [longs]
        shorts = shorts if isinstance(shorts, list) else [shorts]
        return [_span(x) for x in longs], [_span(x) for x in shorts]
    if isinstance(a, list):  # plain SQuAD
        return [], [_span(x) for x in a]
    return [], []


def _sentence_at(context: str, start: int | None, answer: str) -> str:
    if start is None or not (0 <= start < len(context)) or not context[start:].startswith(answer[:10]):
        start = context.find(answer)
    if start < 0:
        return ""
    left = max(context.rfind(". ", 0, start), context.rfind("\n", 0, start))
    right_candidates = [p for p in (context.find(". ", start), context.find("\n", start)) if p != -1]
    right = min(right_candidates) + 1 if right_candidates else len(context)
    return context[left + 1:right].strip()


def _impossible(qa: dict) -> bool:
    v = qa.get("is_impossible")
    return v is True or str(v).strip().lower() in ("true", "1")


def milqa_article(article: dict) -> tuple[list[str], list[dict]]:
    paras, gold = [], []
    for p in article.get("paragraphs", []):
        ctx = p.get("context") or ""          # not stripped: answer offsets refer to this string
        if not ctx.strip():
            continue
        paras.append(ctx.strip())
        for qa in p.get("qas", []):
            question = _text(qa.get("question"))
            if _impossible(qa) or not question:
                continue
            longs, shorts = _answers(qa)
            short = next((x for x in shorts if x["text"]), None)
            long_ = next((x for x in longs if x["text"]), None)
            key = (short["modanswer"][0] if short and short["modanswer"] else short["text"] if short else "") \
                or (long_["text"] if long_ else "")
            if not key:
                continue
            ev = long_["text"] if long_ else _sentence_at(ctx, short["start"], key)
            if not ev:
                continue
            qtype = qa.get("qtype")
            gold.append({"id": qa.get("id"), "kerdes": question, "helyes_valasz": key, "evidence": [ev],
                         "type": "open", "kerdestipus": qtype if isinstance(qtype, str) else None})
    return paras, gold


def _excerpt_len(article: dict) -> int:
    return sum(len(p.get("context") or "") for p in article.get("paragraphs", []))


def import_milqa(source: str = MILQA_URL, n: int = 24, seed: int = 1, min_gold: int = 4, max_gold: int = 10,
                 titles: list[str] | None = None, name: str = "milqa", long_from_wikipedia: bool = True) -> Path:
    """MILQA contexts are article excerpts (the test split tops out around 14,000 characters), so
    long documents come from the full current Wikipedia article of the same title: the MILQA
    questions whose evidence sentences are still in that article are kept as gold."""
    raw = load_json_source(source)
    articles = raw.get("data", raw) if isinstance(raw, dict) else raw
    if titles:
        want = {t.lower() for t in titles}
        articles = [a for a in articles if a.get("title", "").lower() in want]
    rng = random.Random(seed)
    articles = articles[:]
    rng.shuffle(articles)
    plan = _plan(n)
    placed, used = {}, set()
    # medium excerpts are the scarcest in MILQA; long ones come from Wikipedia, so they go last
    for i in _scarce_first(plan, ("medium", "short", "long")):
        band = plan[i]
        lo, hi = BANDS[band]
        # short/medium: keep articles whose own excerpt is already long for the long band
        order = articles if band == "long" else sorted(
            articles, key=lambda a: _excerpt_len(a) >= BANDS["long"][0])
        for a in order:
            if a.get("title") in used:
                continue
            paras, gold = milqa_article(a)
            if not paras:
                continue
            source_note = f"MILQA / Hungarian Wikipedia: {a.get('title', '')}"
            if band == "long":
                text = f"{a.get('title', '')}\n\n" + "\n\n".join(paras)
                if len(text) < lo and long_from_wikipedia:
                    try:
                        text = fetch_wikipedia(a.get("title", ""))
                    except Exception as e:
                        print(f"[import] could not fetch Wikipedia article '{a.get('title')}': {e}")
                        continue
                    source_note = (f"Hungarian Wikipedia (full article, fetched {time.strftime('%Y-%m-%d')}): "
                                   f"{a.get('title', '')}; gold questions from MILQA")
                if len(text) < lo:
                    continue
                text = text[:hi]
                h = Haystack(text)
                qs = [g for g in gold if all(h.contains(e) for e in g["evidence"])]
            else:
                text, qs = best_window(paras, lo, hi, gold)
            if len(qs) < min_gold:
                continue
            used.add(a.get("title"))
            rng.shuffle(qs)
            placed[i] = ({"id": f"hu-wiki-{band}-{i + 1:02d}-{slugify(a.get('title', ''))}", "text": text,
                         "gold": qs[:max_gold], "title": a.get("title", ""), "language": "hu",
                         "subject": "wikipedia", "band": band, "difficulty": DIFFICULTIES[(i // 3) % 3],
                         "source": source_note})
            break
        else:
            print(f"[import] WARNING: ran out of articles for a {band} document")
    docs = [placed[i] for i in sorted(placed)]
    return write_dataset(name, docs, "CC-BY-SA-4.0 (Wikipedia via MILQA)", True,
                         "Source: MILQA (Novák et al., LAW 2023), Hungarian Wikipedia, CC BY-SA 4.0. "
                         "Set each document's `subject` by hand after import.")
