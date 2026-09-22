# Mimir GDPR-megfelelőségi dokumentáció

1.0-s verzió (tervezet) · 2026. szeptember 22. · English version: [compliance.en.md](compliance.en.md)

Ez a belső dokumentáció tartalmazza mindazt, amire a Mimir üzemeltetőjének a GDPR (az (EU) 2016/679 rendelet), az Infotv. (2011. évi CXII. törvény) és az EU MI-rendelet átláthatósági kötelezettségei alapján szüksége van. A nyilvános szöveg az [adatkezelési tájékoztató](privacy-notice.hu.md). Minden elem jelölve van: **Megvalósítva**, **Részben megvalósítva** vagy **Tervezett**, a hozzá tartozó GitHub-issue számával.

> Ez mérnöki megfelelőségi tervezet, nem jogi tanácsadás. Éles használat előtt nézesse át az egyetem adatvédelmi tisztviselőjével vagy jogásszal, és töltse ki az összes `[KITÖLTENDŐ]` mezőt (lista a 13. pontban).

## Tartalom

1. Szerepek: ki az adatkezelő és ki az adatfeldolgozó
2. Adatleltár
3. Adatkezelési nyilvántartás (30. cikk)
4. Megőrzési rend és törlési mechanizmusok
5. Adatfeldolgozók és harmadik országba történő továbbítás (28., 44–49. cikk)
6. Technikai és szervezési intézkedések (32. cikk)
7. Beépített és alapértelmezett adatvédelem: szabályok fejlesztőknek (25. cikk)
8. Adatvédelmi hatásvizsgálat – előszűrés (35. cikk)
9. Az érintetti kérelmek kezelése (12–22. cikk)
10. Adatvédelmi incidens kezelése (33–34. cikk)
11. Kapcsolódás az MI-rendelethez
12. Megvalósítási ellenőrzőlista
13. Még kitöltendő mezők

---

## 1. Szerepek: ki az adatkezelő és ki az adatfeldolgozó

| Adat | A Mimir üzemeltetőjének szerepe | Indoklás |
| --- | --- | --- |
| Felhasználói fiókok, mentett tesztek, naplók, kapcsolatfelvételi üzenetek | **Adatkezelő** | Az üzemeltető határozza meg az adatkezelés célját és módját. |
| Harmadik személyek adatai a feltöltött dokumentumokban (pl. nevek egy esettanulmányban) | Egyéni felhasználónál **adatkezelő**; ha egy intézmény (iskola, kar) használja a munkatársai számára, **adatfeldolgozó** | Az intézmény dönt a saját dokumentumai feldolgozásáról; a Mimir csak a generálást végzi a nevében. |
| Az egyetemi GenAI API-nak küldött dokumentumrészletek | Az Óbudai Egyetem az üzemeltető **adatfeldolgozója** | A modellt kizárólag az üzemeltető utasítására futtatja. |

Következmények:

- Intézményi használathoz **adatfeldolgozói szerződés** (28. cikk) kell az intézmény és az üzemeltető között. A szerződésminta tervezett (GDPR-08, #80).
- Ha a Mimirt maga az Óbudai Egyetem üzemelteti, az egyetem az adatkezelő, a GenAI szolgáltatás pedig belső szolgáltatás; ekkor az 5. pont ennek megfelelően módosul.

## 2. Adatleltár

| Adatelem | Hol található (célarchitektúra) | Személyes adat? |
| --- | --- | --- |
| E-mail cím, jelszó hash, megerősítő token | Postgres `users` tábla (auth szolgáltatás, GW-01 #8) | Igen |
| Feltöltött fájl bájtjai | Csak a Wellspring folyamat memóriájában | Lehet (a dokumentum tartalma) |
| Kinyert szöveg, chunkok | RuneCarver / Bifrost memória; Qdrant kollekció | Lehet |
| Embeddingek | Qdrant (jelenleg memóriában) | Lehet (származtatott) |
| Prompt és a modell nyers válasza | Csak a worker memóriájában | Lehet |
| Generált teszt piszkozata | Bifrost feladattár (memóriában, lejárati idővel) és a böngésző | Lehet |
| Mentett tesztek | Skald tárhely (PDF + SQLite sor a tulajdonos e-mail címével) | Igen |
| MI működési napló | Postgres `audit_logs` (csak lenyomatok és metaadatok) | Álnevesített (feladatazonosító) |
| Szervernaplók | Nginx és a konténerek kimenete | Igen (rövidített IP) |
| Böngészőtár: `mimir-theme`, `mimir-lang`, `mimir_user` | A felhasználó saját böngészője | A `mimir_user` tartalmazza az e-mail címet |

## 3. Adatkezelési nyilvántartás (30. cikk)

**Adatkezelő:** [KITÖLTENDŐ] · **Elérhetőség:** [KITÖLTENDŐ] · **Adatvédelmi tisztviselő:** [KITÖLTENDŐ vagy „nincs kijelölve”]

| # | Adatkezelés | Cél | Érintettek | Adatkategóriák | Jogalap | Címzettek | Harmadik országba továbbítás | Megőrzés | Biztonsági intézkedések |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Fiókkezelés | Fiók és belépés biztosítása | Regisztrált felhasználók | E-mail, jelszó hash, megerősítő token, időbélyegek | 6. cikk (1) b) | Tárhelyszolgáltató, e-mail szolgáltató | Nem (kivéve a Cloudflare hálózati adatait) | Törlésig; meg nem erősített fiók 30 nap | TLS, hash-elt jelszó, hozzáférés-szabályozás |
| 2 | Tesztgenerálás | Teszt készítése a felhasználó dokumentumából | Felhasználók; a dokumentumokban szereplő személyek | Dokumentumtartalom, származtatott szöveg, embeddingek, prompt | 6. cikk (1) b) | Tárhelyszolgáltató, egyetemi GenAI (kivéve LOCAL_ONLY módban) | Nem | A feladat idejére, legfeljebb 60 perc | Memóriában történő feldolgozás, törlés a feladat után, lejárati idő |
| 3 | Mentett tesztek (kérésre) | Tesztek újbóli letöltése | Felhasználók | Cím, PDF, tulajdonos e-mail címe, időbélyegek | 6. cikk (1) b), a felhasználó kérésére | Tárhelyszolgáltató | Nem | Törlésig, legfeljebb 12 hónap | Tulajdonos-ellenőrzés törléskor, automatikus törlés |
| 4 | MI működési napló | Minőség, nyomonkövethetőség, hibakeresés | Felhasználók (álnevesítve) | Feladatazonosító, modell, promptverzió, SHA-256 lenyomatok, hosszak, pontszám | 6. cikk (1) f) | Tárhelyszolgáltató | Nem | 30 nap | Tartalmat nem tárol, automatikus törlés |
| 5 | Biztonsági naplózás | Biztonság, visszaélések felderítése | Látogatók | Rövidített IP, időpont, útvonal paraméterek nélkül, válaszkód | 6. cikk (1) f) | Tárhelyszolgáltató, Cloudflare | Cloudflare (DPF / általános szerződési feltételek) | Legfeljebb 14 nap | IP-rövidítés, lekérdezési paraméterek nélkül |
| 6 | Kapcsolatfelvétel | Megkeresések megválaszolása | Megkeresők | Név, e-mail, üzenet | 6. cikk (1) f) / b) | E-mail szolgáltató | Nem | Lezárás után 1 év | Hozzáférés-szabályozás |

A 4., 5. és 6. adatkezeléshez érdekmérlegelési teszt szükséges. Röviden: az érdekek (biztonság, szolgáltatásminőség) szükségesek, az adatok minimalizáltak (nincs tartalom, rövidített IP), a megőrzés rövid, és a felhasználók tiltakozhatnak. Indulás előtt teljes terjedelmében el kell készíteni (tervezett, GDPR-08 #80).

## 4. Megőrzési rend és törlési mechanizmusok

| Adat | Megőrzés | Törlési mechanizmus | Állapot |
| --- | --- | --- | --- |
| Feltöltött fájl bájtjai | A kérés idejére | Soha nem kerül lemezre; a kinyerés után felszabadul | **Megvalósítva** (a Wellspring eddig is memóriában dolgozott) |
| Chunkok és embeddingek | A feladat végéig, legfeljebb 60 perc | A Bifrost a feladat befejezésekor vagy hibájakor kiüríti a vektortárat; a következő betöltés is kiüríti | **Megvalósítva** ebben a változtatásban; témakörönkénti elkülönítés: tervezett (TOP-03 #107) |
| Feladateredmények (tesztpiszkozat) | 60 perc (`JOB_TTL_SECONDS`) | A Bifrost minden kérésnél eldobja a lejárt feladatokat | **Megvalósítva** ebben a változtatásban |
| Mentett tesztek | Törlésig, legfeljebb 12 hónap (`HISTORY_RETENTION_DAYS=365`) | Skald törlés induláskor és 24 óránként; törlési végpont a felhasználónak; a mentés csak kérésre történik | **Megvalósítva** ebben a változtatásban |
| MI működési napló | 30 nap (`AUDIT_RETENTION_DAYS`) | A The Forge óránként töröl; csak lenyomatokat tárol; a régi szöveges oszlopokat induláskor kiüríti | **Megvalósítva** ebben a változtatásban |
| Szervernaplók | Legfeljebb 14 nap | Az Nginx hozzáférési napló paraméterek nélkül, rövidített IP-vel készül; a hibanapló csak `crit` szinten; a Docker naplók konténerenként 10 MB × 3 fájl után forognak | **Részben megvalósítva** (anonimizálás és méretalapú rotáció kész; a szigorú 14 napos időkorlát üzemeltetési feladat) |
| Fiókok | Törlésig; meg nem erősített 30 nap | Auth szolgáltatás | **Tervezett** (GW-01 #8, GDPR-07 #79) |
| Kapcsolatfelvételi üzenetek | 1 év | Postafiók-szabály | **Tervezett** (az űrlap még nincs bekötve) |
| Böngészőtár | Amíg a felhasználó törli vagy kijelentkezik | Az „Adataim” oldal minden Mimir-kulcsot töröl | **Megvalósítva** ebben a változtatásban |
| A git-történetben lévő adatok (`services/skald/storage`) | El kell távolítani | Ebben a változtatásban kikerülnek a követésből; történet-újraírás `git filter-repo`-val | **Részben megvalósítva** (újraírás: PLT-01 #1) |

**Tervezett változás – Témakör-munkaterület ([#103 epic](https://github.com/Deatron01/Project-Mimir/issues/103)):** a témakörök bevezetésével a chunkok, embeddingek, a fogalmi gráf és a chatelőzmények témakörönként megmaradnak, amíg a felhasználó törli a fájlt vagy a témakört, illetve amíg a témakör a [#104](https://github.com/Deatron01/Project-Mimir/issues/104)-ben meghatározott ideig (javaslat: 90 nap) inaktív nem lesz. A nyers fájlokat továbbra sem tároljuk. A témakör törlése minden hozzá tartozó adatot töröl ([#108](https://github.com/Deatron01/Project-Mimir/issues/108)). Az adatkezelési tájékoztatót és ezt a dokumentációt a kiadás előtt frissíteni kell ([#121](https://github.com/Deatron01/Project-Mimir/issues/121)); addig a fenti szabályok érvényesek.

Mentések: a fiókadatokról készülhet mentés, de a feltöltött dokumentumok, chunkok és feladateredmények soha nem kerülhetnek mentésbe. A fenti megőrzési időnél régebbi mentéseket ki kell forgatni.

## 5. Adatfeldolgozók és harmadik országba történő továbbítás

| Adatfeldolgozó | Adatok | Helyszín | Szerződés (28. cikk) | Továbbítási garancia | Állapot |
| --- | --- | --- | --- | --- | --- |
| Tárhelyszolgáltató [KITÖLTENDŐ] | A szolgáltatás összes adata | [KITÖLTENDŐ] | Szükséges | — | Nyitott |
| Cloudflare, Inc. | Hálózati forgalom metaadatai (IP) | USA / globális | Cloudflare DPA (a vezérlőpulton elfogadandó) | EU–USA adatvédelmi keretrendszer vagy általános szerződési feltételek | Ellenőrizni, hogy a DPA el van-e fogadva |
| Óbudai Egyetem GenAI (genai.uni-obuda.hu) | Dokumentumrészletek, promptok | Magyarország | Szükséges: írásos megállapodás arról, hogy nem őriz meg adatot és nem tanít vele | — | Nyitott (R6 #98) |
| E-mail szolgáltató [KITÖLTENDŐ] | E-mail cím, levél tartalma | [KITÖLTENDŐ] | Szükséges | Szolgáltatótól függ | Nyitott |

Minden adatfeldolgozónál ellenőrizendő: írásos szerződés; kizárólag utasítás szerinti adatkezelés; titoktartás; biztonsági intézkedések; további adatfeldolgozó igénybevételének jóváhagyása; közreműködés az érintetti kérelmekben; törlés vagy visszaadás a szerződés végén; ellenőrzési jog.

**Helyi mód:** a `.env` fájlban `LOCAL_ONLY=true` beállítással a Bifrost, a Heimdall és a Wellspring nem hívja az egyetemi API-t, így a dokumentum szövege nem hagyja el az üzemeltető szerverét. **Megvalósítva** ebben a változtatásban (alapértéke `false`, hogy a jelenlegi telepítés tovább működjön; kapcsolja be, amint a szerveren elérhető helyi modell).

## 6. Technikai és szervezési intézkedések (32. cikk)

| Intézkedés | Állapot |
| --- | --- |
| TLS minden forgalomhoz (Cloudflare Tunnel, HTTPS) | Megvalósítva |
| Jelszavak bcrypt/Argon2 hash-sel | Tervezett az auth szolgáltatással (GW-01 #8) |
| Valódi hitelesítés és felhasználónkénti jogosultság minden végponton | Tervezett (GW-01 #8, GW-02 #9, SKA-02 #45) — **legmagasabb prioritás**: ma a `/tests` és a letöltések egy `user_id` paraméterben bíznak meg |
| Témakörönként elkülönített feldolgozás (kötelező `topic_id` szűrő, nincs közös keresés) | Tervezett (TOP-03 #107) |
| Feldolgozási adatok, feladateredmények, mentett tesztek, működési napló automatikus törlése | Megvalósítva ebben a változtatásban |
| Nincs dokumentumtartalom a naplókban és a működési naplóban | Megvalósítva ebben a változtatásban |
| IP-rövidítés és lekérdezési paraméterek nélküli hozzáférési napló | Megvalósítva ebben a változtatásban |
| Titkok csak a `.env`-ben, soha a gitben; `.env.example` a repóban | Részben (a `docker-compose.yml` még tartalmaz jelszavakat, PLT-04 #4) |
| Kéréskorlátozás és feltöltési méretkorlát | Részben (50 MB az Nginxben; kéréskorlátozás GW-04 #11) |
| Fájlellenőrzés (típus, méret, kártékony PDF) | Tervezett (WEL-05 #18) |
| Csak a gateway érhető el az internetről | Tervezett (GW-06 #13) |
| Függőség- és image-sebezhetőség-vizsgálat a CI-ban | Tervezett (az ütemterv 4. pontja) |
| Éles rendszerhez csak név szerint kijelölt csapattagok férnek hozzá; kétfaktoros belépés GitHubon és Cloudflare-en | Szervezési — teendő |
| Titoktartási nyilatkozat és rövid GDPR-oktatás a csapatnak | Szervezési — teendő |
| E dokumentáció évenkénti felülvizsgálata | Szervezési — teendő |

## 7. Beépített és alapértelmezett adatvédelem: szabályok fejlesztőknek (25. cikk)

1. Feltöltött tartalmat, kinyert szöveget, promptot vagy modellválaszt soha ne írj lemezre, adatbázisba, naplósorba vagy hibaüzenetbe. Helyette azonosítót, méretet és lenyomatot naplózz.
2. Minden feldolgozási adat feladat- vagy munkamenet-azonosítót és lejárati időt kap. Ha új tárolót vezetsz be, ugyanabban a PR-ben írd meg a törlését is.
3. Az opcionális tárolás **alapértelmezésben ki van kapcsolva** (a tesztek mentése csak kérésre történik).
4. Új külső szolgáltatás vagy adatáramlás esetén ugyanabban a PR-ben frissíteni kell ezt a dokumentációt (3. és 5. pont).
5. Soha ne kerüljön a repóba felhasználói adat, generált vizsga vagy adatbázis. Teszteléshez szintetikus vagy közkincs dokumentumokat használj.
6. Az adatvédelemről szóló felhasználói szövegeknek igaznak kell lenniük az aktuális telepítésre (nem állíthatjuk, hogy „soha nem hagyja el a gépet”, ha külső API-t használunk).
7. A PR-sablonban zéró megőrzési jelölőnégyzet van; a bírálónak ellenőriznie kell.

## 8. Adatvédelmi hatásvizsgálat – előszűrés (35. cikk)

| NAIH / EDPB szempont | Fennáll? |
| --- | --- |
| Innovatív technológia (generatív MI) | Igen |
| Kiszolgáltatott személyek adatai (diákok, esetleg kiskorúak szerepelhetnek a dokumentumokban) | Lehetséges |
| Nagy volumenű adatkezelés | Pilot méretben nem; egyetemi szintű bevezetésnél igen |
| Személyek értékelése vagy pontozása | Nem (a Mimir nem osztályoz diákokat) — ennek így is kell maradnia |
| Joghatással járó automatizált döntés | Nem |
| Különleges adatok | Nem cél; előfordulhat, ha a felhasználók ilyen dokumentumot töltenek fel |

**Következtetés:** legalább két szempont fennállhat, ezért **intézményi bevezetés előtt teljes hatásvizsgálat javasolt**. A pilot időszakban az alábbi kockázatokat a zéró megőrzés csökkenti.

| Kockázat | Valószínűség / hatás | Kockázatcsökkentés | Állapot |
| --- | --- | --- | --- |
| Egy másik felhasználó látja a dokumentumomat vagy tesztemet (közös vektortár) | Magas / magas | Témakör-elkülönítés (TOP-03 #107, tesztelve: TOP-08 #112); törlés minden feladat után | Részben |
| Jogosulatlan hozzáférés a mentett tesztekhez | Magas / közepes | Valódi hitelesítés és tulajdonos-ellenőrzés (GW-01 #8, SKA-02 #45) | Tervezett |
| Dokumentumtartalom marad a naplókban vagy a működési naplóban | Közepes / magas | Csak metaadatot tartalmazó működési napló, naplószűrés | Megvalósítva |
| Túlzott megőrzés | Közepes / közepes | Lejárati idők és törlési feladatok | Megvalósítva |
| Tartalom továbbítása harmadik félnek jogalap vagy szerződés nélkül | Közepes / magas | `LOCAL_ONLY` mód; adatfeldolgozói megállapodás az egyetemmel | Részben |
| A felhasználók különleges vagy diákokra vonatkozó adatot töltenek fel | Közepes / magas | Figyelmeztetés és megerősítés feltöltéskor; adatfeldolgozói szerződés intézményekkel | Megvalósítva (felületi figyelmeztetés) / Tervezett (szerződés) |
| A pontatlan MI-kimenet kárt okoz a diákoknak | Közepes / közepes | Kötelező emberi ellenőrzés, szerkesztő, figyelmeztetés | Megvalósítva |

## 9. Az érintetti kérelmek kezelése

1. **Beérkezés:** a kérelmek az adatvédelmi e-mail címre érkeznek (az „Adataim” oldal is erre mutat). Minden kérelmet rögzíteni kell a kérelem-nyilvántartásban (dátum, típus, kérelmező, határidő, eredmény) — dokumentumtartalom nélkül.
2. **Személyazonosság ellenőrzése:** kérjük, hogy a kérelmező a fiókhoz tartozó e-mail címről erősítse meg a kérést. Ennél több adatot ne kérjünk.
3. **Határidő:** a beérkezéstől számított 1 hónapon belül válaszolni kell; összetett esetben legfeljebb további 2 hónappal meghosszabbítható, erről az első hónapon belül tájékoztatni kell a kérelmezőt.
4. **Teljesítés:**
   - Hozzáférés / adathordozhatóság: a fiókadatok és a mentett tesztek exportja (JSON + PDF-ek).
   - Törlés: a fiók, a mentett tesztek (Skald sorok és fájlok), valamint – ha összekapcsolható – a felhasználó feladataihoz tartozó naplósorok törlése. A feldolgozási adatok a zéró megőrzés miatt már nem léteznek; ezt a válaszban jelezni kell.
   - Helyesbítés: az e-mail cím módosítása.
   - Tiltakozás / korlátozás: az adott adatkezelés leállítása az érintettre nézve, és ennek rögzítése.
5. **Válasz** a kérelem nyelvén (magyarul vagy angolul), díjmentesen.
6. **Eszközök állapota:** a mentett tesztek és a helyi adatok önkiszolgáló törlése ebben a változtatásban **megvalósult**; a fiókexport és -törlés végpontjai **tervezettek** (GDPR-07 #79, a GW-01 #8-tól függ).

## 10. Adatvédelmi incidens kezelése

1. **Észlelés és megfékezés** (0–4 óra): aki észleli, azonnal szól az incidensfelelősnek [KITÖLTENDŐ]. A szivárgást meg kell állítani (titkok cseréje, végpont lekapcsolása, tokenek visszavonása).
2. **Értékelés** (24 órán belül): milyen adatok, hány érintett, milyen következmények várhatók. Mindent rögzíteni kell az incidens-nyilvántartásban (33. cikk (5)), akkor is, ha nem kell bejelenteni.
3. **Bejelentés a NAIH-nak a tudomásszerzéstől számított 72 órán belül**, kivéve, ha az incidens valószínűleg nem jár kockázattal. A NAIH online incidensbejelentő felületét kell használni. Ha nem áll rendelkezésre minden információ, a bejelentés szakaszosan is megtehető.
4. **Az érintettek indokolatlan késedelem nélküli tájékoztatása**, ha az incidens valószínűleg magas kockázattal jár (34. cikk), közérthetően: mi történt, milyen következményekkel járhat, mit tettünk, mit tehetnek ők, kihez fordulhatnak.
5. **Adatfeldolgozók** indokolatlan késedelem nélkül kötelesek értesíteni az üzemeltetőt; ezt minden adatfeldolgozói szerződésbe bele kell foglalni.
6. **Utólagos elemzés** 2 héten belül: kiváltó ok, javítások, e dokumentáció frissítése.

Példa: a hitelesítés nélküli `/api/v1/tests` végpont (lásd az ütemterv auditját) incidensnek minősül, ha a tulajdonoson kívül bárki letöltött egy mentett tesztet. A bejelentésről a hozzáférési naplók átnézése után kell dönteni.

## 11. Kapcsolódás az MI-rendelethez

- **Átláthatóság (50. cikk):** a felhasználóknak tudniuk kell, hogy MI-rendszerrel dolgoznak, és hogy a kérdéseket MI generálta. **Megvalósítva:** figyelmeztetés a chatben, az adatkezelési tájékoztató 7. pontja, valamint a PDF metaadat-oldala, amely jelzi, hogy a tartalom MI-asszisztens segítségével készült.
- **Emberi felügyelet:** a szerkesztő kötelező ellenőrzési lépést iktat be az exportálás elé. **Megvalósítva.**
- **Kockázati besorolás:** a III. melléklet szerint az oktatásban a *tanulási eredmények értékelésére* vagy a *tanulási folyamat irányítására* használt MI **magas kockázatú**. A tanárok által teljes egészében ellenőrzött tesztek *generálása* ezen kívül esik, de **a diákválaszok automatikus pontozása magas kockázatú kategóriába sorolná a Mimirt**. Pontozási funkciót csak új értékelés után szabad bevezetni.
- **Naplózás:** a csak metaadatot tartalmazó működési napló tartalom tárolása nélkül biztosítja a nyomonkövethetőséget.

## 12. Megvalósítási ellenőrzőlista

| Követelmény | Hol | Állapot | Issue |
| --- | --- | --- | --- |
| Adatkezelési tájékoztató magyarul és angolul, az oldalon megjelenítve | `docs/gdpr/privacy-notice.*.md`, `/privacy` oldal | Megvalósítva (kitöltendő mezőkkel) | GDPR-08 #80 |
| Figyelmeztetés és megerősítés feltöltéskor | Chat oldal | Megvalósítva | GDPR-10 #82 |
| A tesztek mentése csak kérésre, a megőrzési idő jelzésével | Kérdésszerkesztő, Skald `save` jelző | Megvalósítva | SKA-01 #44 |
| Mentett teszt törlése | „Tesztjeim” oldal, Skald `DELETE /api/v1/tests/{id}` | Megvalósítva (a valódi hitelesítésig `user_id` alapú tulajdonos-ellenőrzéssel) | GDPR-07 #79 |
| „Adataim” oldal: böngészőben tárolt adatok megtekintése, exportja és törlése | `/data` oldal | Megvalósítva | GDPR-07 #79 |
| Feldolgozási adatok törlése minden feladat után; feladat-lejárati idő | Bifrost | Megvalósítva | GDPR-02 #74, GDPR-03 #75 |
| Csak metaadatot tartalmazó működési napló, 30 napos megőrzés, régi adatok kiürítése | Bifrost, The Forge | Megvalósítva | FRG-05 #42, GDPR-01 #73 |
| Mentett tesztek megőrzése (12 hónap) | Skald | Megvalósítva | GDPR-03 #75 |
| Hozzáférési napló: paraméterek nélkül, rövidített IP-vel | Nginx | Megvalósítva | GDPR-05 #77 |
| Helyi mód (külső MI nélkül) | Bifrost, Heimdall, Wellspring, compose | Megvalósítva (alapból kikapcsolva) | GDPR-06 #78 |
| Tárolt felhasználói adatok kivétele a git-követésből | `.gitignore`, `git rm --cached` | Megvalósítva | PLT-01 #1 |
| A git-történet újraírása a régi felhasználói adatok eltávolításához | Repó | Tervezett (csapatszintű egyeztetés és force push kell) | PLT-01 #1 |
| Valódi hitelesítés és tulajdonos-ellenőrzés | Auth szolgáltatás, gateway, Skald | Tervezett | GW-01 #8, GW-02 #9, SKA-02 #45 |
| Vektoradatok elkülönítése | Bifrost | Tervezett (témakörönként) | TOP-03 #107 (a BIF-01 #25 helyett) |
| Fiókexport és -törlés | Auth szolgáltatás | Tervezett | GDPR-07 #79 |
| Automatizált zéró megőrzési teszt a CI-ban | Tesztek | Tervezett | GDPR-04 #76 |
| Témakör-elkülönítés: kötelező `topic_id` szűrés a Qdrantban | Bifrost | Tervezett | TOP-03 #107 |
| Témakör kaszkádtörlése és takarító feladat | Skald, Bifrost, The Forge | Tervezett | TOP-04 #108 |
| Témakör-elkülönítési és maradványmentességi tesztcsomag | Tesztek | Tervezett | TOP-08 #112 |
| Inaktív témakörök automatikus törlése | The Forge | Tervezett | TOP-09 #113 |
| Megőrzési döntés és titkosítás tároláskor a témakör-adatokra | Architektúra | Tervezett | TOP-18 #104 |
| Tájékoztató és dokumentáció frissítése a témakörökhöz | Dokumentáció | Tervezett (a témakörök kiadása előtt) | TOP-17 #121 |
| Adatfeldolgozói szerződések (tárhely, egyetem, e-mail) és intézményi szerződésminta | Jogi | Tervezett | R6 #98, GDPR-08 #80 |
| Érdekmérlegelési teszt, teljes hatásvizsgálat a bevezetés előtt | Jogi | Tervezett | GDPR-08 #80 |
| Naplórotáció | `docker-compose.yml` (konténerenként 10 MB × 3); 14 napos időkorlát a szerveren | Részben megvalósítva | GDPR-05 #77 |

## 13. Még kitöltendő mezők

- Az adatkezelő neve, címe, adatvédelmi e-mail címe és adatvédelmi tisztviselője (tájékoztató 1. pont; e dokumentáció 3. pont).
- Tárhelyszolgáltató és e-mail szolgáltató (tájékoztató 5. pont; e dokumentáció 5. pont).
- Az Óbudai Egyetemmel a GenAI API-ra kötött megállapodás megnevezése.
- Incidensfelelős és helyettese (10. pont).
- A jogi átvizsgálás dátuma és végzője.
