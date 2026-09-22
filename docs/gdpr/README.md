# GDPR / Adatvédelem

| Dokumentum | Magyar | English | Kinek szól / Audience |
| --- | --- | --- | --- |
| Adatkezelési tájékoztató / Privacy notice | [privacy-notice.hu.md](privacy-notice.hu.md) | [privacy-notice.en.md](privacy-notice.en.md) | Felhasználók (a weboldal `/privacy` oldalán is) / Users (also on the website at `/privacy`) |
| Megfelelőségi dokumentáció / Compliance pack | [compliance.hu.md](compliance.hu.md) | [compliance.en.md](compliance.en.md) | Üzemeltető és fejlesztők / Operator and developers |

**HU:** A megfelelőségi dokumentáció tartalmazza az adatkezelési nyilvántartást, a megőrzési rendet, az adatfeldolgozók listáját, a technikai és szervezési intézkedéseket, a hatásvizsgálati előszűrést, az érintetti kérelmek és az adatvédelmi incidensek kezelésének rendjét, az MI-rendelet kapcsolódási pontjait, valamint egy ellenőrzőlistát arról, mi valósult meg és mi tervezett. Éles indulás előtt jogi átvizsgálás és a `[KITÖLTENDŐ]` mezők kitöltése szükséges.

**EN:** The compliance pack contains the record of processing activities, retention schedule, processor list, technical and organisational measures, DPIA screening, data subject request and breach procedures, AI Act touchpoints, and a checklist of what is implemented and what is planned. Before going live it needs a legal review and every `[TO BE COMPLETED]` field filled in.

## Konfiguráció / Configuration

| Változó / Variable | Alapérték / Default | Szolgáltatás / Service | Hatás / Effect |
| --- | --- | --- | --- |
| `LOCAL_ONLY` | `false` | Bifrost, Heimdall, Wellspring | `true`: nincs hívás az egyetemi GenAI API felé / no calls to the university GenAI API |
| `JOB_TTL_SECONDS` | `3600` | Bifrost | Feladateredmények élettartama / lifetime of job results |
| `AUDIT_RETENTION_DAYS` | `30` | The Forge | MI működési napló megőrzése / AI audit log retention |
| `HISTORY_RETENTION_DAYS` | `365` | Skald | Mentett tesztek maximális megőrzése / max retention of saved tests |
