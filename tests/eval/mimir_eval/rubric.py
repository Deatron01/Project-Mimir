"""One rubric, used by both the LLM judge and the teachers' rating sheet (RQ3 needs them identical)."""

CRITERIA = ["correctness", "clarity", "distractor_quality", "bloom_fit"]

RUBRIC_EN = {
    "correctness": "The marked answer is correct according to the source, and no other option is also correct. "
                   "1 = key wrong or two options correct; 3 = key right but imprecise; 5 = key fully right, unambiguous.",
    "clarity": "The question is understandable on its own, grammatical, unambiguous and does not refer to "
               "'the text' or the document structure. 1 = confusing; 3 = understandable with effort; 5 = exam-ready wording.",
    "distractor_quality": "Wrong options are clearly wrong per the source but plausible to a student who has not "
                          "learned the material (same topic, similar length and form). 1 = absurd or also correct; "
                          "3 = some plausible; 5 = all plausible and wrong. Leave empty for open questions.",
    "bloom_fit": "The cognitive level fits the requested difficulty (easy: remember/understand; medium: apply/"
                 "understand; hard: analyse/evaluate). 1 = clearly wrong level; 3 = borderline; 5 = fits well.",
    "would_use": "Would you put this question into a real exam with at most minor edits? (yes/no)",
}

RUBRIC_HU = {
    "correctness": "Helyesség: a megjelölt válasz a forrás szerint helyes, és más opció nem helyes. "
                   "1 = hibás kulcs vagy két helyes opció; 3 = helyes, de pontatlan; 5 = teljesen helyes, egyértelmű.",
    "clarity": "Érthetőség: a kérdés önmagában érthető, nyelvtanilag helyes, egyértelmű, nem hivatkozik „a szövegre” "
               "vagy a dokumentum szerkezetére. 1 = zavaros; 3 = nehezen érthető; 5 = vizsgakész megfogalmazás.",
    "distractor_quality": "Disztraktorok: a rossz válaszok a forrás szerint egyértelműen rosszak, de egy felkészületlen "
                          "diák számára hihetők (azonos téma, hasonló hossz és forma). 1 = abszurd vagy szintén helyes; "
                          "3 = részben hihető; 5 = mind hihető és rossz. Kifejtős kérdésnél hagyd üresen.",
    "bloom_fit": "Szintillesztés: a kognitív szint megfelel a kért nehézségnek (könnyű: felidézés/megértés; közepes: "
                 "alkalmazás/megértés; nehéz: elemzés/értékelés). 1 = egyértelműen rossz szint; 3 = határeset; 5 = illik.",
    "would_use": "Beraknád ezt a kérdést egy valódi dolgozatba legfeljebb apró javítással? (igen/nem)",
}
