## Eredmények

A módszereket 9 dokumentumon (en, hu), dokumentumonként 3 ismétléssel (seed) értékeltük; minden vizsga 10 feleletválasztós kérdésből állt. A minőségi index a következő mutatók átlaga: formai megfelelés, forrással igazolt válasz, vakon megoldható, jó disztraktorok. Mindegyik 0 és 1 közötti, és mindegyiknél a nagyobb érték a jobb. Az értékeket először dokumentumonként átlagoltuk, majd a dokumentumokra vett bootstrap-mintavétellel (10 000 minta) 95%-os konfidenciaintervallumot számoltunk. A kérdések helyességét egy független nyelvi modell (gpt-oss:120b) ítélte meg, amely más modellcsaládba tartozik, mint a kérdéseket író modell.

### A legjobb módszer

A legmagasabb minőségi indexet az **E4b – Ellenőrzés, szervermodell** módszer érte el (0,99; 95% KI: 0,97–1,00), lásd a 2. ábrát. Lényege: E2 az egyetemi szerver nagy modelljén. Az alapmódszerhez (E0, 0,64) képest a különbség +0,35. A második helyezett az E2 (0,96); a különbség nem szignifikáns (páros Wilcoxon-próba, Holm-korrekció: p = 1,000).

**Győztes: E4b – Ellenőrzés, szervermodell** (minőségi index 0,99). Ha az adatok nem hagyhatják el a gépet (csak helyi modell), a legjobb választás az **E2 – Tervezés + ellenőrzés** (0,96).

**1. táblázat – A módszerek összesített rangsora** (`tabla1_osszesito`)

| Hely | Módszer | Minőségi index | Formai megfelelés | Forrással igazolt válasz | Vakon megoldható | Jó disztraktorok | Idő / vizsga (perc) | LLM-hívás / vizsga | Eredmény |
|---|---|---|---|---|---|---|---|---|---|
| 1. | E4b – Ellenőrzés, szervermodell | 0,99 | 100% | 98% | 100% | 98% | 47,7 | 37 | ★ Győztes |
| 2. | E2 – Tervezés + ellenőrzés | 0,96 | 100% | 90% | 97% | 96% | 3,5 | 51 | Legjobb helyi |
| 3. | B-doc-S – Teljes dokumentum, szerver | 0,95 | 100% | 90% | 100% | 89% | 4,0 | 1 |  |
| 4. | E2h – Ellenőrzés + hibrid keresés | 0,92 | 100% | 82% | 92% | 94% | 3,7 | 55 |  |
| 5. | E4 – Alapmódszer, szervermodell | 0,91 | 100% | 77% | 98% | 87% | 5,3 | 1 |  |
| 6. | E2f – Ellenőrzés vak teszt nélkül | 0,90 | 100% | 78% | 88% | 92% | 2,8 | 37 |  |
| 7. | E2x – Ellenőrzés más modellel | 0,89 | 100% | 78% | 83% | 95% | 7,6 | 20 |  |
| 8. | E3 – Ellenőrzés + fogalomgráf | 0,88 | 100% | 83% | 87% | 83% | 5,5 | 54 |  |
| 9. | E1 – Tervezés | 0,88 | 100% | 80% | 80% | 91% | 1,9 | 18 |  |
| 10. | E5a – Régi darabolás | 0,87 | 100% | 74% | 84% | 90% | 0,3 | 1 |  |
| 11. | E5c – Fix darabolás | 0,86 | 100% | 82% | 82% | 81% | 0,3 | 1 |  |
| 12. | B-doc-L – Teljes dokumentum, helyi | 0,83 | 83% | 79% | 86% | 85% | 0,4 | 1 |  |
| 13. | E5b – Szórás alapú darabolás | 0,70 | 100% | 39% | 78% | 63% | 0,3 | 1 |  |
| 14. | E0 – Alapmódszer | 0,64 | 100% | 43% | 62% | 52% | 0,3 | 1 |  |

**2. táblázat – A győztes az alapmódszerhez (E0) képest** (`tabla2_gyoztes_vs_alap`)

| Mutató | E0 – Alapmódszer | E4b – Ellenőrzés, szervermodell | Különbség |
|---|---|---|---|
| Minőségi index | 0,64 | 0,99 | +0,35 |
| Formai megfelelés | 100% | 100% | +0 %-pont |
| Forrással igazolt válasz | 43% | 98% | +55 %-pont |
| Vakon megoldható | 62% | 100% | +38 %-pont |
| Jó disztraktorok | 52% | 98% | +46 %-pont |
| Idő / vizsga (perc) | 0,3 | 47,7 | 150,4× lassabb |
| LLM-hívás / vizsga | 1 | 37 | 37× |

Mutatónként (3. ábra):

- **Formai megfelelés:** E4b: 100%, E0: 100%
- **Forrással igazolt válasz:** E4b: 98%, E0: 43%
- **Vakon megoldható:** E4b: 100%, E0: 62%
- **Jó disztraktorok:** E4b: 98%, E0: 52%
- **„A szöveg szerint” típusú kérdések aránya:** E4b: 0%, E0: 0%

### Mit ad hozzá az egyes komponens

Az 5. ábra lépésenként mutatja a minőségi index változását az alapmódszertől a teljes rendszerig: a tervezés +0,24; az ellenőrzés +0,08; a fogalomgráf -0,07.

### Minőség és költség

A jobb minőségnek ára van (4. ábra): egy 10 kérdéses vizsga az E4b módszerrel medián 47,7 perc, az alapmódszerrel 0,3 perc; az E4b medián 37 nyelvimodell-hívást igényel vizsgánként.

### Darabolás

A 6. ábra az alapmódszert hasonlítja össze különböző darabolási változatokkal: E5a (régi darabolás): 0,87; E0 (alapmódszer): 0,64; E5b (szórás alapú darabolás): 0,70; E5c (fix darabolás): 0,86.

### Adatkészlet

Az adatkészlet (eval-v1) 39 dokumentumból áll (27 magyar, 12 angol), összesen 326 arany (ember által írt) kérdéssel; ebben a jelentésben 9 dokumentum eredménye szerepel (6. táblázat).

**6. táblázat – Az értékelő adatkészlet** (`tabla6_adatkeszlet`)

| Forrás | Nyelv | Dokumentum | Rövid / közepes / hosszú | Karakter (átlag) | Karakter (min–max) | Arany kérdés | Licenc | Kiértékelve |
|---|---|---|---|---|---|---|---|---|
| saját | magyar | 3 | 3 / 0 / 0 | 1 971 | 1 696–2 295 | 12 | own | 3 |
| OpenStax via EduQG | angol | 12 | 4 / 4 / 4 | 28 980 | 5 843–68 063 | 74 | CC-BY-4.0 | 6 |
| Wikipedia via MILQA | magyar | 24 | 8 / 8 / 8 | 18 913 | 2 394–65 288 | 240 | CC-BY-SA-4.0 | 0 |
| Összesen | – | 39 | 15 / 12 / 12 | 20 707 | 1 696–68 063 | 326 | – | 9 |

### A bíráló megbízhatósága

(A tanári értékelés még nem érkezett be; a `rate-import` után a `report` elkészíti a 3. táblázatot.)

### Statisztikai próbák

A fő lépéseket páros Wilcoxon-próbával hasonlítottuk össze a dokumentumonkénti minőségi indexen; a p-értékeket a 6 összevetésre Holm-módszerrel korrigáltuk, a hatásméret a rangbiszeriális korreláció (r > 0: az új módszer jobb). Szignifikáns (p < 0,05): 0 összevetés.

**4. táblázat – Páros Wilcoxon-próbák** (`tabla4_szignifikancia`)

| Összevetés | Dokumentum (n) | Referencia | Új módszer | Különbség | Hatásméret (r) | p | p (Holm) | Szignifikáns |
|---|---|---|---|---|---|---|---|---|
| E1 vs B-doc-L | 6 | 0,83 | 0,88 | +0,04 | 0,24 | 0,688 | 0,875 | nem |
| E1 vs E0 | 6 | 0,64 | 0,88 | +0,24 | 0,62 | 0,219 | 0,875 | nem |
| E2 vs E1 | 6 | 0,88 | 0,96 | +0,08 | 1,00 | 0,031 | 0,188 | nem |
| E2x vs E2 | 6 | 0,96 | 0,89 | -0,06 | -0,90 | 0,062 | 0,312 | nem |
| E3 vs E2 | 6 | 0,96 | 0,88 | -0,07 | -0,62 | 0,219 | 0,875 | nem |
| E4 vs E0 | 3 | 0,40 | 0,93 | +0,54 | 1,00 | 0,250 | 0,875 | nem (n < 6) |

### Magyar és angol dokumentumok

Az 5. táblázat és a 7. ábra nyelvenként mutatja az eredményeket. A két nyelv dokumentumai különbözők (forrás, téma, hossz), ezért a különbség leíró jellegű, nem ok-okozati.

**5. táblázat – Magyar és angol dokumentumok** (`tabla5_nyelvek`)

| Módszer | Index – magyar (n) | Index – angol (n) | Különbség (magyar − angol) | Formai megfelelés (magyar / angol) | Forrással igazolt válasz (magyar / angol) | Vakon megoldható (magyar / angol) | Jó disztraktorok (magyar / angol) |
|---|---|---|---|---|---|---|---|
| E4b – Ellenőrzés, szervermodell | – (0) | 0,99 (6) | – | – / 100% | – / 98% | – / 100% | – / 98% |
| E2 – Tervezés + ellenőrzés | 0,96 (3) | 0,95 (3) | +0,02 | 100% / 100% | 93% / 87% | 97% / 97% | 96% / 96% |
| B-doc-S – Teljes dokumentum, szerver | 0,99 (3) | 0,90 (3) | +0,09 | 100% / 100% | 100% / 80% | 100% / 100% | 98% / 81% |
| E2h – Ellenőrzés + hibrid keresés | 0,91 (3) | 0,92 (3) | -0,01 | 100% / 100% | 80% / 83% | 90% / 93% | 94% / 93% |
| E4 – Alapmódszer, szervermodell | – (0) | 0,91 (6) | – | – / 100% | – / 77% | – / 98% | – / 87% |
| E2f – Ellenőrzés vak teszt nélkül | 0,86 (3) | 0,93 (3) | -0,07 | 100% / 100% | 77% / 80% | 80% / 97% | 88% / 96% |
| E2x – Ellenőrzés más modellel | 0,87 (3) | 0,91 (3) | -0,04 | 100% / 100% | 80% / 77% | 77% / 90% | 92% / 98% |
| E3 – Ellenőrzés + fogalomgráf | 0,84 (3) | 0,92 (3) | -0,08 | 100% / 100% | 77% / 90% | 77% / 97% | 83% / 83% |
| E1 – Tervezés | 0,85 (3) | 0,91 (3) | -0,06 | 100% / 100% | 80% / 80% | 70% / 90% | 90% / 92% |
| E5a – Régi darabolás | 0,87 (3) | 0,87 (3) | -0,01 | 100% / 100% | 78% / 70% | 79% / 89% | 90% / 90% |
| E5c – Fix darabolás | 0,77 (3) | 0,96 (3) | -0,19 | 100% / 100% | 69% / 94% | 69% / 96% | 69% / 93% |
| B-doc-L – Teljes dokumentum, helyi | 0,89 (3) | 0,77 (3) | +0,12 | 89% / 78% | 87% / 72% | 90% / 81% | 91% / 78% |
| E5b – Szórás alapú darabolás | 0,89 (3) | 0,51 (3) | +0,38 | 100% / 100% | 79% / 0% | 84% / 72% | 94% / 33% |
| E0 – Alapmódszer | 0,88 (3) | 0,40 (3) | +0,49 | 100% / 100% | 87% / 0% | 83% / 40% | 84% / 20% |

### Példák

Módszerenként egy jó és egy rossz kérdés a bíráló indoklásával a `peldak.md` fájlban található (a hibaelemzés alapanyaga).

### Táblázatok és ábrák

1. táblázat – A módszerek összesített rangsora (`tabla1_osszesito`).
2. táblázat – A győztes összevetése az alapmódszerrel (`tabla2_gyoztes_vs_alap`).
1. ábra – A vizsgált módszerek felépítése (`abra1_modszerek`).
2. ábra – A módszerek rangsora a minőségi index alapján, 95%-os konfidenciaintervallummal (`abra2_rangsor`).
3. ábra – Az egyes minőségi mutatók módszerenként (`abra3_mutatok`).
4. ábra – Minőség és futási idő (`abra4_minoseg_koltseg`).
5. ábra – Az egyes komponensek hozzájárulása (`abra5_komponensek`).
6. ábra – A darabolási változatok összehasonlítása (`abra6_darabolas`).
4. táblázat – Páros Wilcoxon-próbák a fő lépésekre (`tabla4_szignifikancia`).
5. táblázat – Magyar és angol dokumentumok (`tabla5_nyelvek`).
7. ábra – Minőségi index nyelvenként (`abra7_nyelvek`).
6. táblázat – Az értékelő adatkészlet (`tabla6_adatkeszlet`).
Példakérdések a hibaelemzéshez: `peldak.md`.

*Generálva: 2026-09-28, `python -m mimir_eval report`; adatok: B-doc-L_20260927_130112, B-doc-S_20260928_000032, E0_20260927_121353, E1_20260927_173119, E2_20260927_184417, E2f_20260927_210952, E2h_20260927_215454, E2x_20260927_195117, E3_20260927_224855, E4_20260928_025504, E4b_20260928_055715, E5a_20260928_115954, E5b_20260928_132736, E5c_20260928_145756*
