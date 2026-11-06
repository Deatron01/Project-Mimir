# A TDK dolgozat új felépítése – írási terv (2026. november)

Ez a fájl a fejezetek íróinak (embernek és agentnek) közös útmutatója. Minden szám forrása
`tdk/elemzes/szamok.md` / `szamok.json` (generálja: `tdk/elemzes/elemzes.py`). Számot csak onnan
szabad átvenni; kerekítés: két tizedes (0,95), ráták egész százalékban (86 %), tizedesvessző.

## Célkeret

Kb. 50 oldal: ~4 oldal előlap + ~46 oldal főszöveg (12 pt, másfeles sorköz, A4, 2,5 cm margó).
Ökölszabály: egy teljes szövegoldal ≈ 330 szó; egy közepes táblázat vagy ábra ≈ fél oldal.
Irodalomjegyzék és függelék ezen felül (≈ 5 + 4 oldal), 60–75 hivatkozással.

| Fejezet | Fájl | Oldal | Szó (kb.) |
|---|---|---|---|
| Tartalmi összefoglaló | `fejezetek/osszefoglalo.tex` | 1 | 330 |
| 1. Bevezetés | `fejezetek/bevezetes.tex` | 3 | 900 |
| 2. Szakirodalmi háttér | `fejezetek/szakirodalom.tex` | 10 | 2 900 + 1 táblázat |
| 3. A Mimir rendszer | `fejezetek/modszertan.tex` | 8 | 1 800 + 3 ábra + 3 táblázat |
| 4. Kiértékelési módszertan | `fejezetek/kiertekeles.tex` | 6 | 1 400 + 1 ábra + 2 táblázat |
| 5. Eredmények | `fejezetek/eredmenyek.tex` | 12 | 2 300 + 5 ábra + 5 táblázat |
| 6. Az eredmények értékelése | `fejezetek/diszkusszio.tex` | 5 | 1 400 + 1 táblázat |
| 7. Összefoglalás | `fejezetek/osszefoglalas.tex` | 2 | 600 |

## A központi üzenet

„Nem jobb prompt, hanem ellenőrizhető módszer” – de őszintén, a 30 dokumentumos fő vizsgálat
fényében:

1. **A naiv RAG törékeny minden modellnél** (E0: PULI 0,28; Qwen 0,64; Gemma 0,72), mert a
   lekérdezése feladatleírás („10 feleletválasztós kérdés…”), és a szemantikus darabolás rövid,
   tartalom nélküli darabokat is létrehoz, amelyekhez ez a lekérdezés a legközelebb áll.
2. **A vizsgaterv (tervezés) minden modellnél jelentősen javít** a naiv RAG-hoz képest
   (PULI +0,26, Holm-korrigált p < 0,001; Gemma +0,23, p = 0,002; Qwen +0,24, 6 dok., nem szign.).
3. **A módszer haszna a modell képességével csökken.** Gyenge modellnél (PULI) a teljes
   módszer (E2) jóval jobb, mint a teljes dokumentumos prompt (0,67 vs 0,41, p < 0,001), és az
   ellenőrzés is számít (+0,13). Közepes modellnél (Qwen, 6 dok.) a teljes módszer 0,96 vs 0,83.
   Erős helyi modellnél (Gemma 3 12B) a teljes dokumentumos prompt is 0,96, az E2 0,95 – nincs
   különbség, és az ellenőrzés sem javít (+0,01, n. sz.).
4. **A modellválasztás nagyobb hatású, mint bármely komponens.** Ugyanaz az E2: PULI 0,67 vs
   Gemma 0,95. A magyarra továbbtanított PULI-LlumiX egy hívásban átlagosan 1,8 kérdést ad a kért
   10 helyett (formai megfelelés 1 %), gyakran szivárogtat és nem kérdő törzset ír: a magyar
   nyelvi továbbtanítás nem pótolja az utasításkövetést.
5. **A Mimir hozzáadott értéke erős modell mellett is megmarad**, de máshol van: forráshivatkozás
   kérdésenként (ellenőrizhetőség, P1), Bloom-szint- és darabszám-kiosztás (P2), robusztusság a
   darabolással szemben, helyi futás (P3–P4). Ezt nem szabad elhallgatni, és nem szabad túlállítani.
6. **Hardver – két fogyasztói szint:** Qwen2.5-7B ≈ 4,8 GiB, PULI 8B ≈ 5,5 GiB (Ollama szerint)
   → **8 GB-os kártya** (a pilot egy RTX 3070 Ti-n futott); Gemma 3 12B ≈ 7,8 GiB + az asztali
   környezet 1,6–1,9 GiB-ja → **12 GB-os kártya** (pl. RTX 3060 12 GB, RTX 4070). Mindkettő
   fogyasztói GPU. A cím és a beküldött absztrakt csak „fogyasztói GPU”-t mond, ez marad.
   A szövegben a „8 GB” helyett: „fogyasztói GPU (8–12 GB)”; a „8 GB-on is fut” csak a 7–8B
   modellekre állítható. Üzenet: 8 GB-on a módszer adja a minőséget, 12 GB-on a modell, és a
   módszer az ellenőrizhetőséget és a robusztusságot.
7. **Mérési tanulságok:** szivárgás (Goodhart, a pilotból), csendes tartalékágak (E2x: a
   Llama-ellenőrző hívásai mindhárom futásban hibáztak, így az E2x csak szabályalapú ellenőrzést
   mért), a bíró és az ellenőrző kérdésenkénti egyezése a véletlen szintjén (κ ≈ 0–0,2).

## A vizsgálatok (így kell hivatkozni rájuk)

| Név a dolgozatban | Adat | Generátor | Dokumentum | Karok |
|---|---|---|---|---|
| **pilot** (2026. szept. 23.) | `tests/eval/results_pilot` | Qwen2.5-7B | 1 (hu-coffee) | 10 |
| **előzetes vizsgálat** (szept. 27–28.) | `tests/eval/results_qwen_2026-09` | Qwen2.5-7B + szervermodell | 6 közös (+3 a szerveres RAG-karoknál) | 14 |
| **fő vizsgálat** (okt. 7. – nov. 1.) | `tests/eval/results` | PULI-LlumiX 8B és Gemma 3 12B | 30 (24 magyar Wikipédia, 3 saját magyar, 3 angol OpenStax) | 11 helyi kar modellenként |

Bíró mindenhol: gpt-oss-120b, az egyetemi GenAI-szerveren, T = 0, „low” gondolkodás, a kérdés
saját forrásdarabjaival. Hardver: NVIDIA RTX A4500 (20 GB), egyetemi munkaállomás (XR Lab).
A szerverkarok (B-doc-S, E4, E4b) csak az előzetes vizsgálatban futottak.

## Egységes szóhasználat (BSc-olvasónak)

| Ezt írjuk | Nem ezt | Megjegyzés |
|---|---|---|
| konfiguráció (rövid jele: E0, E1 …) | kar | a kísérlet egy beállítása; első előfordulásnál magyarázni |
| kérdéshely | slot | a vizsgaterv egy pontja |
| generálási folyamat | csővezeték, pipeline | |
| bíró (értékelő nyelvi modell) | judge | első előfordulásnál: „a kérdéseket pontozó, független nyelvi modell (bíró)” |
| ellenőrző | verifier | a Mimir saját ellenőrző lépése |
| darab, darabolás | chunk | |
| naiv RAG | alapmódszer | E0 |
| teljes dokumentumos prompt | B-doc | B-doc-L helyi, B-doc-S szerver |
| szivárgás | leakage | a kulcs szinte szó szerint a törzsben |
| minőségi index (Q) | | (F + G + A + V) / 4 |

Modellnevek: **Qwen2.5-7B**, **PULI-LlumiX 8B** (a NYTK Llama-3.1 alapú, magyarra továbbtanított
modellje), **Gemma 3 12B**, **gpt-oss-120b** (bíró), „szervermodell” (az egyetemi GenAI-szerver
nagy Qwen-modellje). Mindegyik 4 bites (Q4_K_M) kvantálással fut az Ollamán.

## LaTeX-konvenciók

- Makrók: `\Mimir{}`, `\arm{E2}` (konfiguráció neve), `\code{...}`; magyar névelő a
  hivatkozás előtt: `\Az{\ref{tab:x}}.~táblázat`, `\az{\ref{sec:y}}.~szakasz`.
- Ábrák: `figures/` mappa; diagramok a `diagrams/*.mmd` forrásból renderelt `figures/d*_*.pdf`,
  adatábrák a `tdk/elemzes/abrak.py`-ból generált `figures/f*_*.pdf`.
- Megtartandó címkék (más fejezetek hivatkoznak rájuk): `ch:bevezetes`, `ch:szakirodalom`,
  `ch:modszer`, `ch:kiertekeles`, `ch:eredmenyek`, `ch:diszkusszio`, `ch:osszefoglalas`,
  `sec:irod-res`, `sec:architektura`, `sec:zero`, `sec:vram`, `sec:darabolas`, `sec:blueprint`,
  `sec:verifier`, `sec:graf`, `sec:karok`, `sec:mutatok`, `sec:biro`, `sec:oktatoi`,
  `sec:statisztika`, `sec:adatkeszlet`, `sec:vizsgalatok`, `sec:szivargas`, `eq:vram`,
  `eq:qindex`, `h:terv`, `h:verif`, `h:lefed`, `h:helyi`, `h:meres`, `tab:checks`, `tab:karok`.
- Táblázat: `booktabs`, `\small`, felirat a táblázat fölött; ábra: felirat alatta.
- Csak a `references.bib`-ben meglévő kulcsot szabad idézni; új forrás csak valós,
  ellenőrzött adatokkal kerülhet be.

## Ábrák (a fájlnevek rögzítettek)

Diagramok (mermaid):
- `figures/d1_architektura.pdf` – szolgáltatások és adatfolyam (3. fejezet)
- `figures/d2_folyamatok.pdf` – naiv RAG vs. tervezett folyamat (3. fejezet)
- `figures/d3_ellenorzo.pdf` – az ellenőrző lánc visszacsatolással (3. fejezet)
- `figures/d4_kiertekeles.pdf` – egy teszt lépései (4. fejezet)
- `figures/d5_kiserleti_terv.pdf` – a konfigurációk egytényezős fája (4. fejezet)

Adatábrák (matplotlib):
- `figures/f1_rangsor.pdf` – Q konfigurációnként és modellenként, 95 % CI
- `figures/f2_lepesek.pdf` – E0 → E1 → E2 és B-doc-L modellenként
- `figures/f3_dokumentumok.pdf` – a dokumentumonkénti Q eloszlása (robusztusság)
- `figures/f4_minoseg_ido.pdf` – minőség és futási idő
- `figures/f5_forrasok.pdf` – Q forrásonként (saját magyar / magyar Wikipédia / angol)
