# A TDK dolgozat felépítése – írási terv (2026. november, 3. változat)

## 3. változat: csak a tudományos rész (ez az érvényes, felülírja a lenti 2. változatot ott, ahol eltér)

A 2. változat teljes, 97 oldalas szövege (rendszerállapot, megfelelési megvalósítás, fejlesztési
döntés és ütemterv) a repó gyökerében, a `publikacio/` mappában megmaradt. A TDK-változat **kutatási
dolgozat**, nem fejlesztési napló: a módszer, a kísérletek, az eredmények és azok tudományos
értékelése. **Cél: kb. 42–45 oldal főszöveg** (az előlap, az irodalomjegyzék és a függelék ezen
felül; a teljes PDF kb. 65 oldal alatt).

**Ami kimarad a TDK-ból** (megvan a `publikacio/` változatban): a szolgáltatások architektúrája és
nevei (Wellspring, RuneCarver, Bifrost, Heimdall, The Forge, Skald), az nginx, a feladatsor, a
`BackgroundTasks`, a frontend (legacy/v1 mód, ál-backend), a „fejlesztési fázis / éles útvonal”
keretezés, az adatfajták életciklusa táblázat, a megfelelési táblázat (`tab:megfeleles`), a
szerkesztő képernyőképe, az architektúra-ábra, a fejlesztési ütemterv, a „mit építünk be a
Bifrostba” jellegű mérnöki teendők, a docker-alapú telepítési lépések.

**Ami marad:** a probléma és a kutatási kérdések; a szakirodalom (a jogi keret tömörítve, kb. 1,5
oldal, mert a P3 problémát és a helyi futtatás indokát adja); a javasolt **generálási módszer** mint
kutatási hozzájárulás (darabolás, vizsgaterv és Bloom-kiosztás, kérdéshelyenkénti keresés,
forráshoz kötött generálás, ellenőrző lánc, fogalomgráf), a helyi futtatás memóriamodellje
(röviden), és egy rövid bekezdés a tervezési elvekről (helyi futtatás, adatmegőrzés nélküli
feldolgozás, kötelező oktatói jóváhagyás – elvként, nem megvalósítási részletként); a kísérleti
módszertan; az eredmények; a tudományos értékelés (hipotézisek, irodalmi összevetés, mikor éri meg a
módszer, mérési tanulságok, érvényesség) és **rövid gyakorlati következmények** (melyik konfiguráció
ajánlott GPU-szintenként – ez mérési eredmény, nem fejlesztési terv).

A módszert „kutatási prototípusként, a nyílt kiértékelő keretrendszerben megvalósítva” említjük; a
„fejlesztési fázis”, „éles útvonal”, „beépítés” kifejezéseket kerüljük.

| Fejezet | Fájl | Cél oldal | Felelős |
|---|---|---|---|
| Összefoglaló, rövidítések | `osszefoglalo.tex`, `jelolesek.tex` | 1 + 1 | Keret |
| 1. Bevezetés | `bevezetes.tex` | 3 | Keret |
| 2. Szakirodalom | `szakirodalom.tex` | 12 | Irodalom |
| 3. A javasolt generálási módszer | `modszertan.tex` | 7 | Rendszer |
| 4. Kísérleti módszertan | `kiertekeles.tex` | 5,5 | Rendszer |
| 5. Eredmények: a módszer komponensei | `eredmenyek.tex` | 8,5 | Eredmények |
| 6. Eredmények: a generátormodellek | `modellek.tex` | 4 | Eredmények |
| 7. Az eredmények értékelése | `diszkusszio.tex` | 5 | Döntés |
| 8. Összefoglalás | `osszefoglalas.tex` | 1,5 | Keret |
| Függelék | `fuggelek_modszer.tex` (Rendszer), `fuggelek_eredmeny.tex` (Eredmények), `fuggelek.tex` (Keret) | – | |

**Megszűnő címkék** (senki ne hivatkozzon rájuk): `sec:megvalositas`, `sec:megfeleles`,
`tab:megfeleles`, `tab:eletciklus`, `app-eletciklus`, `fig:architektura`, `fig:szerkeszto`,
`tab:celok`. **Megmaradó, de rövid** szakaszok (a címke marad): `sec:architektura` (tervezési elvek),
`sec:zero` (helyi futtatás és adatkezelés, 1 bekezdés), `sec:vram`, `sec:felugyelet` (emberi
felügyelet mint elv), `sec:dontes` és `tab:dontes` (a 7. fejezetben „Gyakorlati következmények”).

Ez a fájl a fejezetek íróinak (embernek és agentnek) közös útmutatója. Minden szám forrása
`tdk/elemzes/szamok.md` / `szamok.json` (generálja: `tdk/elemzes/elemzes.py`). Számot csak onnan
szabad átvenni; kerekítés: két tizedes (0,95), ráták egész százalékban (86 %), tizedesvessző.
A `szamok.json`-ban a `szamok.md`-nél több mező van (pl. `judge_review_coverage`, `recall@3`,
`stem_len`, `Q_pooled`), ezek is használhatók.

## Keret: mit állít a dolgozat

A \Mimir{} **fejlesztési fázisban lévő** rendszer, nem kiadott termék. Az éles szolgáltatások ma a
naiv RAG-ot (E0) futtatják; a tervezett folyamat (vizsgaterv, ellenőrző lánc, forráshivatkozás) a
kiértékelő keretrendszerben (`tests/eval`, a fő vizsgálat kódja `tests/new eval`) készült el. A
dolgozat célja: **mérésen alapuló döntés arról, melyik megoldás kerüljön be a rendszerbe**
(legjobb minőség, leggyorsabb, legrobusztusabb, GPU-szintenként). Ezt egyenesen ki kell mondani,
de nem bocsánatkérően: a keretrendszer saját, újszerű eszköz (NIK-lap 3. szempont).

**Gerincmondat (minden fejezet ezt szolgálja):**
„Fogyasztói GPU-n futó kis modellekkel a vizsgakérdések minőségét elsősorban a választott modell és
a visszakeresés lekérdezése határozza meg; a feladat lépésekre bontása gyenge modellnél
nélkülözhetetlen, erős modellnél pedig az ellenőrizhetőséget adja. Ezt egy saját, nyílt kiértékelő
keretrendszerrel, 30 dokumentumon és három modellen mértük, és ebből döntöttük el, mi kerül a
rendszerbe.”

**Három üzenet:**
1. A naiv RAG törékeny, konkrét okkal: a feladatleírás mint lekérdezés + a szemantikus darabolás
   rövid, tartalom nélküli darabjai (E0 vs E5c: Gemma 0,72 → 0,97; Qwen 0,64 → 0,86).
2. A módszer haszna a modelltől függ (PULI 0,28 → 0,67; Qwen 0,64 → 0,96; Gemma: a teljes
   dokumentumos prompt is 0,96, az E2 0,95, az E5c 0,97).
3. A mérés is eredmény: szivárgás, csendes tartalékágak, κ ≈ 0 az ellenőrző és a bíró között,
   forrásfüggő hiányzó bírói ítéletek.

## Szabályok, amelyeket minden író betart

- **Összevetés csak azonos dokumentumokon.** A három vizsgálat közötti összevetés a hat közös
  dokumentumon (`szamok.md` utolsó blokkja, `common6`) megengedett, és mindig ki kell írni, hogy
  azon készült. A „csak vizsgálaton belül hasonlítunk” mondatot ennek megfelelően kell átírni.
- **Futásidő csak relatív szorzóként** értelmezendő: ugyanazon a GPU-n az egyik konfiguráció hányszor
  lassabb a másiknál (pl. Gemma: E0 ≈ 1×, B-doc-L ≈ 1×, E5c ≈ 1×, E1 ≈ 5×, E2 ≈ 8,5×, E3 ≈ 10,6×).
  Abszolút perc mellékesen közölhető; a GPU típusa a szorzót érdemben nem változtatja.
- **Módszertani és modellértékelés külön** (5. és 6. fejezet). Egy modell kudarca (PULI) a 6.
  fejezetbe tartozik; az 5. fejezet a módszer lépéseinek hatását vizsgálja modellenként.
- **Nincs túlállítás.** Ha egy hatás nem szignifikáns, így írjuk; ha egy állítást nem mértünk (pl.
  hogy a tervezett folyamat nem függ a darabolástól), elvárásként fogalmazzuk.
- **Hivatkozás:** csak a `references.bib`-ben meglévő kulcs. Új forrást csak a szakirodalmi író
  vehet fel, és csak valós, ellenőrzött adatokkal (szerző, cím, év, kiadó/DOI/URL). Kitalált forrás
  nem kerülhet be; ha egy állításhoz nincs forrás, `\tbd{[forrás kell: …]}`.
- **Hiányzó adat** (pl. oktatói értékelés, szerzői adatok): `\tbd{[…]}` piros helyőrző.
- **Ismétlés kerülése:** egy szám részletesen egy helyen; máshol hivatkozás a táblázatra/szakaszra.
- Minden fejezet egy rövid bekezdéssel kezdődik (mit tud meg belőle az olvasó), és egy rövid
  tanulsággal zárul.

## Célkeret: kb. 55 oldal előlap + főszöveg (irodalomjegyzék és függelék ezen felül)

Ökölszabály: egy teljes szövegoldal ≈ 330 szó; egy közepes táblázat vagy ábra ≈ fél oldal.

| Fejezet | Fájl | Oldal | Felelős (agent) |
|---|---|---|---|
| Tartalmi összefoglaló | `fejezetek/osszefoglalo.tex` | 1 | Keret |
| Rövidítések | `fejezetek/jelolesek.tex` | 1 | Keret |
| 1. Bevezetés | `fejezetek/bevezetes.tex` | 3 | Keret |
| 2. Szakirodalom (+ hazai irodalom, + jogi keret) | `fejezetek/szakirodalom.tex` | 15 | Irodalom |
| 3. A rendszer jelenlegi állapota (+ megfelelés) | `fejezetek/modszertan.tex` | 9 | Rendszer |
| 4. Kiértékelési módszertan | `fejezetek/kiertekeles.tex` | 6 | Rendszer |
| 5. A módszerek kiértékelése | `fejezetek/eredmenyek.tex` | 9 | Eredmények |
| 6. A modellek kiértékelése | `fejezetek/modellek.tex` (új) | 5 | Eredmények |
| 7. Értékelés és döntés: mit építünk be | `fejezetek/diszkusszio.tex` | 6 | Döntés |
| 8. Összefoglalás és további munka | `fejezetek/osszefoglalas.tex` | 2 | Keret |
| Függelék (+ kötelező OTDK-elemek) | `fejezetek/fuggelek.tex` | – | Keret |

Az irodalomjegyzéket (`references.bib`) **csak az Irodalom agent** szerkeszti. A `main.tex`-et csak a
koordinátor szerkeszti. Senki nem futtat LaTeX-fordítást, teszteket, Ollamát vagy kiértékelő kódot.

## Fejezetenként mi kerül bele

**1. Bevezetés.** Motiváció, P1–P4, RQ1–3, H1–H5 (változatlan címkékkel), új bekezdés a fejlesztési
fázisról és a dolgozat céljáról (döntés). Hozzájárulások számozva; a keretrendszer mint saját
eszköz; a gerincmondat. A dolgozat felépítése a 8 fejezetre.

**2. Szakirodalom.** A meglévő anyag megmarad, de: (a) a tankönyvi részek (transzformer, BERT,
koszinusz) rövidülnek, a helyükre elemző összevetés kerül; (b) **hazai irodalom**: magyar
nyelvtechnológia (PULI-család, HuLU, MILQA, huBERT, MSZNY-cikkek), a NAIH MI-vel kapcsolatos anyagai,
hazai tudásmérés – csak ellenőrzött forrás; (c) új alfejezet **„Jogi keret: GDPR és MI-rendelet”**
(kb. 3 oldal): GDPR alapelvek (5. cikk), beépített adatvédelem (25.), adatfeldolgozó (28.),
biztonság (32.), DPIA (35.); Infotv.; MI-rendelet: kockázati osztályok, III. melléklet 3. pont
(oktatás), 4. cikk (MI-jártasság), 50. cikk (átláthatóság), emberi felügyelet, alkalmazási
határidők (ellenőrizni, mert az ütemezés változhatott); a Mimir besorolása (tanár által ellenőrzött
kérdésgenerálás: nem magas kockázatú; automatikus pontozás: az lenne). (d) A kutatási rés táblázata
marad, a „Nincs olyan nyílt rendszer” → „tudomásunk szerint”.

**3. A rendszer jelenlegi állapota.** Tervezési célok; architektúra **úgy, ahogy van**: a generálás a
Bifrost háttérfeladataként fut (FastAPI `BackgroundTasks`), a The Forge az audit naplót és a
feldolgozási sort kezeli; az éles útvonal ma naiv RAG, alapból az egyetemi GenAI-szervert hívja,
helyi tartalékkal, `LOCAL_ONLY` kapcsolóval csak helyi; a v1 szerkesztő (forráshivatkozással) a
frontend v1 API-szerződésén, fejlesztéskor ál-backenddel fut – a tervezett folyamat integrálása a
7. fejezet döntésén múlik. Memóriabecslés (változatlan). A generálási módszer (változatlan
tartalommal). **Új alfejezet: „Adatvédelem és MI-rendelet a megvalósításban”** (1,5 oldal) a
`docs/gdpr/compliance.hu.md` alapján: táblázat követelmény → megoldás → állapot (Megvalósítva /
Részben / Tervezett). A „zéró adatmegőrzés” pontosan: a vektortár a feladat végén törlődik
(`_purge_document_data`), a vázlat 60 percig él, a jóváhagyott vizsga beállítható ideig.

**4. Kiértékelési módszertan.** A keretrendszer mint saját eszköz; konfigurációk; a három vizsgálat;
mutatók; bíró; statisztika. Két kimondott szabály: azonos dokumentum, relatív időszorzó. A 4.3.
táblázat „Bírált kérdések” sora → „Pontozott kérdések”, mellé a bírói ítélettel rendelkezők aránya.

**5. A módszerek kiértékelése.** Pilot tanulságai (röviden); a fő vizsgálat összesített eredménye;
a komponensek hatása (tervezés, ellenőrzés, gráf, hibrid, vak próba); **darabolás és robusztusság**
(E0 vs E5a–c, a naiv RAG törékenységének oka); az ellenőrző működése; lefedettség, Bloom,
felhasználhatóság; **költség relatív szorzókkal**; a mérés megbízhatósága (hiányzó ítéletek
forrásonként!). Modellenként bontva, de a módszer szemszögéből.

**6. A modellek kiértékelése.** Qwen, PULI, Gemma azonos dokumentumokon (`common6`, és a 30 dokumentum
PULI–Gemma); a szervermodell a hat közös dokumentumon; a PULI kudarca (utasításkövetés; a
modellkártya szerint a Llama 3.1 8B **Instruct** továbbelőtanítása, utólagos utasítás-hangolás
nélkül; a következtetés erre a modellre szűkítve); memóriaigény és GPU-szintek (8 GB / 12 GB).

**7. Értékelés és döntés.** Hipotézisek értékelése (H2 a fő vizsgálatban nem támogatott);
**összevetés az irodalommal** (Huang: önellenőrzés; Qu: darabolás; Li: hosszú kontextus vs RAG;
Doughty/Wang: hibás kulcsok aránya; Zheng/Chiang: bíró); **döntési táblázat GPU-szintenként**
(legjobb / leggyorsabb / legrobusztusabb); mi kerül be (kérdésenkénti forráshivatkozás, szabályalapú
ellenőrzés, rögzített vagy minimális méretű darabolás, adaptív ellenőrzés), mi marad ki
(fogalomgráf, hibrid keresés); fejlesztési ütemterv; az érvényesség korlátai.

**8. Összefoglalás.** RQ-válaszok, további munka.

**Függelék.** Promptok, rubrika, paraméterek, reprodukálás (a fő vizsgálat kódja `tests/new eval`),
és a 38. OTDK Informatikai Szekció kötelező elemei: **rezümé** (800–2 500 karakter: indoklás,
módszerek, saját eredmények, következtetések, mindegyik ≥ 200 karakter; 5 kulcsszó, amely nincs a
címben), **MI-használati nyilatkozat** (eszközök, felhasználás módja, mely részeknél, milyen
mértékben), **eredménynyilatkozat** (2 000–4 000 karakter, saját vs. témavezetői eredmények;
személyes részek `\tbd`), **adatforrások és nyilvánosságuk**.

## A bírálati szempontok (amit minden író szem előtt tart)

ÓE NIK pontozás (60 pont): szerkesztés, stílus 5; irodalom 10 (hazai **és** külföldi, széles körű,
elemző); kidolgozás színvonala 15 (új eszköz); eredmények értékelése 15 (megalapozott, **irodalmi
adatokkal összevetve**, **továbbfejlesztésre utal**); gyakorlati alkalmazhatóság 10; összbenyomás 5.
OTDK (írásbeli 50 pont): újszerűség, tartalom, az eredmények igazoltsága, irodalom, forma,
tudományos érték és publikálhatóság.

## A vizsgálatok (így kell hivatkozni rájuk)

| Név a dolgozatban | Adat | Generátor | Dokumentum | Karok |
|---|---|---|---|---|
| **pilot** (2026. szept. 23.) | `tests/eval/results_pilot` | Qwen2.5-7B | 1 (hu-coffee) | 10 |
| **előzetes vizsgálat** (szept. 27–28.) | `tests/eval/results_qwen_2026-09` | Qwen2.5-7B + szervermodell | 6 közös (+3 a szerveres RAG-karoknál) | 14 |
| **fő vizsgálat** (okt. 7. – nov. 1.) | `tests/eval/results` | PULI-LlumiX 8B és Gemma 3 12B | 30 (24 magyar Wikipédia, 3 saját magyar, 3 angol OpenStax) | 11 helyi kar modellenként |

Bíró mindenhol: gpt-oss-120b, az egyetemi GenAI-szerveren, T = 0, „low” gondolkodás, a kérdés
saját forrásdarabjaival. A szerverkarok (B-doc-S, E4, E4b) csak az előzetes vizsgálatban futottak.

## Ismert javítandó pontok (az audit alapján)

- Bírói ítéletek lefedettsége forrásfüggő (Gemma E2: angol 100 %, saját magyar 87 %, Wikipédia 42 %;
  Gemma E0: 100 / 100 / 55 %; PULI E2 összesen 28 %, kb. 85 kérdés). A „független volt a forrástól”
  állítás hamis. Az érzékenységvizsgálat (Q_pooled) a Gemmánál és a PULI tervezett konfigurációinál
  ≤ 0,01; a PULI egyhívásosainál 0,03–0,08 (E5a, E5c 0,08).
- H2: a fő vizsgálatban az alátámasztottság mindkét modellnél csökkent (PULI 58 → 52 %, Gemma
  88 → 86 %), a Q-változás Holm után egyiknél sem szignifikáns → „nem támogatott a fő vizsgálatban”.
- E5c a Gemmánál a legjobb (0,97) és a leggyorsabb; a „vizsgaterv minden modellnél javít a naiv
  RAG-hoz képest” csak a szemantikus darabolású, 3 darabos E0-ra igaz. Az E1 és az E0 több
  tényezőben különbözik.
- „A tervezett folyamat nem függ a darabolástól” – nem mértük (az E5a–c csak az E0-t változtatta).
- A szervermodell a saját módszerünkkel (E4b) 0,99; a „Qwen elérte a szervermodellt” csak a
  teljes dokumentumos szerveres promptra (B-doc-S 0,95) igaz.
- 5.2. táblázat: a „Min.” oszlop a feliratban szerepel, a táblázatban nincs; a Perc/Hívás csak Gemma.
- Kisebb számok: Gemma E2 legrosszabb dokumentuma 0,799 és E2x 0,798 (nem „0,80 felett”); Gemma
  E1 angolon 0,916 (nem „0,92 felett”); sikertelen vizsgák 14–29 % (nem 15–29 %); PULI
  „felhasználnám” legfeljebb 38 % (E5a), nem 29 %; Bloom-egyezés 12–20 % (nem 16–20 %); Gemma
  lefedettség E1 0,425 → egységesen 43 %; Q4_K_M bit/súly egységesen „kb. 4,8”; GB/GiB egységes.
- „Az önpreferencia nem lép fel” → „csökkenti”.

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

Modellnevek: **Qwen2.5-7B**, **PULI-LlumiX 8B** (a NYTK Llama-3.1-8B-Instruct alapú, magyarra
továbbelőtanított modellje), **Gemma 3 12B**, **gpt-oss-120b** (bíró), „szervermodell” (az egyetemi
GenAI-szerver nagy Qwen-modellje). Mindegyik 4 bites (Q4_K_M) kvantálással fut az Ollamán.

## LaTeX-konvenciók

- Makrók: `\Mimir{}`, `\arm{E2}` (konfiguráció neve), `\code{...}`, `\tbd{...}`; magyar névelő a
  hivatkozás előtt: `\Az{\ref{tab:x}}.~táblázat`, `\az{\ref{sec:y}}.~szakasz`.
- Felirat: `\caption[rövid cím.]{teljes felirat}` – a rövid cím az első mondat, az kerül a jegyzékbe.
- Ábrák: `figures/` mappa; diagramok a `diagrams/*.mmd` forrásból renderelt `figures/d*_*.pdf`,
  adatábrák a `tdk/elemzes/abrak.py`-ból generált `figures/f*_*.pdf` (új ábrát nem generálunk).
- Fejezetcímkék: `ch:bevezetes`, `ch:szakirodalom`, `ch:modszer`, `ch:kiertekeles`,
  `ch:eredmenyek` (5. fejezet, a módszerek kiértékelése), `ch:modellek` (6., új),
  `ch:diszkusszio` (7., értékelés és döntés), `ch:osszefoglalas`.
- Megtartandó címkék (más fejezetek hivatkoznak rájuk): `sec:irod-res`, `sec:architektura`,
  `sec:zero`, `sec:vram`, `sec:darabolas`, `sec:csonkolt`, `sec:blueprint`, `sec:verifier`, `sec:graf`,
  `sec:felugyelet`, `sec:attekintes`, `sec:karok`, `sec:mutatok`, `sec:biro`, `sec:oktatoi`,
  `sec:statisztika`, `sec:adatkeszlet`, `sec:vizsgalatok`, `sec:pilot`, `sec:szivargas`,
  `sec:elozetes`, `sec:fo-vizsgalat`, `sec:fo-robusztus`, `sec:fo-puli` (a 6. fejezetbe kerül),
  `sec:fo-ellenorzo`, `sec:fo-eroforras` (a 6. fejezetbe kerül), `sec:fo-meres`,
  `sec:oktatoi-eredmeny`, `sec:hipotezis-ertekeles`, `sec:meres-tanulsag`, `sec:validitas`,
  `eq:vram`, `eq:qindex`, `h:terv`, `h:verif`, `h:lefed`, `h:helyi`, `h:meres`, `tab:checks`,
  `tab:karok`, `fig:lepesek`, `app-prompt`, `app-rubrika`, `app-reprodukcio`.
- Táblázat: `booktabs`, `\small`, felirat a táblázat fölött; ábra: felirat alatta.
- Fájlszerkesztés: Edit/Write eszközzel, nem `sed`-del (a sorvégek és az ékezetek miatt).

## Ábrák (a fájlnevek rögzítettek)

Diagramok: `d1_architektura` (3.), `d2_folyamatok` (3.), `d3_ellenorzo` (3.), `d4_kiertekeles` (4.),
`d5_kiserleti_terv` (4.). Adatábrák: `f1_rangsor` (5. vagy 6.), `f2_lepesek` (5.),
`f3_dokumentumok` (5.), `f4_minoseg_ido` (5.), `f5_forrasok` (5.). Képernyőkép: `k1_szerkeszto` (3.).
