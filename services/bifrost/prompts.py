"""Bifrost prompt templates.

Kept in a separate, dependency-free module so the evaluation harness
(tests/eval) can build exactly the same prompt as production.
"""

PROMPT_VERSION = "v1.0"

SYSTEM_PROMPT = "Te egy kiemelkedő tudású oktatásmódszertani szakértő és vizsgakészítő vagy. Kizárólag érvényes JSON formátumban válaszolj, markdown formázás nélkül!"


def build_naive_prompt(context_text: str, query: str, fmt: str = "pdf") -> str:
    """The v1 single-call exam prompt (top-k context -> whole exam)."""
    return f"""Te egy kiemelkedő tudású oktatásmódszertani szakértő és professzionális vizsgakészítő vagy.

        KÖTELEZŐ SZABÁLYOK, AMIKET SZIGORÚAN BE KELL TARTANOD:
        1. ZÉRÓ HALLUCINÁCIÓ: KIZÁRÓLAG a megadott KONTEXTUS alapján dolgozz! Ha a kontextus nem tartalmazza a választ, ne találj ki semmit!
        2. FELHASZNÁLÓI UTASÍTÁS KÖVETÉSE: Alább a FELADAT részben megkapod a felhasználó pontos kérését. Ebből kell kiolvasnod, hogy HÁNY DARAB és MILYEN TÍPUSÚ (pl. feleletválasztós, igaz-hamis, kifejtős) kérdést kér. Pontosan a kért mennyiséget és típust generáld le!
        3. DISZTRAKTOROK: Feleletválasztós (mcq) kérdés esetén 1 helyes és 3 hihető, de helytelen válasz legyen.
        4. NO LATEX: Szigorúan TILOS LaTeX formázást vagy dollárjeleket ($) használni!
        5. META-REFERENCIA TILALOM: Szigorúan TILOS a dokumentum szerkezetére kérdezni (pl. "Mi van a 4.3 pontban?"). Úgy fogalmazz, mintha egy általános vizsgát írnál.

        KONTEXTUS:
        {context_text}

        FELADAT (A felhasználó pontos kérése):
        "{query}"

        KIMENETI FORMÁTUM:
        A válaszod KIZÁRÓLAG egy tiszta, érvényes JSON objektum lehet! Szigorúan TILOS markdown formázást (```json) és megjegyzéseket (//) használni!
        
        A struktúrának pontosan így kell kinéznie:
        {{
            "title": "Mimir AI Vizsga",
            "format": "{fmt}",
            "questions": [
                {{
                    "type": "mcq",
                    "text": "A pontos és egyértelmű kérdés szövege?",
                    "answers": [
                        {{"text": "Helyes válasz", "is_correct": true}},
                        {{"text": "Helytelen válasz 1", "is_correct": false}},
                        {{"text": "Helytelen válasz 2", "is_correct": false}},
                        {{"text": "Helytelen válasz 3", "is_correct": false}}
                    ]
                }}
            ]
        }}

        SZABÁLYOK A VÁLASZOKHOZ:
        - Ha a típus "mcq" (feleletválasztós): kövesd a fenti példát (1 true, 3 false).
        - Ha a típus "tf" (igaz-hamis): pontosan 2 válasz legyen (az egyik true, a másik false).
        - Ha a típus "open" (kifejtős): pontosan 1 válasz legyen (is_correct: true), ami a megoldókulcsot tartalmazza.
        """
