# Érdekmérlegelési teszt

0.1-es verzió (tervezet, 2026. szeptember 24.) · English version: [lia.en.md](lia.en.md)

> **Jogi átvizsgálásra szánt tervezet.** A GDPR 6. cikk (1) bekezdés f) pontja szerint jogszerű az adatkezelés, ha az adatkezelő jogos érdekéhez szükséges, és az érintettek érdekei vagy jogai nem élveznek elsőbbséget. Ez a dokumentum a háromlépcsős tesztet (cél, szükségesség, mérlegelés) végzi el az [adatkezelési nyilvántartás](compliance.hu.md#3-adatkezelési-nyilvántartás-30-cikk) jogos érdeken alapuló három tevékenységére: **4. MI működési napló**, **5. biztonsági naplózás** és **6. kapcsolatfelvétel**. Rögzíti a tiltakozási jogot is (21. cikk). Az adatkezelés változásakor, de legalább évente felül kell vizsgálni.

Adatkezelő: [KITÖLTENDŐ] · Készítette: [KITÖLTENDŐ] · Jóváhagyta (adatvédelmi tisztviselő / jogász): [KITÖLTENDŐ]

## Összefoglaló

| # | Tevékenység | Jogos érdek | Szükséges? | Mérlegelés | Eredmény |
| --- | --- | --- | --- | --- | --- |
| 4 | MI működési napló | Egy MI-rendszer minősége, nyomonkövethetősége és hibakeresése; az MI-rendelet által elvárt emberi felügyelet és nyilvántartás igazolása | Igen: feladatonkénti nyilvántartás nélkül a hibás vagy nem biztonságos kimenet nem vezethető vissza és nem javítható | Álnevesített feladatazonosító, tartalom nélkül (csak SHA-256 lenyomatok és hosszak), 30 nap | **Megfelel** |
| 5 | Biztonsági naplózás | A szolgáltatás biztonsága és elérhetősége; visszaélések és támadások észlelése | Igen: a támadásokat és hibákat a hozzáférési naplók alapján lehet felderíteni | Rövidített IP, paraméterek nélkül, 14 nap; bármely weboldal látogatója számít rá | **Megfelel** |
| 6 | Kapcsolatfelvétel | A hozzánk érkező megkeresések megválaszolása | Igen: cím és üzenet nélkül nem lehet válaszolni | Az érintett maga adja meg erre a célra; lezárás után 1 évig | **Megfelel** |

## 4. MI működési napló

**Célteszt.** Az üzemeltető nagy nyelvi modellel vizsgakérdéseket generáló rendszert működtet. Tudnia kell, melyik modell és promptverzió készítette az eredményt, hogyan értékelte a minőségellenőrzés és mikor, hogy a hibás kimenetet ki tudja vizsgálni és javítani, és igazolni tudja a rendszer felügyeletét (az MI-rendelet átláthatósági és nyilvántartási kötelezettségei, [megfelelőségi dokumentáció 11. pont](compliance.hu.md#11-kapcsolódás-az-mi-rendelethez)). Ez valós, fennálló és jogszerű érdek.

**Szükségességi teszt.** A napló a legkevésbé beavatkozó megoldás: nem tárolja sem a dokumentumot, sem a promptot, sem a kimenetet, csak ezek SHA-256 lenyomatát és hosszát, valamint a feladatazonosítót, a modell nevét, a promptverziót, a minőségi pontszámot és az időpontot. A lenyomatokból megállapítható, hogy két feladat ugyanazt a bemenetet kapta-e, a bemenet megőrzése nélkül. Feladathoz nem köthető napló a hibakereséshez nem lenne elég.

**Mérlegelés.**

- *Az adatok jellege:* álnevesített (feladatazonosító); dokumentumtartalom nélkül; különleges adat nincs.
- *Észszerű elvárások:* egy MI-szolgáltatás felhasználója számít arra, hogy az üzemeltető figyeli a minőséget; az [adatkezelési tájékoztató](privacy-notice.hu.md) 3. pontja leírja a naplót.
- *Hatás:* nagyon alacsony. A lenyomatokból a szöveg nem állítható vissza; a naplót nem használjuk személyekre vonatkozó döntéshez vagy profilalkotáshoz.
- *Garanciák:* 30 napos megőrzés automatikus törléssel (`AUDIT_RETENTION_DAYS`), hozzáférés csak az üzemeltető csapatának, a korábbi, tartalmat is tároló sorok kiürítve (GDPR-01).

**Eredmény:** az érintettek érdekei nem élveznek elsőbbséget. Az adatkezelés a fenti garanciákkal folytatható.

## 5. Biztonsági naplózás

**Célteszt.** A szolgáltatás és a felhasználói adatok biztonsága (GDPR 32. cikk) megköveteli a támadások, visszaélések és hibák észlelését. A (49) preambulumbekezdés a hálózat- és információbiztonságot kifejezetten jogos érdeknek tekinti.

**Szükségességi teszt.** A támadások és hibák felderítésének bevett eszköze a hozzáférési napló. Adattakarékos: az IP-cím rövidített, a kérés paramétereit nem naplózzuk, a kérések törzsét soha.

**Mérlegelés.**

- *Az adatok jellege:* rövidített IP-cím, időpont, útvonal paraméterek nélkül, állapotkód, válaszidő.
- *Észszerű elvárások:* a látogatók számítanak arra, hogy egy weboldal alapvető biztonsági naplót vezet; a tájékoztató felsorolja.
- *Hatás:* alacsony; a rövidített IP-ből az azonosítás valószínűtlen; a naplót nem kapcsoljuk össze más adattal, profilalkotásra nem használjuk.
- *Garanciák:* legfeljebb 14 napos megőrzés, hozzáférés csak az üzemeltető csapatának, a Cloudflare a saját adatfeldolgozói szerződése és érvényes továbbítási eszköz alapján kezeli a hálózati adatokat.

**Eredmény:** az érintettek érdekei nem élveznek elsőbbséget.

## 6. Kapcsolatfelvétel

**Célteszt.** A hozzánk forduló személyek megkeresésének megválaszolása jogos érdek (a szolgáltatás igénybevételével kapcsolatos megkeresésnél pedig szerződéskötést megelőző lépés, 6. cikk (1) b) pont).

**Szükségességi teszt.** A válaszhoz a küldő neve, e-mail-címe és üzenete kell; mást nem kérünk.

**Mérlegelés.**

- *Az adatok jellege:* amit az érintett elküldeni választott; kérjük, hogy érzékeny adatot ne írjon.
- *Észszerű elvárások:* aki ír nekünk, számít arra, hogy elolvassuk, válaszolunk, és az ügy lezárásáig megőrizzük.
- *Hatás:* alacsony.
- *Garanciák:* törlés a megkeresés lezárása után 1 évvel, hozzáférés csak a megkereséseket kezelő munkatársaknak.

**Eredmény:** az érintettek érdekei nem élveznek elsőbbséget. Megjegyzés: a kapcsolatfelvételi űrlap még nincs bekötve ([megfelelőségi dokumentáció, megőrzési rend](compliance.hu.md#4-megőrzési-rend-és-törlési-mechanizmusok)); bekötéskor ezt az értékelést újra át kell nézni.

## Tiltakozási jog (21. cikk)

Az érintett a jogos érdeken alapuló adatkezelés ellen bármikor tiltakozhat a tájékoztató 1. pontjában megadott címen. Tiltakozás esetén az üzemeltető az érintett adatait az adott tevékenységhez nem kezeli tovább, kivéve, ha olyan kényszerítő erejű jogos okot igazol, amely elsőbbséget élvez az érintett érdekeivel szemben, vagy az adat jogi igény érvényesítéséhez szükséges. Az 5. tevékenységnél a tiltakozásra általában a biztonsági szükséglet ismertetésével válaszolunk, mert a napló rövid életű és adattakarékos; a döntést az érintetti kérelmek nyilvántartásában rögzítjük ([megfelelőségi dokumentáció 9. pont](compliance.hu.md#9-az-érintetti-kérelmek-kezelése)).

## Felülvizsgálati napló

| Dátum | Változás | Ki |
| --- | --- | --- |
| 2026-09-24 | Első tervezet | [KITÖLTENDŐ] |
