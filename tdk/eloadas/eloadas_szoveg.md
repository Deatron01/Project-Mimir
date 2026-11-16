# A TDK-előadás szövege szóról szóra

Ez a fájl az előadás diák szerinti szövege. A `build_template_deck.py` ebből tölti fel a PowerPoint
jegyzeteit, és a szöveg hosszából becsüli az időt (kb. 110 szó/perc). Ha itt átírsz valamit, futtasd
újra a szkriptet: `python build_template_deck.py`.

Felosztás: **Hindulák Bálint** 1–5. dia · **Nagy István Bence** 6–11. dia · **Szegedi Achilles Károly** 12–16. dia.

## 1. dia — Hindulák Bálint

Tisztelt Bizottság, kedves Hallgatóság! Hindulák Bálint vagyok, a társaim Nagy István Bence és Szegedi
Achilles Károly, a konzulensünk Hartveg Ádám. A dolgozatunk azt vizsgálja, hogyan lehet egy átlagos,
otthoni videokártyán, helyben futó kis nyelvi modellel megbízható feleletválasztós vizsgát generálni, és
mitől függ, hogy ez sikerül-e.

## 2. dia — Hindulák Bálint

Az előadás a dolgozat szerkezetét követi. Először a problémát, az elméleti hátteret és a módszert mutatom
be. Utána Bence ismerteti a kísérleteket és az eredményeket, végül Achilles a következtetéseket és a
javaslatokat.

## 3. dia — Hindulák Bálint

Kezdjük a mai gyakorlattal. Az oktató feltölti a jegyzetét egy felhős csevegőasszisztensbe, és kér tőle
tíz feleletválasztós kérdést. Ez kényelmes, de négy gyengesége van. Egy: senki nem ellenőrzi, hogy a
megjelölt helyes választ a forrás tényleg alátámasztja-e. Kettő: a darabszám és a nehézség csak kérés,
a modell nem köteles betartani. Három: a tananyag egy külső szolgáltatóhoz kerül, ez adatvédelmi kérdés.
Négy: a teljes jegyzet egyben csak egy nagy, távoli modellbe fér bele. A harmadik és a negyedik pont
ütközik: helyben futtatva megoldódna az adatvédelem, de a kis modellek éppen a hosszú, egylépéses
feladatban gyengék. Ebből három kutatási kérdést, vagyis célkitűzést fogalmaztunk meg. Az első: jobb vizsgát
ad-e, ha a feladatot lépésekre bontjuk, minden kérdést a forrásához kötünk és ellenőrzünk, mint ha a
modell mindent egyetlen kérésben kap meg? A második: mennyit ér, és mennyibe kerül az egyes lépés, vagyis
a terv, az ellenőrző, a fogalomgráf, a keresés és a darabolás? A harmadik: mennyire közelíti meg egy
8–12 gigabájtos kártyán futó kis modell a nagy, szerveren futó modellt?

## 4. dia — Hindulák Bálint

A szakirodalmat öt területen, 101 hazai és nemzetközi forrással dolgoztuk fel. Három tanulságot emelek
ki. Egy: még a nagy modellek kérdései között is van hibás, a GPT-4 kérdéseinek közel 5%-ában több
helyes válasz is volt. Kettő: a visszakereséses generálás minőségét erősen befolyásolja, hogy mivel keresünk,
és hogyan daraboljuk a szöveget. Három: a modell külső információ nélkül alig tudja kijavítani a saját
hibáit. A kutatási rés: tudomásunk szerint nincs olyan nyílt rendszer, amely tervvel, kérdésenkénti
forrással és ellenőrzéssel, otthoni videokártyán generálna vizsgát, és magyar nyelvű kiértékelés sincs.

## 5. dia — Hindulák Bálint

Nézzük a módszert. Felül az alapvonal, a naiv RAG látható. A rendszer darabokra vágja a dokumentumot, a
keresés kérdése maga a feladat, vagyis „tíz feleletválasztós kérdés”. A modell megkapja a három
legközelebbi darabot, és egyetlen hívásban megírja az egész vizsgát. Alul a mi módszerünk. Először egy
vizsgaterv rögzíti minden kérdéshelyre, melyik fogalomról, milyen típusú és milyen Bloom-szintű kérdés
készüljön. Ezután minden kérdéshelyre külön keresünk, a tervezett fogalommal. A modell egyszerre csak egy
kérdést ír, és meg kell neveznie a forrásdarabot. Végül egy ellenőrző lánc vizsgálja a kérdést: előbb olcsó
szabályok, majd egy nyelvi modell nézi meg, hogy a forrás alátámasztja-e a választ. Ha hibát talál,
visszajelzéssel új kísérlet jön. A szerkezetről tehát program dönt, nem a modell, a végső döntés pedig
mindig az oktatóé. Átadom a szót Nagy István Bencének.

## 6. dia — Nagy István Bence

Köszönöm. A méréshez saját, nyílt kiértékelő keretrendszert építettünk. 30 dokumentumon dolgoztunk,
27 magyar és 3 angol szövegen, 14 konfigurációval. Minden konfiguráció pontosan egy
tényezőben tér el a referenciájától, így minden lépés hatása külön mérhető. Három helyi modellt
vizsgáltunk, és összesen több mint 11 000 kérdést pontoztunk. A fő mutató a minőségi index, 0 és 1 között. Ez négy arány átlaga: hibátlan-e a vizsga formája, igazolja-e a forrás a helyes választ,
kitalálja-e egy független modell a választ a kulcs ismerete nélkül, és tényleg hibásak-e a rossz válaszok.
A pontozást egy más modellcsaládba tartozó nagy modell, a bíró végzi, a bírót pedig kilenc oktató vak
értékelésével ellenőriztük. A konfigurációkat dokumentumonként, párosan hasonlítjuk össze. Mivel sok
összevetést végzünk, a véletlen is adhat „szignifikáns” eredményt; ezt szűri a Holm-korrekció. A
p-értékeket sorba rendezzük, a legkisebbet az összevetések számával szorozzuk, a következőt eggyel
kevesebbel, és így tovább, és csak az számít szignifikánsnak, ami ezután is 0,05 alatt
marad. Öt hipotézist vizsgáltunk. Az első: a vizsgaterv a naiv RAG-hoz képest több forrással igazolt
kérdést ad, és jobban lefedi a dokumentumot. A második: az ellenőrző lánc ezen tovább javít, és az ítélete
egyezik a bíróéval. A harmadik: ha a modell a teljes dokumentumot egyben kapja, a kérdései a dokumentum
kisebb részét fedik le. A negyedik: a helyi kis modell a módszerrel megközelíti a szervermodellt, a
minőségi indexben 0,1-nél kisebb különbséggel. Az ötödik: a bíró megbízhatóan egyezik az
oktatókkal, vagyis a Krippendorff-féle alfa legalább 0,667.

## 7. dia — Nagy István Bence

A legfontosabb eredmény a vizsgaterv hatása. Az ábrán a minőségi index látható a fő vizsgálat két
modelljén. A naiv RAG-hoz képest a vizsgaterv a PULI-nál 0,28-ról 0,54-re, a Gemmánál 0,72-ről 0,95-re javított. A PULI-nál
27, a Gemmánál 22 dokumentumon lett jobb, és a különbség Holm-korrekció után is
szignifikáns. A Qwennél, az előzetes vizsgálat hat dokumentumán, ugyanezt az irányt láttuk. A haszon
viszont a modelltől függ. A gyenge PULI-nál a teljes módszer 0,67-et ér el, míg ha az
egész dokumentumot egyben kapja, csak 0,41-et. Az erős Gemmánál viszont a teljes
dokumentumos prompt is 0,96. Ott a módszer már nem az átlagos minőséget emeli, hanem
azt adja, hogy minden kérdés forrása ellenőrizhető.

## 8. dia — Nagy István Bence

Miért gyenge a naiv RAG? Nem a keresővel van baj: ha tartalmi kérdéssel keresünk, a jó darab az esetek
86%-ában az első három találat között van. A baj a lekérdezés: az, hogy „tíz
feleletválasztós kérdés, könnyű”, semmit nem mond a tartalomról. A szemantikus darabolás ráadásul rövid,
tartalom nélküli darabokat is vág, és a lekérdezés éppen ezekhez van a legközelebb. Így születnek az
ilyen kérdések: „Mi a nehézségi szint a vizsgának?” Rögzített, 800 karakteres darabokkal ugyanez a
naiv RAG a Gemmánál 0,72-ről 0,97-re javul. A PULI-nál viszont ez
sem segít.

## 9. dia — Nagy István Bence

A táblázat az előre rögzített hat összevetést mutatja, 30 dokumentumon. A tervezés és a teljes
módszer mindkét modellnél szignifikánsan javít. Az ellenőrző lánc a PULI-nál 0,13-at
hoz, de Holm-korrekció után ez nem szignifikáns, a Gemmánál pedig gyakorlatilag nulla. Érdekes, hogy a
csak szabályalapú ellenőrzés ugyanannyit ér, mint a teljes, vagyis a lánc haszna a szabályokból jön, nem
a nyelvi modellből. A fogalomgráf és a hibrid keresés nem érte meg a többletköltséget.

## 10. dia — Nagy István Bence

Hasonlítsuk össze a modelleket ugyanazon a hat dokumentumon. A sorrend minden konfigurációban ugyanaz:
a Gemma a legjobb, utána a Qwen, végül a PULI. Ugyanaz a teljes módszer a PULI-val 0,72-t, a Gemmával 0,97-et ér el, tehát a modellválasztás többet számít, mint
bármelyik komponens. Meglepő, hogy a magyarra továbbtanított PULI a magyar szövegeken is a leggyengébb.
Az ok az utasításkövetés: egy hívásban átlagosan 1,8 kérdést ír a kért tíz helyett, egy hívásban a
vizsgáknak csak 1–6%-a hibátlan formájú, és ellenőrzés nélkül a kérdések 34%-a elárulja a választ. A modell a Llama magyar továbbtanítása, utólagos utasításhangolás nélkül,
ezért a következtetésünk csak erre a változatra érvényes. Memóriában a Qwen és a PULI elfér egy 8, a Gemma egy 12 gigabájtos kártyán.

## 11. dia — Nagy István Bence

Végül azt ellenőriztük, mennyire bízhatunk a bíróban. Kilenc oktató értékelt vakon 60 kérdést,
ugyanazzal a szempontrendszerrel, mint a bíró. A rangsor egyezik: az oktatók szerint is a Gemma a
legjobb és a PULI a leggyengébb, a hat konfiguráció sorrendje 0,71-es korrelációval
egyezik. A helyességen a bíró és az oktatók egyezése 0,68, ez éppen eléri az elvárt
küszöböt, miközben az oktatók egymással is csak 0,47-tel egyeztek. A bíró viszont
engedékenyebb: a kérdések 70%-át használná fel, az oktatók csak 55%-át. Ezért a
bíró számait összevetésre használjuk, abszolút minőségként felső becslésnek tekintjük. Átadom a szót
Szegedi Achilles Károlynak.

## 12. dia — Szegedi Achilles Károly

Köszönöm. Összefoglalom, mi lett a hipotézisekkel. Az első igazolást nyert: a vizsgaterv mindkét
modellnél jobb vizsgát adott, mint a naiv RAG, és ez a szigorított próbán is megállt. A második nem
igazolódott: az ellenőrző lánc után nem lett több forrással igazolt kérdés, és az ellenőrző ítélete csak
a véletlen szintjén egyezik a bíróéval. A harmadik sem: a teljes dokumentumot kapó modell ugyanakkora
részt fed le a dokumentumból, mint a módszerünk. A negyedik igazolást nyert: a 8 gigabájtos kártyán
futó Qwen a módszerrel elérte a szervermodell szintjét. Az ötödik részben igazolódott: a bíró jól
rangsorol, és a helyességen eléri az elvárt egyezést, a többi szempontban viszont nem.

## 13. dia — Szegedi Achilles Károly

Négy újszerű eredményt emelnénk ki. Az első maga a módszer: tervezésvezérelt, forráshivatkozásos
generálás, amely egy 8–12 gigabájtos kártyán is fut. A második a nyílt kiértékelő
keretrendszer. Tudomásunk szerint ez az első rendszerszintű magyar nyelvű kiértékelés ebben a témában. A
harmadik a naiv RAG kudarcának magyarázata: a feladatleírás mint lekérdezés és a túl rövid darabok együtt
vezetnek tartalom nélküli kérdésekhez. A negyedik, hogy a lépésekre bontás haszna a modelltől függ: gyenge
modellnél nélkülözhetetlen, erősnél az ellenőrizhetőséget adja.

## 14. dia — Szegedi Achilles Károly

Négy következtetést vonunk le. Egy: a minőséget elsősorban a választott modell és a keresés lekérdezése
határozza meg, nem egy-egy komponens. Kettő: az ellenőrző lánc javítja a vizsgát, mert kiszűri a hibás
kérdést és új kísérletet kér, de a kérdésenkénti jelzése nem ítélet, csak figyelmeztetés az oktatónak.
Három: a mérést magát is ellenőrizni kell. Jobb oldalon három olyan hiba látható, amely hihető számokat
adott volna: a pilotban a kérdések 20%-a elárulta a választ, a bíró mégis ötöst adott rájuk; az
ellenőrző és a bíró kérdésenként csak véletlenszerűen egyezett; és a Wikipédia-kérdéseknek csak
42–55%-a kapott bírói ítéletet. Négy: a bíró rangsorolásra alkalmas, de az oktatók
szigorúbbak nála.

## 15. dia — Szegedi Achilles Károly

A mérésekből három módszertani javaslat következik. Egy: a keresés kérdése tartalmi legyen, például a
vizsgaterv fogalmai, és ne maga a feladatleírás; a darabolásnál pedig kell egy minimális darabméret. Kettő:
minden kérdés hivatkozzon a forrására, és az ellenőrzés gerincét olcsó szabályok adják; a nyelvi modell
jelzése csak figyelmeztetés, a döntés az oktatóé. Három: egy nyelvi modell bíróként rangsorolásra
használható, abszolút minőségre nem, ezért oktatói mintán kalibrálni kell. Összefoglalva egy mondatban: otthoni videokártyán
futó kis modellekkel a vizsgakérdések minőségét elsősorban a választott modell és a keresés lekérdezése
határozza meg; a feladat lépésekre bontása gyenge modellnél nélkülözhetetlen, erős modellnél pedig az
ellenőrizhetőséget adja.

## 16. dia — Szegedi Achilles Károly

Köszönjük a megtisztelő figyelmet! Szívesen válaszolunk a Bizottság kérdéseire.

## 17. dia — tartalék

Ide kerülnek a bírálatokban szereplő kérdések és a rövid válaszok, ha a bírálatok megérkeztek. Ki
válaszol: mérés, statisztika és eredmények – Nagy István Bence; szakirodalom, a módszer, jogi és etikai
kérdések – Hindulák Bálint; ajánlások és további munka – Szegedi Achilles Károly.
