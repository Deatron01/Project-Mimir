"""Importers: EduQG (chapter json) and MILQA (SQuAD 2.0 + long/short answers) on small synthetic samples."""
import json

import yaml

from mimir_eval import importers
from mimir_eval.dataset import load_dataset
from mimir_eval.schema import normalize_gold

SENT = "The {w} is a structure that stores {x} for the cell and controls how the {x} is used."


def _paragraphs(n, tag):
    return [" ".join(SENT.format(w=f"{tag}organ{i}{k}", x=f"{tag}thing{i}{k}") for k in range(6)) for i in range(n)]


def _chapter(num, bname, n_par=40):
    paras = _paragraphs(n_par, bname[:3])
    text = f"{num}.1   Section One Learning Objectives\n\n" + "\n\n".join(paras[: n_par // 2]) + \
           f"\n\n{num}.2   Section Two Learning Objectives\n\n" + "\n\n".join(paras[n_par // 2:])
    qs = []
    for i in range(0, n_par, 2):
        ev = SENT.format(w=f"{bname[:3]}organ{i}0", x=f"{bname[:3]}thing{i}0").replace(".", " .")
        qs.append({"question": {"question_id": f"{bname}-{i}", "question_text": f"What stores thing {i}?",
                                "question_choices": ["a", f"organ {i}", "c", "d"], "normal_format": f"Q{i}?"},
                   "answer": {"ans_choice": 1}, "bloom": "2" if i % 4 == 0 else None, "hl_sentences": ev})
    return {"chapter": num, "chapter_text": text, "questions": qs, "bname": bname}


def test_eduqg_import(tmp_path, monkeypatch):
    monkeypatch.setattr(importers, "EVAL_ROOT", tmp_path)
    chapters = [_chapter(n, b, 80 if n % 2 else 40) for n, b in enumerate(
        ["biology", "psychology", "business_law_i_essentials", "principles_of_accounting,_volume_1:_financial_accounting"] * 3, 1)]
    src = tmp_path / "eduqg.json"
    src.write_text(json.dumps(chapters), encoding="utf-8")
    m = importers.import_eduqg(str(src), n=6, seed=1)
    docs = yaml.safe_load(m.read_text(encoding="utf-8"))["documents"]
    assert len(docs) >= 4
    for d in docs:
        text = (tmp_path / "dataset" / d["path"]).read_text(encoding="utf-8")
        lo, hi = importers.BANDS[d["length"]]
        assert lo <= len(text) <= hi, (d["id"], len(text))
        gold = normalize_gold(json.loads((tmp_path / "dataset" / d["gold"]).read_text(encoding="utf-8")))
        assert len(gold) >= 4 and all(g["type"] == "mcq" and g["evidence"] for g in gold)
        assert all(importers.Haystack(text).contains(e) for g in gold for e in g["evidence"])
    # the manifest can be included from a main manifest
    main = tmp_path / "dataset" / "manifest.yaml"
    main.write_text("version: t\ninclude: [manifest_eduqg.yaml]\ndocuments: []\n", encoding="utf-8")
    ds = load_dataset(main)
    assert len(ds.documents) == len(docs) and ds.documents[0].gold()


def test_milqa_import(tmp_path, monkeypatch):
    monkeypatch.setattr(importers, "EVAL_ROOT", tmp_path)
    arts = []
    for a in range(9):
        paras = []
        for p, ctx in enumerate(_paragraphs(12 if a % 3 else 60, f"a{a}")):
            ans = f"a{a}thing{p}0"
            start = ctx.find(ans)
            qas = [{"id": f"{a}-{p}", "question": f"Mi a{a} {p}?", "is_impossible": False,
                    "answers": {"short": [{"text": ans, "start": start, "end": start + len(ans), "modanswer": []}],
                                "long": [{"text": ctx.split(". ")[0] + ".", "start": 0, "end": 10}]}},
                   {"id": f"{a}-{p}-x", "question": "Nincs?", "is_impossible": True, "answers": {"long": []}}]
            if p % 2:   # plain SQuAD answers too
                qas.append({"id": f"{a}-{p}-s", "question": "Sima?", "answers": [{"text": ans, "answer_start": start}]})
            paras.append({"context": ctx, "section": "", "qas": qas})
        arts.append({"title": f"Cikk {a}", "paragraphs": paras})
    src = tmp_path / "milqa.json"
    src.write_text(json.dumps({"version": "x", "data": arts}), encoding="utf-8")
    monkeypatch.setattr(importers, "fetch_wikipedia", lambda *a, **k: (_ for _ in ()).throw(OSError("offline")))
    m = importers.import_milqa(str(src), n=6, seed=2)
    docs = yaml.safe_load(m.read_text(encoding="utf-8"))["documents"]
    assert len(docs) == 6 and {d["length"] for d in docs} == {"short", "medium", "long"}
    for d in docs:
        gold = normalize_gold(json.loads((tmp_path / "dataset" / d["gold"]).read_text(encoding="utf-8")))
        assert all(g["type"] == "open" and g["key"] and "Nincs" not in g["text"] for g in gold)


def test_detok_and_sentences():
    s = importers.detok("the skin ( the integumentary system ) . Next “ quoted ” one .")
    assert s == "the skin (the integumentary system). Next “quoted” one."
    assert len(importers.split_sentences("First sentence is here . Second one is also here .")) == 2


def test_milqa_long_documents_from_wikipedia(tmp_path, monkeypatch):
    """MILQA excerpts are short; long documents come from the full Wikipedia article."""
    monkeypatch.setattr(importers, "EVAL_ROOT", tmp_path)
    arts, full = [], {}
    for a in range(12):
        paras = []
        for p, ctx in enumerate(_paragraphs(12, f"w{a}")):
            ans = f"w{a}thing{p}0"
            start = ctx.find(ans)
            paras.append({"context": ctx, "qas": [{"question": f"K {a} {p}?", "is_impossible": "false",
                          "answers": {"short": [{"text": ans, "start": str(start), "end": str(start + len(ans))}]}}]})
        arts.append({"title": f"Szócikk {a}", "paragraphs": paras})
        full[f"Szócikk {a}"] = "\n\n".join(p["context"] for p in paras) + "\n\n" + "\n\n".join(_paragraphs(40, f"x{a}"))
    src = tmp_path / "milqa.json"
    src.write_text(json.dumps({"data": arts}), encoding="utf-8")
    fetched = []
    monkeypatch.setattr(importers, "fetch_wikipedia", lambda t, lang="hu": fetched.append(t) or full[t])
    m = importers.import_milqa(str(src), n=6, seed=3)
    docs = yaml.safe_load(m.read_text(encoding="utf-8"))["documents"]
    longs = [d for d in docs if d["length"] == "long"]
    assert len(docs) == 6 and len(longs) == 2 and fetched
    assert all(d["chars"] >= 25000 and "full article" in d["source"] for d in longs)
    assert all(d["id"].startswith("hu-wiki-") and "szocikk" in d["id"] for d in docs)
