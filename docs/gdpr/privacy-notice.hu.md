# Adatkezelési tájékoztató

Hatályos: 2026. szeptember 24-től · 1.1-es verzió (tervezet) · English version: [privacy-notice.en.md](privacy-notice.en.md)

> Ezt a fájlt a `frontend/src/locales/hu/translation.json` `legal.privacy` blokkjából generáltuk; a weboldal ugyanezt a szöveget mutatja. Módosítás esetén mindkettőt frissíteni kell.

Ez a tájékoztató elmondja, milyen személyes adatokat kezel a Mimir AI tesztgeneráló szolgáltatás, mire használja őket, meddig őrzi meg és milyen jogaid vannak. A Mimir alapelve a „zéró megőrzés”: a feltöltött dokumentumaidat csak a teszt elkészítéséhez használjuk, utána töröljük.

## 1. Az adatkezelő

- Adatkezelő: [KITÖLTENDŐ: az üzemeltető neve]
- Székhely / postacím: [KITÖLTENDŐ]
- E-mail az adatvédelmi kérésekhez: [KITÖLTENDŐ: pl. adatvedelem@mimir-ai.hu]
- Adatvédelmi tisztviselő: [KITÖLTENDŐ, ha van; ha nincs, ez a sor törölhető]
- Weboldal: https://mimir-ai.hu

## 2. Röviden

- A feltöltött dokumentumot, a kinyert szöveget és az abból készült szövegrészeket kizárólag a teszt generálásához használjuk, és a feldolgozás végén töröljük (legkésőbb 60 perc után automatikusan).
- A generált tesztet csak akkor mentjük el a fiókodhoz, ha ezt kifejezetten kéred; a mentett teszteket bármikor törölheted, és legfeljebb 12 hónapig őrizzük.
- A dokumentumaidat nem használjuk fel mesterséges intelligencia tanítására, és nem adjuk el senkinek.
- Nem használunk nyomkövető, hirdetési vagy analitikai sütiket.

## 3. Milyen adatokat, milyen célból és jogalappal kezelünk, és meddig

| Adatkezelés | Adatok | Cél | Jogalap | Megőrzés |
| --- | --- | --- | --- | --- |
| Felhasználói fiók | E-mail cím, jelszó hash-e (visszafejthetetlen formában), megerősítő token, regisztráció ideje | Fiók létrehozása, belépés, a szolgáltatás nyújtása | Szerződés teljesítése – GDPR 6. cikk (1) b) | A fiók törléséig; a meg nem erősített fiókokat 30 nap után töröljük |
| Feltöltött dokumentum és származékai | A fájl, a kinyert szöveg, a szövegrészek (chunkok), azok vektoros reprezentációi, a nyelvi modellnek küldött kérés | A kért teszt elkészítése | Szerződés teljesítése – GDPR 6. cikk (1) b) | Csak a feldolgozás idejére; a feladat végén töröljük, legkésőbb 60 perc után automatikusan |
| Generált teszt (piszkozat) | A generált kérdések és válaszok | Ellenőrzés és szerkesztés az exportálás előtt | Szerződés teljesítése – GDPR 6. cikk (1) b) | A szerveren legfeljebb 60 percig; a szerkesztés a böngésződben történik |
| Mentett tesztek („Tesztjeim”) – csak kérésre | A teszt címe, PDF-fájlja, mérete, létrehozási ideje, a fiókod azonosítója (e-mail cím) | Hogy később újra letölthesd | Szerződés teljesítése – GDPR 6. cikk (1) b), a kifejezett kérésedre | Amíg nem törlöd, de legfeljebb 12 hónapig |
| AI működési napló | Feladatazonosító, modell neve, promptverzió, a kérés és a kontextus kriptográfiai lenyomata (SHA-256) és hossza, minőségi pontszám, időpont – a dokumentum szövege nélkül | Az AI-rendszer minőségének, nyomonkövethetőségének és hibakeresésének biztosítása | Jogos érdek – GDPR 6. cikk (1) f) | 30 nap |
| Szervernaplók | Rövidített (anonimizált) IP-cím, időpont, a kért útvonal paraméterek nélkül, válaszkód, válaszidő | Biztonság, visszaélések felderítése, hibaelhárítás | Jogos érdek – GDPR 6. cikk (1) f) | Legfeljebb 14 nap |
| Kapcsolatfelvétel | Név, e-mail cím, az üzenet tartalma | Válaszadás a megkeresésedre | Jogos érdek – GDPR 6. cikk (1) f), illetve szerződés előkészítése – 6. cikk (1) b) | Az ügy lezárásától számított 1 év |
| Beállítások a böngésződben | Színpaletta és mód (mimir-theme), nyelv (mimir-lang), bejelentkezési állapot (mimir_user), utolsó tesztbeállítások (mimir-gen-options), választott nyelvi modell (mimir-model) | A választott beállítások megjegyzése, a munkamenet fenntartása | A kért szolgáltatáshoz feltétlenül szükséges tárolás (az ePrivacy-irányelv 5. cikk (3) bekezdése szerinti kivétel); nem igényel hozzájárulást | A saját eszközödön, amíg törlöd vagy kijelentkezel |

## 4. Mások személyes adatai a feltöltött dokumentumokban

Kérjük, lehetőleg olyan oktatási anyagokat tölts fel, amelyek nem tartalmaznak személyes adatot. Ne tölts fel különleges kategóriájú adatot (pl. egészségügyi adat), diákok értékelését, névsorokat vagy más azonosítható személyekre vonatkozó információt.

Ha mégis ilyen adatot tartalmazó dokumentumot töltesz fel, neked (vagy az intézményednek) kell rendelkeznie ehhez megfelelő jogalappal. Ezeket az adatokat kizárólag a teszt elkészítéséhez, a feldolgozás idejére kezeljük, a fenti zéró megőrzési szabály szerint. Intézményi használat esetén az intézménnyel adatfeldolgozói szerződést kötünk.

## 5. Kik férhetnek hozzá az adatokhoz (címzettek, adatfeldolgozók)

- Tárhely- és szerverszolgáltató: [KITÖLTENDŐ: név, székhely] – a szolgáltatás futtatása.
- Cloudflare, Inc. (USA) – biztonságos hálózati hozzáférés (Cloudflare Tunnel); a forgalom technikai adatait (pl. IP-cím) kezeli.
- Óbudai Egyetem GenAI szolgáltatása (genai.uni-obuda.hu) – ha a szolgáltatás nem kizárólag helyi módban fut, a dokumentumból kiválasztott szövegrészeket és a kérésedet a teszt és a minőségellenőrzés elkészítéséhez az egyetem által üzemeltetett nyelvi modell dolgozza fel. Minden feltöltés előtt az oldal megmutatja, hol dolgozzuk fel a dokumentumot, és választhatod helyette a helyi modellt; ekkor a szöveg nem hagyja el az üzemeltető szerverét. [KITÖLTENDŐ: az egyetemmel kötött megállapodás megnevezése]
- E-mail-küldő szolgáltató: [KITÖLTENDŐ] – a fiók megerősítéséhez és jelszó-visszaállításhoz szükséges levelek kiküldése.
- Helyi mód: ha az üzemeltető bekapcsolja a LOCAL_ONLY beállítást, a dokumentum szövege nem hagyja el az üzemeltető saját szerverét.

Adatfeldolgozóink csak a mi utasításunkra, írásbeli szerződés alapján (GDPR 28. cikk) kezelhetik az adatokat. Hatósági megkeresés esetén jogszabály alapján adatot továbbíthatunk hatóságnak vagy bíróságnak.

## 6. Adattovábbítás az EGT-n kívülre

A Cloudflare, Inc. az Egyesült Államokban is kezelhet hálózati adatokat. Az adattovábbítás az EU–USA adatvédelmi keretrendszer (Data Privacy Framework) szerinti tanúsítás, ennek hiányában az Európai Bizottság által elfogadott általános szerződési feltételek (GDPR 46. cikk) alapján történik. A feltöltött dokumentumok tartalmát nem továbbítjuk az EGT-n kívülre.

## 7. Mesterséges intelligencia és automatizált döntéshozatal

- A Mimir egy mesterséges intelligencián alapuló rendszer: a kérdéseket nagy nyelvi modell generálja. Az így készült tartalom hibás lehet, ezért a felhasználásuk előtt emberi ellenőrzés kötelező.
- A Mimir nem hoz rólad (és a diákokról sem) olyan automatizált döntést, amely joghatással járna vagy hasonlóan jelentős mértékben érintene (GDPR 22. cikk). A rendszer nem értékel és nem pontoz vizsgázókat.
- A dokumentumaidat, a kérdéseket és a válaszokat nem használjuk fel modellek tanítására.

## 8. Adatbiztonság

- Titkosított (HTTPS/TLS) kapcsolat a böngésző és a szolgáltatás között.
- A jelszavakat csak visszafejthetetlen, sózott hash formában tároljuk.
- A feldolgozás alatti adatok munkamenetenként elkülönítve, a feladat végén automatikusan törlődnek.
- A naplókban nem tárolunk dokumentumtartalmat, az IP-címeket rövidítve naplózzuk.
- Hozzáférés-korlátozás, rendszeres frissítések, biztonsági mentések a fiókadatokról (a feltöltött dokumentumokról nem készül mentés).

## 9. A jogaid

- Hozzáférés (15. cikk): tájékoztatást és másolatot kérhetsz a rólad kezelt adatokról.
- Helyesbítés (16. cikk): kérheted a pontatlan adatok javítását.
- Törlés („elfeledtetés”, 17. cikk): kérheted az adataid törlését; a mentett tesztjeidet magad is törölheted a „Tesztjeim” oldalon, a böngésződben tárolt adatokat pedig az „Adataim” oldalon.
- Az adatkezelés korlátozása (18. cikk).
- Adathordozhatóság (20. cikk): a fiókadataidat és mentett tesztjeidet géppel olvasható formában kikérheted.
- Tiltakozás (21. cikk): a jogos érdeken alapuló adatkezelés ellen bármikor tiltakozhatsz.
- Ha egy adatkezelés hozzájáruláson alapul, a hozzájárulásodat bármikor visszavonhatod; ez nem érinti a korábbi adatkezelés jogszerűségét.

Kérésedet az 1. pontban megadott e-mail címre küldheted. Legfeljebb egy hónapon belül válaszolunk; ez indokolt esetben további két hónappal meghosszabbítható, erről tájékoztatunk. A kérés teljesítése előtt ellenőrizhetjük a személyazonosságodat (pl. a fiókodhoz tartozó e-mail címről küldött megerősítéssel). A kérések teljesítése díjmentes.

## 10. Jogorvoslat

Ha úgy gondolod, hogy megsértettük az adatvédelmi jogaidat, kérjük, először fordulj hozzánk. Panaszt tehetsz a Nemzeti Adatvédelmi és Információszabadság Hatóságnál (NAIH, 1055 Budapest, Falk Miksa utca 9–11., postacím: 1363 Budapest, Pf. 9., telefon: +36 1 391 1400, e-mail: ugyfelszolgalat@naih.hu, www.naih.hu), vagy bírósághoz fordulhatsz; a pert – választásod szerint – a lakóhelyed vagy tartózkodási helyed szerint illetékes törvényszék előtt is megindíthatod.

## 11. Gyermekek

A Mimir oktatóknak és felnőtt felhasználóknak szól. 16 éven aluli személyek nem regisztrálhatnak. Ha tudomásunkra jut, hogy 16 éven aluli személy adatait kezeljük, azokat haladéktalanul töröljük.

## 12. A tájékoztató módosítása

A tájékoztatót a szolgáltatás vagy a jogszabályok változása esetén frissíthetjük. A lényeges változásokról a weboldalon, regisztrált felhasználóinkat e-mailben is értesítjük. A korábbi változatokat kérésre elérhetővé tesszük.
