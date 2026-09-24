> **PILOT – nem végleges eredmény.** Csak 1 dokumentum; ennyi adatból statisztikailag szignifikáns különbség nem mutatható ki (páros Wilcoxon-próbához legalább 6 dokumentum kell). A teljes futás után a `python -m mimir_eval report` ugyanezt a szöveget a végleges számokkal generálja újra.

## Eredmények

A módszereket 1 dokumentumon (hu), dokumentumonként 3 ismétléssel (seed) értékeltük; minden vizsga 10 feleletválasztós kérdésből állt. A minőségi index a következő mutatók átlaga: formai megfelelés, forrással igazolt válasz, vakon megoldható, jó disztraktorok. Mindegyik 0 és 1 közötti, és mindegyiknél a nagyobb érték a jobb. Az értékeket először dokumentumonként átlagoltuk, majd a dokumentumokra vett bootstrap-mintavétellel (10 000 minta) 95%-os konfidenciaintervallumot számoltunk. A kérdések helyességét egy független nyelvi modell (gpt-oss:120b) ítélte meg, amely más modellcsaládba tartozik, mint a kérdéseket író modell.

### A legjobb módszer

A legmagasabb minőségi indexet az **E4 – Alapmódszer, szervermodell** módszer érte el (0,99), lásd a 2. ábrát. Lényege: E0 az egyetemi szerver nagy modelljén. Az alapmódszerhez (E0, 0,83) képest a különbség +0,16. A második helyezett az E5b (0,90); a különbség nem szignifikáns (páros Wilcoxon-próba, Holm-korrekció: p = 1,000).

**Győztes: E4 – Alapmódszer, szervermodell** (minőségi index 0,99). Ha az adatok nem hagyhatják el a gépet (csak helyi modell), a legjobb választás az **E5b – Szórás alapú darabolás** (0,90).

**1. táblázat – A módszerek összesített rangsora** (`tabla1_osszesito`)

| Hely | Módszer | Minőségi index | Formai megfelelés | Forrással igazolt válasz | Vakon megoldható | Jó disztraktorok | Idő / vizsga (perc) | LLM-hívás / vizsga | Eredmény |
|---|---|---|---|---|---|---|---|---|---|
| 1. | E4 – Alapmódszer, szervermodell | 0,99 | 100% | 100% | 100% | 97% | 6,6 | 1 | ★ Győztes |
| 2. | E5b – Szórás alapú darabolás | 0,90 | 100% | 80% | 90% | 91% | 0,3 | 1 | Legjobb helyi |
| 3. | E5a – Régi darabolás | 0,90 | 100% | 80% | 86% | 93% | 0,3 | 1 |  |
| 4. | E1 – Tervezés | 0,88 | 100% | 73% | 93% | 87% | 3,0 | 24 |  |
| 5. | E3 – Ellenőrzés + fogalomgráf | 0,85 | 67% | 87% | 100% | 87% | 8,0 | 103 |  |
| 6. | E0 – Alapmódszer | 0,83 | 100% | 67% | 85% | 80% | 0,3 | 1 |  |
| 7. | E5c – Fix darabolás | 0,81 | 100% | 60% | 79% | 83% | 0,3 | 1 |  |
| 8. | E2h – Ellenőrzés + hibrid keresés | 0,76 | 67% | 67% | 79% | 93% | 6,7 | 82 |  |
| 9. | E2 – Tervezés + ellenőrzés | 0,76 | 67% | 73% | 77% | 89% | 6,2 | 74 |  |
| 10. | E2f – Ellenőrzés vak teszt nélkül | 0,73 | 67% | 53% | 82% | 90% | 5,3 | 58 |  |

**2. táblázat – A győztes az alapmódszerhez (E0) képest** (`tabla2_gyoztes_vs_alap`)

| Mutató | E0 – Alapmódszer | E4 – Alapmódszer, szervermodell | Különbség |
|---|---|---|---|
| Minőségi index | 0,83 | 0,99 | +0,16 |
| Formai megfelelés | 100% | 100% | +0 %-pont |
| Forrással igazolt válasz | 67% | 100% | +33 %-pont |
| Vakon megoldható | 85% | 100% | +15 %-pont |
| Jó disztraktorok | 80% | 97% | +17 %-pont |
| Idő / vizsga (perc) | 0,3 | 6,6 | 20,1× lassabb |
| LLM-hívás / vizsga | 1 | 1 | 1× |

Mutatónként (3. ábra):

- **Formai megfelelés:** E4: 100%, E0: 100%
- **Forrással igazolt válasz:** E4: 100%, E0: 67%
- **Vakon megoldható:** E4: 100%, E0: 85%
- **Jó disztraktorok:** E4: 97%, E0: 80%
- **„A szöveg szerint” típusú kérdések aránya:** E4: 0%, E0: 0%

### Mit ad hozzá az egyes komponens

Az 5. ábra lépésenként mutatja a minőségi index változását az alapmódszertől a teljes rendszerig: a tervezés +0,05; az ellenőrzés -0,12; a fogalomgráf +0,09.

### Minőség és költség

A jobb minőségnek ára van (4. ábra): egy 10 kérdéses vizsga az E4 módszerrel medián 6,6 perc, az alapmódszerrel 0,3 perc; az E4 medián 1 nyelvimodell-hívást igényel vizsgánként.

### Darabolás

A 6. ábra az alapmódszert hasonlítja össze különböző darabolási változatokkal: E5a (régi darabolás): 0,90; E0 (alapmódszer): 0,83; E5b (szórás alapú darabolás): 0,90; E5c (fix darabolás): 0,81.

### Táblázatok és ábrák

1. táblázat – A módszerek összesített rangsora (`tabla1_osszesito`).
2. táblázat – A győztes összevetése az alapmódszerrel (`tabla2_gyoztes_vs_alap`).
1. ábra – A vizsgált módszerek felépítése (`abra1_modszerek`).
2. ábra – A módszerek rangsora a minőségi index alapján, 95%-os konfidenciaintervallummal (`abra2_rangsor`).
3. ábra – Az egyes minőségi mutatók módszerenként (`abra3_mutatok`).
4. ábra – Minőség és futási idő (`abra4_minoseg_koltseg`).
5. ábra – Az egyes komponensek hozzájárulása (`abra5_komponensek`).
6. ábra – A darabolási változatok összehasonlítása (`abra6_darabolas`).

*Generálva: 2026-09-24, `python -m mimir_eval report`; adatok: E0_20260923_180520, E1_20260923_181906, E2_20260923_184104, E2f_20260923_191817, E2h_20260923_195340, E3_20260923_202615, E4_20260923_210124, E5a_20260923_215312, E5b_20260923_220538, E5c_20260923_222135*
