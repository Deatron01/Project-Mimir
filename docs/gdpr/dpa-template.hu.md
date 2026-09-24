# Adatfeldolgozói szerződés (minta)

0.1-es verzió (tervezet, 2026. szeptember 24.) · English version: [dpa-template.en.md](dpa-template.en.md)

> **Jogi átvizsgálásra szánt tervezet.** A minta a GDPR 28. cikk (3) bekezdését és az Európai Bizottság adatkezelők és adatfeldolgozók közötti általános szerződési feltételeit ((EU) 2021/915 végrehajtási határozat) követi. **Intézményi használatra** készült (iskola vagy kar használja a Mimirt a munkatársai számára), amikor az intézmény az adatkezelő, a Mimir üzemeltetője pedig az adatfeldolgozó (lásd a [megfelelőségi dokumentáció 1. pontját](compliance.hu.md#1-szerepek-ki-az-adatkezelő-és-ki-az-adatfeldolgozó)). Aláírás előtt jogásszal át kell nézetni, és minden `[KITÖLTENDŐ]` mezőt ki kell tölteni. Egyéni felhasználókkal nem kell megkötni; rájuk az [adatkezelési tájékoztató](privacy-notice.hu.md) vonatkozik.

---

**amely létrejött**

**Adatkezelő:** [KITÖLTENDŐ: intézmény neve, székhelye, nyilvántartási száma, képviselője] (a továbbiakban: „Adatkezelő”)

**és**

**Adatfeldolgozó:** [KITÖLTENDŐ: a Mimir üzemeltetőjének neve, címe, nyilvántartási száma, képviselője] (a továbbiakban: „Adatfeldolgozó”)

**között.**

## 1. A szerződés tárgya és időtartama

1.1 Az Adatfeldolgozó a Mimir AI tesztgeneráló szolgáltatást (a továbbiakban: „Szolgáltatás”) nyújtja az Adatkezelő jogosult munkatársai számára [KITÖLTENDŐ: alapszerződés / megrendelés, dátum] alapján. Ennek során az Adatkezelő nevében személyes adatokat kezel.

1.2 A szerződés addig hatályos, amíg az Adatfeldolgozó az Adatkezelő számára személyes adatot kezel; az alapszerződés megszűnésével automatikusan megszűnik, a 10. pontban foglaltak szerint.

## 2. Az adatkezelés jellege, célja és terjedelme

A részleteket az **1. melléklet** tartalmazza. Az Adatfeldolgozó a személyes adatokat kizárólag a Szolgáltatás nyújtásához kezeli: az Adatkezelő munkatársai által feltöltött dokumentumokból tesztkérdéseket készít, és teszteket csak akkor tárol, ha a felhasználó kifejezetten elmenti azokat.

## 3. Utasítások

3.1 Az Adatfeldolgozó a személyes adatokat kizárólag az Adatkezelő írásbeli utasításai alapján kezeli – ideértve a harmadik országba történő továbbítást is –, kivéve, ha uniós vagy tagállami jog másként rendelkezik; ilyenkor erről az adatkezelés előtt tájékoztatja az Adatkezelőt, hacsak a jog ezt nem tiltja.

3.2 Az Adatkezelő utasításának minősül ez a szerződés, az 1. mellékletben választott beállítás (különösen a `LOCAL_ONLY` mód), valamint a felhasználók műveletei a Szolgáltatásban (dokumentum feltöltése, teszt mentése vagy törlése). További utasítást írásban (e-mailben is) lehet adni.

3.3 Az Adatfeldolgozó haladéktalanul jelzi, ha véleménye szerint egy utasítás sérti a GDPR-t vagy más adatvédelmi jogszabályt.

## 4. Titoktartás

Az Adatfeldolgozó biztosítja, hogy a személyes adatok kezelésére jogosult személyek titoktartási kötelezettség (szerződés vagy jogszabály alapján) hatálya alatt állnak, és az adatokat csak a Szolgáltatáshoz szükséges mértékben kezelik.

## 5. Az adatkezelés biztonsága

5.1 Az Adatfeldolgozó végrehajtja a **2. mellékletben** felsorolt technikai és szervezési intézkedéseket (GDPR 32. cikk). Egy intézkedést csak legalább azonos védelmi szintet nyújtóval válthat ki.

5.2 Zéró megőrzés: a feltöltött dokumentumokat, a belőlük kinyert szöveget, a szövegrészeket, a vektorokat és a promptokat csak a generálási feladat idejére kezeli, és a feladat végén, legkésőbb 60 perc elteltével törli. Ezeket modellek tanítására nem használja, és biztonsági mentésbe soha nem kerülnek.

## 6. További adatfeldolgozók

6.1 Az Adatkezelő általános felhatalmazást ad a **3. mellékletben** felsorolt további adatfeldolgozók igénybevételére.

6.2 Új további adatfeldolgozó bevonásáról vagy cseréjéről az Adatfeldolgozó legalább [KITÖLTENDŐ: 30] nappal előre írásban értesíti az Adatkezelőt. Az Adatkezelő ezen belül észszerű adatvédelmi okból tiltakozhat; ha a felek nem jutnak megállapodásra, az Adatkezelő az érintett szolgáltatásrészt felmondhatja.

6.3 Az Adatfeldolgozó minden további adatfeldolgozóra írásbeli szerződésben ugyanazokat az adatvédelmi kötelezettségeket rója, és azok teljesítéséért teljes felelősséggel tartozik az Adatkezelő felé.

## 7. Továbbítás az EGT-n kívülre

A feltöltött dokumentumokból származó személyes adat nem kerül az EGT-n kívülre. A hálózati forgalmi metaadatokat (pl. IP-cím) a Cloudflare, Inc. az Egyesült Államokban kezelheti az EU–USA adatvédelmi keret, ennek hiányában a Bizottság általános szerződési feltételei alapján (GDPR 46. cikk). Minden más továbbításhoz az Adatkezelő előzetes írásbeli utasítása szükséges.

## 8. Az Adatkezelő segítése

8.1 **Érintetti kérelmek:** az Adatfeldolgozó a közvetlenül hozzá érkező érintetti kérelmet haladéktalanul továbbítja az Adatkezelőnek, és utasítás nélkül maga nem válaszol rá. Az adatkezelés jellegének megfelelően segít az Adatkezelőnek a GDPR 15–22. cikke szerinti kérelmek teljesítésében (például egy felhasználó mentett tesztjeinek exportálásával vagy törlésével).

8.2 **Egyéb kötelezettségek:** az Adatfeldolgozó a rendelkezésére álló információk alapján segíti az Adatkezelőt a GDPR 32–36. cikke szerinti kötelezettségek (biztonság, incidensbejelentés, hatásvizsgálat, előzetes konzultáció) teljesítésében.

## 9. Adatvédelmi incidensek

9.1 Az Adatfeldolgozó az Adatkezelő adatait érintő adatvédelmi incidensről való tudomásszerzését követően indokolatlan késedelem nélkül, de legkésőbb **[KITÖLTENDŐ: 48] órán belül** értesíti az Adatkezelőt.

9.2 Az értesítés – amennyiben rendelkezésre áll – tartalmazza az incidens jellegét, az érintettek és az adatok kategóriáit és hozzávetőleges számát, a valószínű következményeket, a megtett vagy tervezett intézkedéseket és a kapcsolattartó elérhetőségét. A még nem ismert információkat később, részletekben is közölheti.

9.3 Az Adatfeldolgozó minden incidenst dokumentál, és a [megfelelőségi dokumentáció 10. pontja](compliance.hu.md#10-adatvédelmi-incidens-kezelése) szerint jár el.

## 10. Törlés vagy visszaadás a szerződés végén

A Szolgáltatás megszűnésekor az Adatfeldolgozó az Adatkezelő választása szerint [KITÖLTENDŐ: 30] napon belül visszaadja (gépi feldolgozásra alkalmas exportként) vagy törli az Adatkezelő számára kezelt összes személyes adatot, és törli a meglévő másolatokat, kivéve, ha uniós vagy tagállami jog tárolást ír elő. A csak a feladatok memóriájában kezelt adatok az 5.2 pont szerint addigra már törlődtek. Kérésre a törlést írásban igazolja.

## 11. Ellenőrzés és tájékoztatás

11.1 Az Adatfeldolgozó rendelkezésre bocsát minden információt, amely a szerződésnek és a GDPR 28. cikkének való megfelelés igazolásához szükséges, ideértve a mellékleteket, az adatkezelési nyilvántartást és a megfelelőségi dokumentáció vonatkozó részeit.

11.2 Az Adatkezelő (vagy az általa megbízott, titoktartásra kötelezett auditor) legalább [KITÖLTENDŐ: 30] nappal előre írásban bejelentett ellenőrzést, ideértve helyszíni vizsgálatot is, végezhet munkaidőben, az Adatfeldolgozó működésének aránytalan zavarása nélkül. A költségeket mindkét fél maga viseli, kivéve, ha az ellenőrzés az Adatfeldolgozó lényeges szerződésszegését tárja fel.

## 12. Felelősség és záró rendelkezések

12.1 A felelősségre a GDPR 82. cikke és [KITÖLTENDŐ: az alapszerződés felelősségi pontja] irányadó.

12.2 Ha e szerződés és az alapszerződés adatvédelmi kérdésben eltér, e szerződés az irányadó.

12.3 A szerződésre a magyar jog irányadó. [KITÖLTENDŐ: illetékes bíróság vagy vitarendezés.]

12.4 A szerződés csak írásban módosítható.

Kelt: [KITÖLTENDŐ: hely, dátum]

| Adatkezelő | Adatfeldolgozó |
| --- | --- |
| Név, beosztás: | Név, beosztás: |
| Aláírás: | Aláírás: |

---

## 1. melléklet – Az adatkezelés leírása

| Tétel | Részletek |
| --- | --- |
| Az érintettek köre | (a) Az Adatkezelő Szolgáltatást használó munkatársai (felhasználók); (b) a feltöltött dokumentumokban szereplő személyek (pl. szerzők, esettanulmányok szereplői) |
| A személyes adatok köre | (a) Felhasználók: e-mail-cím, jelszó-lenyomat, mentett tesztek (cím, PDF, létrehozás ideje), álnevesített feladat-metaadatok. (b) Dokumentumokban szereplő személyek: a feltöltött oktatási anyagban szereplő személyes adatok |
| Különleges adatok | Nem szándékolt. A felhasználóknak nem szabad különleges adatot (9. cikk) vagy diákokra vonatkozó adatot feltölteniük; a feltöltő felület ezt megerősítteti |
| Az adatkezelés jellege | Szövegkinyerés, szövegrészekre bontás, vektoros keresés, kérdésgenerálás nagy nyelvi modellel, emberi ellenőrzés a böngészőben, PDF-export; a tesztek mentése igény szerint |
| Cél | Tesztkérdések készítése az Adatkezelő oktatási anyagaiból |
| Az adatkezelés helye | Az Adatfeldolgozó szervere, [KITÖLTENDŐ: ország]. Ha a `LOCAL_ONLY` nincs bekapcsolva, a kiválasztott szövegrészeket az Óbudai Egyetem GenAI szolgáltatása (Magyarország) dolgozza fel. A felhasználó minden feltöltés előtt látja, hol dolgozzuk fel a dokumentumot, és választhatja helyette a helyi modellt |
| Az Adatkezelő által választott beállítás | `LOCAL_ONLY` = [KITÖLTENDŐ: true / false] |
| Megőrzés | Dokumentumok és származtatott adatok: a feladat ideje, legfeljebb 60 perc. Tesztvázlatok: legfeljebb 60 perc a szerveren. Mentett tesztek: a felhasználó törléséig, legfeljebb 12 hónap. MI működési napló (tartalom nélkül): 30 nap. Szervernaplók: legfeljebb 14 nap |

## 2. melléklet – Technikai és szervezési intézkedések

- Titkosítás átvitel közben: HTTPS/TLS minden forgalomra (Cloudflare Tunnel).
- Zéró megőrzés: a dokumentumokat és a származtatott adatokat memóriában kezeljük, és minden feladat után töröljük; a feladateredmények 60 perc után lejárnak; a feltöltésekből semmi nem kerül biztonsági mentésbe.
- Adattakarékos naplózás: az MI működési napló csak lenyomatokat és hosszakat tárol, dokumentumszöveget soha; a hozzáférési napló rövidített IP-címet tárol, paraméterek nélkül.
- Helyi mód (`LOCAL_ONLY=true`): a dokumentum szövege semmilyen külső szolgáltatáshoz nem kerül.
- Hozzáférés-kezelés: az éles rendszerhez csak név szerint kijelölt munkatársak férnek hozzá, többfaktoros hitelesítéssel a kódtárolón és a hálózati szolgáltatónál. [KITÖLTENDŐ: állapot]
- A jelszavakat csak sózott, visszafejthetetlen lenyomatként tároljuk (a hitelesítési szolgáltatással). [KITÖLTENDŐ: állapot]
- Minden generált tesztet ember ellenőriz felhasználás előtt (MI-rendelet 14. cikk); a PDF feltünteti, hogy a tartalom MI-asszisztenssel készült, és melyik modell írta.
- Érintetti kérelmek és incidensek kezelése a megfelelőségi dokumentáció 9–10. pontja szerint.
- Az intézkedések évenkénti felülvizsgálata.

## 3. melléklet – Engedélyezett további adatfeldolgozók

| További adatfeldolgozó | Szolgáltatás | Adatok | Helyszín | Továbbítási eszköz |
| --- | --- | --- | --- | --- |
| [KITÖLTENDŐ: tárhelyszolgáltató] | Szerverüzemeltetés | A Szolgáltatás összes adata | [KITÖLTENDŐ] | — |
| Cloudflare, Inc. | Biztonságos hálózati hozzáférés (tunnel) | Hálózati forgalmi metaadatok (IP) | USA / globális | EU–USA adatvédelmi keret vagy általános szerződési feltételek |
| Óbudai Egyetem (genai.uni-obuda.hu) – csak ha a `LOCAL_ONLY` ki van kapcsolva | Nyelvimodell-futtatás | Dokumentumrészletek, promptok | Magyarország | — |
| [KITÖLTENDŐ: e-mail-szolgáltató] | Fiókkal kapcsolatos e-mailek | E-mail-cím, e-mail tartalma | [KITÖLTENDŐ] | [KITÖLTENDŐ] |
