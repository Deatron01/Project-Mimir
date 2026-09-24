# Usability test plan – topic workspace (FE-UX-05)

**Status:** ready to run · **Owner:** frontend (Bence) · **Needs:** 5–6 teachers, 1 moderator, 1 note-taker
**Build under test:** the `v1` UI on the mock API (`npm run dev`, or a preview deploy with `VITE_API_MODE=v1`, `VITE_USE_MOCKS=true`). No real student data is involved, so no data processing agreement is needed for the sessions.

## 1. Goals

1. Can a teacher who has never seen Mimir create a topic, add documents and get a usable test **without help**?
2. Do teachers understand that **topics are separate** (documents and chats do not mix) and that **unsaved tests are temporary**?
3. Is the **review step** (EU AI Act Art. 14) actually used: do people read and edit questions before exporting?
4. Are the **privacy controls** findable: upload consent, deleting a topic, downloading and deleting account data?
5. Does the UI work for people using the **keyboard only** or a **screen reader** (at least one participant, see §6)?

## 2. Participants

| # | Profile | Why |
| --- | --- | --- |
| 5–6 | Secondary-school teachers (mix of STEM and humanities), Hungarian UI | Primary users |
| of which ≥ 1 | Uses a screen reader (NVDA or VoiceOver) or keyboard only | Accessibility (FE-09) |
| of which ≥ 1 | Teaches in English or uses the English UI | Language switch, exam language |
| of which ≥ 2 | Rarely use AI tools | Trust and wording |

Recruit through the university's teacher-training network. Offer a small thank-you (book voucher). Participants sign a short consent form for screen and voice recording; recordings are deleted 90 days after the report.

## 3. Setup

- 45-minute moderated sessions, remote (Teams/Meet, screen share) or in person with a laptop.
- Fresh browser profile per participant; reset the demo data ("Mock mailbox → Reset demo data").
- Give each participant two short sample documents on the desktop (a TXT and an MD file, ~1 page each, on a topic from their own subject) and one file named `scan-fail.pdf` to trigger the "no text" error.
- Think-aloud protocol. The moderator does not help unless the participant is stuck for 3 minutes; that counts as a failure for the task.

## 4. Tasks (read aloud in Hungarian; English in brackets)

| # | Task prompt | Success criterion | Measures |
| --- | --- | --- | --- |
| T1 | „Regisztrálj egy fiókot, és jelentkezz be.” (Create an account and sign in.) | Account verified via the mock mailbox, lands on Topics | time, errors |
| T2 | „Hozz létre egy témát a következő dolgozatodhoz, és töltsd fel a két dokumentumot.” (Create a topic for your next test and upload the two documents.) | Topic created, both files *Ready*, consent ticked | time, whether the consent text is read |
| T3 | „Tölts fel még egy fájlt: scan-fail.pdf.” (Upload one more file.) | Understands the error and either retries or deletes the file | error comprehension (ask: "what happened?") |
| T4 | „Készíttess egy 8 kérdéses, közepes nehézségű tesztet, csak feleletválasztós kérdésekkel.” (Generate an 8-question, medium, multiple-choice test.) | Finds the settings, test generated | settings discoverability |
| T5 | „Nézd át a tesztet. Egy kérdés nem tetszik: cseréltesd le. Tegyél egy kérdést a lista elejére.” (Review the test; replace a question you don't like; move a question to the top.) | Uses regenerate; reorders (drag or buttons) | which reorder method, edits made |
| T6 | „Honnan vette a gép a 2. kérdést?” (Where did question 2 come from?) | Opens *Sources* | citation discoverability |
| T7 | „Mentsd el a tesztet, és töltsd le PDF-ben megoldókulccsal.” (Save the test and download it as PDF with an answer key.) | Saved + correct export format | |
| T8 | „Hol találod meg ezt a tesztet egy hét múlva?” (Where will you find this test next week?) | Navigates to *My tests* or the topic's Tests tab | mental model of saving |
| T9 | „Kérdezz rá valamire a dokumentumokban.” (Ask something about the documents.) | Uses *Ask a question*, reads the answer with sources | |
| T10 | „Töröld a témát mindenestül.” (Delete the topic with everything in it.) | Topic deleted via type-to-confirm | reads the warning? |
| T11 | „Töltsd le az összes adatodat, amit a Mimir tárol rólad.” (Download all data Mimir holds about you.) | Finds *Your data*, export downloaded | privacy findability |
| T12 | „Válts angol nyelvre és sötét módra.” (Switch to English and dark mode.) | Both changed | |

## 5. Post-task and post-test questions

- After each task: Single Ease Question (1–7).
- After T5: „Mennyire bíznál meg ezekben a kérdésekben ellenőrzés nélkül?” (How much would you trust these questions without checking?) 1–7 + why.
- After T8 and T10: ask the participant to explain in their own words what happens to *unsaved* tests and to the documents after deleting a topic. Score: correct / partly / wrong.
- End: SUS questionnaire (Hungarian validated version), plus "What would stop you from using this in class?"

## 6. Accessibility session (≥ 1 participant)

Same tasks, with extra observation points: skip link, focus order in the New topic dialog, focus returning after closing dialogs, announcements for upload progress / job progress / new messages, keyboard drag-and-drop in the editor (Space, arrows, Space), error messages being read out. Log every point where the participant had to leave the keyboard or the screen reader said nothing useful.

## 7. Metrics and targets

| Metric | Target |
| --- | --- |
| Task success (unaided) | ≥ 80 % for T1–T8 |
| Median time T2 (topic + 2 uploads) | < 3 min |
| Median time T4 (first test) | < 2 min (excluding generation time) |
| SEQ average | ≥ 5.5 |
| SUS | ≥ 75 |
| Correct explanation of "unsaved tests are temporary" | ≥ 4 of 6 |
| Accessibility blockers | 0 |

## 8. Analysis and output

- Note-taker logs issues in a shared sheet: task, observation, quote, severity (0 cosmetic – 4 blocker), frequency.
- Within 3 days: debrief, affinity-map the issues, create a GitHub issue per finding (label `ux-research`, link to FE-UX-05), and a 1-page summary with the top 5 changes.
- Re-test the top issues with 2–3 new participants after fixes.

## 9. Schedule

| Week | Activity |
| --- | --- |
| 1 | Recruit, consent forms, pilot session with a colleague, fix the script |
| 2 | 5–6 sessions |
| 3 | Analysis, issues, summary |
| 4–5 | Fixes; short re-test |

## 10. Moderator checklist

- [ ] Demo data reset, browser profile fresh, sample files on the desktop
- [ ] Recording consent signed; recording started
- [ ] Remind: "We are testing the software, not you."
- [ ] Do not name UI elements in the prompts (say "save it", not "tick Save to My tests")
- [ ] Stop recording; thank-you voucher
