"""Prompts for the blueprint pipeline. Each system prompt starts with a [role] tag so logs and
the test mock can tell the calls apart. Internal steps (planner, graph, verifier) are written in
English, which small local models follow more reliably; the generator prompt is Hungarian and
repeats the production prompt's rules, so E0 and E1+ differ in structure, not in rules."""
from __future__ import annotations

import json

BP_PROMPT_VERSION = "blueprint-v1"

LANG_NAME = {"hu": "Hungarian", "en": "English"}
LANG_HU = {"hu": "magyar", "en": "angol"}

BLOOM_HU = {
    "remember": "Emlékezés (tény vagy fogalom felidézése)",
    "understand": "Megértés (magyarázat, összehasonlítás, saját szavakkal)",
    "apply": "Alkalmazás (a tudás használata új, konkrét helyzetben)",
    "analyze": "Elemzés (összefüggések, okok, következmények feltárása)",
    "evaluate": "Értékelés (állítások, döntések megítélése indoklással)",
}

# ------------------------------------------------------------------ planner
PLANNER_SYSTEM = "[planner] You design exam blueprints. Reply with one valid JSON object only."


def planner_prompt(overview: str, n_concepts: int, language: str) -> str:
    return f"""Below is a document split into numbered chunks (C0, C1, ...). Some chunks are shortened.

{overview}

List the {n_concepts} most important, clearly distinct concepts, facts or ideas a student should be tested on.
Cover the whole document: every major part should have at least one concept. Prefer central ideas over trivia.
Write concept names and descriptions in {LANG_NAME.get(language, language)}.

JSON shape:
{{"concepts": [{{"concept": "short name", "description": "one sentence: what exactly should be tested",
  "chunk_ids": ["C0"], "importance": 3}}]}}
importance: 3 = central, 2 = important, 1 = detail."""


# ------------------------------------------------------------------ concept graph
GRAPH_SYSTEM = "[graph] You extract knowledge graphs from teaching material. Reply with one valid JSON object only."


def graph_prompt(chunks_block: str, language: str) -> str:
    return f"""Extract the knowledge in these chunks as a small concept graph. Chunk ids are in brackets.

{chunks_block}

Rules:
- concepts: the key terms, entities, processes or ideas (max 8 per chunk). "parent" is the broader category
  the concept belongs to (e.g. "T-sejt" -> "limfocita"), or "" if none. Give the chunk ids where it appears.
- facts: short atomic statements from the text (max 6 per chunk), each with the concepts it mentions.
- relations: typed links between concepts: is_a, part_of, causes, contrasts_with, used_for, related_to.
Write names and facts in {LANG_NAME.get(language, language)}, exactly as the text names them.

JSON shape:
{{"concepts": [{{"name": "...", "definition": "...", "parent": "...", "chunk_ids": ["C0"]}}],
 "facts": [{{"text": "...", "concepts": ["..."], "chunk_id": "C0"}}],
 "relations": [{{"source": "...", "relation": "is_a", "target": "..."}}]}}"""


# ------------------------------------------------------------------ generator
GENERATOR_SYSTEM = ("[generator] Te egy kiemelkedő tudású oktatásmódszertani szakértő és professzionális vizsgakészítő "
                    "vagy. Kizárólag érvényes JSON formátumban válaszolj, markdown formázás nélkül!")

TYPE_RULES = {
    "mcq": 'feleletválasztós ("mcq"): pontosan 4 válasz, ebből pontosan 1 helyes és 3 hihető, de a kontextus szerint '
           'egyértelműen helytelen disztraktor; a válaszok hossza és formája legyen hasonló.',
    "tf": 'igaz-hamis ("tf"): a kérdés egy állítás; pontosan 2 válasz: "Igaz" és "Hamis", ebből az egyik helyes.',
    "open": 'kifejtős ("open"): pontosan 1 válasz (is_correct: true), ami a rövid megoldókulcs.',
}


def generator_prompt(slot: dict, context: list[tuple[str, str]], difficulty: str, language: str,
                     existing: list[str], distractor_hints: list[str], feedback: str | None) -> str:
    ctx = "\n\n".join(f"[{cid}] {text}" for cid, text in context)
    avoid = "\n".join(f"- {q}" for q in existing[-12:]) or "- (még nincs)"
    hints = ""
    if distractor_hints and slot["type"] == "mcq":
        hints = ("\nDISZTRAKTOR-ÖTLETEK (rokon fogalmak a dokumentumból; csak akkor használd, ha a kontextus szerint "
                 "biztosan helytelen válaszok):\n" + "\n".join(f"- {h}" for h in distractor_hints[:6]) + "\n")
    fb = ""
    if feedback:
        fb = f"\nAZ ELŐZŐ PRÓBÁLKOZÁS HIBÁS VOLT, JAVÍTSD:\n{feedback}\n"
    return f"""Készíts PONTOSAN EGY vizsgakérdést az alábbi terv szerint.

TERV:
- Fogalom: {slot['concept']}
- Mit kérdezzen: {slot.get('description', '')}
- Kérdéstípus: {TYPE_RULES[slot['type']]}
- Bloom-szint: {BLOOM_HU[slot['bloom']]}
- Vizsga nehézsége: {difficulty}
- Nyelv: a kérdést és a válaszokat {LANG_HU.get(language, language)} nyelven írd.

KÖTELEZŐ SZABÁLYOK:
1. ZÉRÓ HALLUCINÁCIÓ: KIZÁRÓLAG a KONTEXTUS alapján dolgozz. A helyes válasznak a kontextusból igazolhatónak kell lennie.
2. HIVATKOZÁS: a "citations" mezőbe írd azoknak a részleteknek az azonosítóját (pl. "C3"), amelyek igazolják a helyes választ.
3. NO LATEX: Tilos LaTeX formázást vagy dollárjeleket használni.
4. META-REFERENCIA TILALOM: Tilos a szövegre vagy a dokumentum szerkezetére hivatkozni ("a szöveg szerint", "a fenti részlet", "a 3. pontban"). Úgy fogalmazz, mintha egy általános vizsgát írnál.
5. NE ISMÉTELD a már elkészült kérdéseket:
{avoid}
{hints}{fb}
KONTEXTUS:
{ctx}

KIMENETI FORMÁTUM (csak ez a JSON objektum):
{{"type": "{slot['type']}", "text": "A kérdés szövege?", "answers": [{{"text": "...", "is_correct": true}}, {{"text": "...", "is_correct": false}}],
 "citations": ["C0"], "bloom": "{slot['bloom']}", "explanation": "egy mondat: miért ez a helyes válasz"}}"""


# ------------------------------------------------------------------ verifier
VERIFIER_SYSTEM = "[verifier] You check exam questions against source text. Reply with one valid JSON object only."


def grounding_prompt(q: dict, source: str) -> str:
    letters = "ABCDEFGH"
    opts = "\n".join(f"{letters[i]}. {o['text']}{'   <-- marked correct' if o['correct'] else ''}"
                     for i, o in enumerate(q["options"]))
    return f"""SOURCE:
\"\"\"
{source}
\"\"\"

QUESTION ({q['type']}): {q['text']}
{opts}

Check strictly against the SOURCE only:
1. key_supported: is the marked-correct answer clearly supported by the SOURCE?
2. For every option NOT marked correct: is it clearly wrong according to the SOURCE? (options_wrong, in order, A.. skipping the correct one)
3. ambiguous: could a careful reader argue that more than one option is correct?
4. problems: one short sentence describing any problem ("" if none).

JSON shape: {{"key_supported": true, "options_wrong": [true, true, true], "ambiguous": false, "problems": ""}}"""


def blind_prompt(q: dict, order: list[int], source: str) -> str:
    letters = "ABCDEFGH"
    opts = "\n".join(f"{letters[j]}. {q['options'][i]['text']}" for j, i in enumerate(order))
    return f"""SOURCE:
\"\"\"
{source}
\"\"\"

Answer the question using only the SOURCE. Exactly one option is correct.
{q['text']}
{opts}

JSON shape: {{"answer": "A"}}"""


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)
