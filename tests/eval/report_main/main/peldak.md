# Példakérdések a hibaelemzéshez

Módszerenként egy jó és egy rossz kérdés a független bíráló (LLM) értékelése alapján. Jó: a forrás igazolja a megjelölt választ, a vak megoldás nem hibázott, és a legmagasabb a négy szempont átlaga. Rossz: a forrás nem igazolja a választ (vagy a vak megoldó mást jelölt), azon belül a legalacsonyabb átlag.

## E4b – Ellenőrzés, szervermodell

### Jó példa – `en-lifesciences-short-04`, seed 1

**Which statement correctly compares how dsRNA, +ssRNA, and -ssRNA viral genomes produce translatable +ssRNA?**

A. +ssRNA can be translated directly, -ssRNA is copied by viral RdRP into +ssRNA, and dsRNA uses its negative strand as a template for RdRP to make +ssRNA. ✓
B. +ssRNA must first be converted into dsDNA by reverse transcriptase, -ssRNA is translated directly, and dsRNA is copied into dsDNA before translation.
C. -ssRNA can be translated directly by host ribosomes, +ssRNA must be copied into -ssRNA first, and dsRNA is translated directly without making +ssRNA.
D. dsRNA is translated directly by host ribosomes, +ssRNA must be converted into -ssRNA by RdRP, and -ssRNA is copied into dsDNA before translation.

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source clearly supports option A and contradicts B, C, and D; the question is well‑phrased, the distractors are plausible misconceptions, and the task matches an easy‑level recall/understanding objective.
- Alátámasztó mondat: „If a virus has a +ssRNA genome, it can be translated directly... However, if a virus contains a −ssRNA genome, the host ribosomes cannot translate it until the −ssRNA is replicated into +ssRNA by viral RNA-dependent RNA polymerase (RdRP)... The RdRP is also an important enzyme for the replication of dsRNA viruses, because it uses the negative strand of the double-stranded genome as a template to create +ssRNA.”

### Rossz példa – `en-lifesciences-short-04`, seed 1

**Which statement best answers whether a latent phage is undetectable in a bacterium?**

A. A latent phage is not undetectable; latent viral DNA may be present without active viral production. ✓
B. A latent phage is always undetectable because no viral particles are made during the latent stage.
C. A latent phage is detectable only when it leaves the lysogenic cycle and enters lytic growth.
D. A latent phage is absent from the bacterium until it begins producing viral particles during lysis.

- Forrással igazolt: nem; vakon megoldva: igen; pontszámok (1–5): helyesség 1, érthetőség 5, disztraktorok 1.0, szintillesztés 4
- A bíráló indoklása: The source material does not provide any information confirming the marked answer, nor does it refute the distractors; therefore the key is unsupported and the distractors are not clearly wrong.

## E2 – Tervezés + ellenőrzés

### Jó példa – `hu-immune`, seed 1

**Az immunrendszer által azonosított molekulák, amelyek kiváltják az immunválaszt, milyen nevet kapnak?**

A. Antigének ✓
B. Antiteste
C. Fertőző agentek
D. Vakcinák

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source explicitly defines antigens as the molecules that trigger the immune response, making the marked answer correct and the distractors plausible yet incorrect.
- Alátámasztó mondat: „A betolakodókat azonosító molekulákat, amelyek kiváltják az immunválaszt, antigéneknek nevezzük.”

### Rossz példa – `hu-coffee`, seed 1

**A Robusta kávé alacsonyabb területeken termelésének és koffeintartalma jellemzői.**

A. A Robusta kávé alacsonyabb területeken termelésének és koffeintartalma 1.5-2 során fejlődik. ✓
B. A Robusta kávé alacsonyabb területeken termelésének és koffeintartalma 0.5-1 során fejlődik.
C. A Robusta kávé alacsonyabb területeken termelésének és koffeintartalma 2.5-3 során fejlődik.
D. A Robusta kávé alacsonyabb területeken termelésének és koffeintartalma 3-4 során fejlődik.

- Forrással igazolt: nem; vakon megoldva: igen; pontszámok (1–5): helyesség 1, érthetőség 3, disztraktorok 1.0, szintillesztés 1
- A bíráló indoklása: The source mentions only that Robusta’s caffeine content is about twice that of Arabica and that it grows at lower altitudes, but provides no numeric range, so the marked answer is unsupported and all options are unsubstantiated.

## B-doc-S – Teljes dokumentum, szerver

### Jó példa – `hu-immune`, seed 3

**Melyik állítás igaz a védőoltások működésére?**

A. Az immunológiai memórián alapulnak: a memóriasejtek azonnal felismerik a kórokozót, és tünetek kialakulása előtt elpusztítják. ✓
B. A veleszületett immunitás nem specifikus válaszán alapulnak.
C. A bőr és a nyálkahártyák fizikai gátját erősítik.
D. A makrofágok bekebelező működését váltják ki.

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source explicitly states that vaccines work via immunological memory, making option A correct; the other options are incorrect yet plausible misconceptions, providing good distractors.
- Alátámasztó mondat: „A szerzett immunrendszer legnagyobb előnye az immunológiai memória... Ha ugyanaz a kórokozó a jövőben újra támad, ezek a memóriasejtek azonnal felismerik, és még azelőtt elpusztítják, ... Ezen az elven alapul a védőoltások (vakcinák) működése is.”

### Rossz példa – `en-law-long-03`, seed 1

**What is the access economy?**

A. A resource circulation system in which consumers participate as both providers and obtainers of resources ✓
B. A government program that provides free housing to low-income workers
C. A traditional retail model where businesses sell goods to individual consumers
D. A type of corporate campus that offers free amenities to all employees

- Forrással igazolt: nem; vakon megoldva: –; pontszámok (1–5): helyesség 1, érthetőség 5, disztraktorok 1.0, szintillesztés 1
- A bíráló indoklása: The source material never mentions the 'access economy', so the marked answer is unsupported and all options are off‑topic. The question is clear, but it does not align with the source content, making it unsuitable for this exam.

## E2h – Ellenőrzés + hibrid keresés

### Jó példa – `hu-coffee`, seed 1

**Melyik faj a globális kávétermelésben leggyakrabban használt, és milyen jellegzetes ízét és színét nyeri el a pörkölés során?**

A. A Robusta, amely erőteljesebb, kesernyészabb ízzal és sötét pörkölés során nyeri el a kávébab ízét és színét.
B. Az Arabica, amely lágyabb, összetettebb és savasabb ízzal és világos pörkölés során nyeri el a kávébab ízét és színét. ✓
C. A Robusta, amely lágyabb, összetettebb és savasabb ízzal és világos pörkölés során nyeri el a kávébab ízét és színét.
D. Az Arabica, amely erőteljesebb, kesernyészabb ízzal és sötét pörkölés során nyeri el a kávébab ízét és színét.

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source clearly states Arabica dominates global production, has a mild, complex, acidic flavor, and that light roasting preserves these characteristics, making option B the only correct choice.
- Alátámasztó mondat: „Az Arabica a globális termelés mintegy 70 százalékát teszi ki; ... Íze lágyabb, összetettebb és savasabb. ... a világosabb pörkölés jobban megőrzi a kávébab eredeti, gyümölcsös ízjegyeit.”

### Rossz példa – `hu-immune`, seed 1

**Melyik a specifikus, de lassabb védelmi vonal, amely a korábbi fertőzésekről memóriát alakíthat?**

A. A B-sejtek
B. A makrofágok
C. A T-sejtek
D. A B-sejtek memóriasejtté alakulnak ✓

- Forrással igazolt: nem; vakon megoldva: igen; pontszámok (1–5): helyesség 1, érthetőség 4, disztraktorok 1.0, szintillesztés 2
- A bíráló indoklása: The source describes the acquired (szerzett) immune system as the specific, slower line with memory; none of the options name this line, and option D only mentions B‑cell memory, not the line itself. Moreover, options A and C are actually parts of the specific slower line, so they are not wrong distractors.

## E4 – Alapmódszer, szervermodell

### Jó példa – `en-lifesciences-short-04`, seed 3

**How many words are in Link to Learning?**

A. 3 ✓
B. 2
C. 4
D. 5

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source explicitly shows the phrase "Link to Learning", which contains three words, making the marked answer correct and the other options clearly wrong yet plausible distractors.
- Alátámasztó mondat: „Link to Learning”

### Rossz példa – `en-economics-short-01`, seed 2

**How many distinct words are shown?**

A. 1 ✓
B. 2
C. 3
D. 4

- Forrással igazolt: nem; vakon megoldva: igen; pontszámok (1–5): helyesség 1, érthetőség 4, disztraktorok 2.0, szintillesztés 2
- A bíráló indoklása: The source material contains no words, so the correct answer would be 0, not the marked 1. Consequently the key is unsupported and all options are incorrect. The question is clear but mismatched to the source, and the distractors lack justification.

## E2f – Ellenőrzés vak teszt nélkül

### Jó példa – `hu-immune`, seed 1

**Melyik a specifikus, de lassabb védelmi vonal, amely memóriát alakíthat ki?**

A. A veleszületett immunitás, mert gyorsan reagál minden idegen anyag ellen.
B. A szerzett immunitás, mert lassan aktiválódik, de rendkívül specifikus. ✓
C. A makrofágok, mert gyorsan reagálnak idegen anyagok ellen.
D. A bőr, mert a leggyorsabban reagál az idegen anyagok ellen.

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source clearly states that the acquired immune system is slower, specific and capable of memory, making option B correct; the other options are plausible but incorrect, yielding a high‑quality medium‑difficulty MCQ.
- Alátámasztó mondat: „Ez a folyamat lassabb, gyakran napokat vesz igénybe, cserébe viszont rendkívül specifikus. A szerzett immunrendszer legnagyobb előnye az immunológiai memória.”

### Rossz példa – `hu-gametheory`, seed 1

**Melyik kimenet szuboptimális, de társadalmi előnyben van?**

A. A két bűnöző mindketten vall, így mindketten 2 év börtönt kapnak. ✓
B. A két bűnöző mindketten hallgat, így mindketten 1 év börtönt kapnak.
C. A két bűnöző egyik vall, az másik hallgat, így a valló szabadon távozhat, a hallgató 3 év börtönt kap.
D. A két bűnöző mindketten hallgat, így mindketten 1 év börtönt kapnak, ami mindkettejük számára szigorúan jobb eredmény lenne.

- Forrással igazolt: nem; vakon megoldva: igen; pontszámok (1–5): helyesség 1, érthetőség 2, disztraktorok 2.0, szintillesztés 2
- A bíráló indoklása: The source does not support the marked answer; it describes the both‑confess outcome as suboptimal and not socially beneficial. All other options are on‑topic but wrong for the asked criterion.

## E2x – Ellenőrzés más modellel

### Jó példa – `hu-gametheory`, seed 1

**Milyen döntéshozatali paradoxon jellemző a racionális döntéshozatal szintjén a Fogolydilemma esetében, amikor mindkét fél racionális, de a kollektív eredmény szuboptimális?**

A. A racionális döntéshozatal szintjén a döntések sorozata mindkét fél számára szuboptimális, mivel a vallás a legjobb eredmény.
B. A racionális döntéshozatal szintjén a döntések sorozata mindkét fél számára optimális, mivel mindkét fél racionális és a vallás a legjobb eredmény.
C. A racionális döntéshozatal szintjén a döntések sorozata mindkét fél számára szuboptimális, mivel a hallgatás a legjobb eredmény, de a racionális döntések sorozata vallást eredményez. ✓
D. A racionális döntéshozatal szintjén a döntések sorozata mindkét fél számára szuboptimális, mivel a Nash-egyensúly a legjobb eredmény.

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source explicitly states that the rational individual decisions lead to a collectively suboptimal outcome, matching option C; the other options contradict the source but are plausible distractors.
- Alátámasztó mondat: „Ugyanakkor ez a kimenetel nem Pareto-optimális, hiszen ha mindketten hallgattak volna ... csak 1-1 évet kapnának, ami mindkettejük számára szigorúan jobb eredmény lenne. ... a tisztán önérdekkövető, racionális egyéni döntések sorozata hogyan vezethet egy kollektíven irracionális és szuboptimális állapothoz.”

### Rossz példa – `hu-gametheory`, seed 1

**A Fogolydilemma esetében, amikor mindkét bűnöző racionális, de a kollektív eredmény szuboptimális, milyen állapotot jellemzően értjük meg?**

A. A szuboptimális állapotot, amely nem stabil, mert mindkét bűnöző mindig kockázatosan vall
B. A szuboptimális állapotot, amely stabil, de nem szuboptimális ✓
C. A szuboptimális állapotot, amely nem stabil, mert mindkét bűnöző mindig kockázatosan hallgat
D. A szuboptimális állapotot, amely stabil, mert mindkét bűnöző mindig kockázatosan vall

- Forrással igazolt: nem; vakon megoldva: nem; pontszámok (1–5): helyesség 1, érthetőség 4, disztraktorok 1.0, szintillesztés 3
- A bíráló indoklása: The source describes the Prisoner's Dilemma equilibrium as stable but suboptimal, which matches option D, not the marked answer B. Therefore the marked answer is unsupported and another option is correct.

## E3 – Ellenőrzés + fogalomgráf

### Jó példa – `hu-coffee`, seed 1

**Melyik növényfajt a kávétermelésben a leggyakrabban használt?**

A. Arabica ✓
B. Robusta
C. Libertica
D. Excelsa

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source clearly states Arabica accounts for about 70% of global coffee production, making it the most commonly used species; the other options are either less common or not mentioned, and the question is a straightforward recall.
- Alátámasztó mondat: „Az Arabica a globális termelés mintegy 70 százalékát teszi ki; ...”

### Rossz példa – `hu-gametheory`, seed 1

**A Fogolydilemma játékelméleti példában, amelyben két bűnözőt elfog a rendőrség, melyik állapot a társadalmi eredmények szempontjából a legjobb?**

A. Mindkettő hallgat, tehát mindketten 1 év börtönt kapnak.
B. Mindkettő vall, tehát mindketten 2 év börtönt kapnak.
C. A valló szabadon távozik, míg a hallgató 3 év börtönt kap.
D. Nincs megfelelő állapot, mert a játékelmélet nem garantálja a társadalmi eredmények optimális kimenetét. ✓

- Forrással igazolt: nem; vakon megoldva: nem; pontszámok (1–5): helyesség 1, érthetőség 4, disztraktorok 2.0, szintillesztés 2
- A bíráló indoklása: A forrás egyértelműen támogatja az A opciót, így a megjelölt D válasz hibás, ezért a feladat nem alkalmas használatra.
- Alátámasztó mondat: „A forrás leírja: "Ha mindketten hallgatnak, mindketten 1 év börtönt kapnak... Ha mindketten vallanak, mindketten 2 év börtönt kapnak... Ha az egyik vall, a másik hallgat, a valló szabadon távozhat (0 év), míg a hallgató 3 év börtönt kap." Ezek alapján a legkisebb összes börtönidő a mindkét hallgatás esetében van, tehát az A opció a legjobb társadalmi eredmény.”

## E1 – Tervezés

### Jó példa – `hu-gametheory`, seed 1

**Milyen döntéshozatali paradoxon jellemző a racionális döntéshozatal szintjén a Fogolydilemma esetében, amikor mindkét fél racionális, de a kollektív eredmény szuboptimális?**

A. A racionális döntéshozatal szintjén a döntések sorozata mindkét fél számára szuboptimális, mivel a vallás a legjobb eredmény.
B. A racionális döntéshozatal szintjén a döntések sorozata mindkét fél számára optimális, mivel mindkét fél racionális és a vallás a legjobb eredmény.
C. A racionális döntéshozatal szintjén a döntések sorozata mindkét fél számára szuboptimális, mivel a hallgatás a legjobb eredmény, de a racionális döntések sorozata vallást eredményez. ✓
D. A racionális döntéshozatal szintjén a döntések sorozata mindkét fél számára szuboptimális, mivel a Nash-egyensúly a legjobb eredmény.

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source explicitly describes the Prisoner's Dilemma paradox as rational decisions leading to a suboptimal collective outcome, matching option C; the other options misstate the optimal outcome or Nash equilibrium, making them plausible distractors.
- Alátámasztó mondat: „Ez a kimenetel nem Pareto-optimális, hiszen ha mindketten hallgattak volna ... csak 1-1 évet kapnának ... a tisztán önérdekkövető, racionális egyéni döntések sorozata hogyan vezethet egy kollektíven irracionális és szuboptimális állapothoz.”

### Rossz példa – `en-economics-short-01`, seed 1

**Which of the following transactions would result in a decrease in the Cost of Goods Sold and an increase in the Inventory account on the income statement?**

A. Recording the purchase of raw materials on credit
B. Recording the payment of a utility bill
C. Recording the sale of goods to a customer who has not yet paid
D. Recording the receipt of raw materials from a supplier and recording it as a debit to Inventory and a credit to Accounts Payable ✓

- Forrással igazolt: nem; vakon megoldva: igen; pontszámok (1–5): helyesség 1, érthetőség 4, disztraktorok 1.0, szintillesztés 3
- A bíráló indoklása: The source material does not discuss inventory, COGS, or related transactions, so it cannot support the marked answer or evaluate the distractors.

## E5a – Régi darabolás

### Jó példa – `hu-immune`, seed 1

**Melyik a T-segítő sejtek feladata?**

A. Riadóztatják a rendszer többi elemét ✓
B. Elpusztítják a fertőzött sejteket
C. Termelik antitesteit
D. Segítenek a B-sejtekben

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source explicitly states the role of helper T cells, making option A correct and the others unsupported; the question is clear and the distractors are plausible yet wrong.
- Alátámasztó mondat: „A T-segítő sejtek riadóztatják a rendszer többi elemét.”

### Rossz példa – `hu-gametheory`, seed 1

**A Pareto-optimalitás azt jelenti, hogy a kimenet a legtöbb embert érzi meg, ugyanakkor senki helyzetén nem lehet javítani anélkül, hogy valaki másé ne romlana.**

A. Helyes ✓
B. Nem helyes, mert a Pareto-optimalitás azt jelenti, hogy minden embert érzi meg
C. Nem helyes, mert a Pareto-optimalitás azt jelenti, hogy a kimenet nem javítható meg
D. Nem helyes, mert a Pareto-optimalitás azt jelenti, hogy a kimenet nem javítható meg, ugyanakkor valaki másé romlásával

- Forrással igazolt: nem; vakon megoldva: nem; pontszámok (1–5): helyesség 1, érthetőség 3, disztraktorok 1.0, szintillesztés 2
- A bíráló indoklása: The source defines Pareto-optimality without the phrase 'legtöbb embert érzi meg', making the marked answer incorrect; option D actually matches the source definition, so it is not a valid distractor.

## E5c – Fix darabolás

### Jó példa – `hu-immune`, seed 3

**Melyik állítás nem felel meg a T-sejtek működésének?**

A. A T-sejtek közvetlenül elpusztítják a fertőzött sejteket ✓
B. A T-segítő sejtek riadóztatják a rendszer többi elemét
C. A citotoxikus T-sejtek közvetlenül elpusztítják a fertőzött sejteket
D. A T-sejtek egy része közvetlenül elpusztítja a fertőzött sejteket

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source explicitly states that only a subset of T cells (cytotoxic) destroy infected cells, making option A inaccurate while B, C, and D are accurate and plausible distractors.
- Alátámasztó mondat: „A T-sejtek egy része (a citotoxikus T-sejtek) közvetlenül elpusztítja a fertőzött sejteket”

### Rossz példa – `hu-immune`, seed 3

**Melyik állítás nem felel meg a B-sejtek működésének?**

A. A B-sejtek feladata az antitestek termelése ✓
B. A B-sejtek feladata az antitestek termelése
C. A B-sejtek feladata az antitestek termelése
D. A B-sejtek feladata az antitestek termelése

- Forrással igazolt: nem; vakon megoldva: –; pontszámok (1–5): helyesség 1, érthetőség 2, disztraktorok 1.0, szintillesztés 1
- A bíráló indoklása: The source confirms that B cells produce antibodies, so the marked answer (a true statement) cannot be the correct choice for a 'not true' question; all options are identical and correct, making the item invalid.

## B-doc-L – Teljes dokumentum, helyi

### Jó példa – `hu-gametheory`, seed 2

**A játékelméletben a Nash-egyensúly a stabil állapotot feltételezi, de nem garantálja a társadalmilag vagy kollektíven optimális kimenetelt.**

A. Helyes válasz ✓
B. Helytelen válasz 1: A játékelméletben a Nash-egyensúly a stabil állapotot feltételezi, de garantálja a társadalmilag vagy kollektíven optimális kimenetelt.
C. Helytelen válasz 2: A játékelméletben a Nash-egyensúly nem feltételezi a stabil állapotot, de garantálja a társadalmilag vagy kollektíven optimális kimenetelt.
D. Helytelen válasz 3: A játékelméletben a Nash-egyensúly nem feltételezi a stabil állapotot, és nem garantálja a társadalmilag vagy kollektíven optimális kimenetelt.

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source explicitly confirms the marked answer and refutes all distractors; the question is clear and the distractors are plausible yet incorrect, matching a hard‑level evaluation task.
- Alátámasztó mondat: „Bár a Nash-egyensúly stabil állapotot feltételez, nem garantálja a társadalmilag vagy kollektíven optimális kimenetelt...”

### Rossz példa – `en-law-long-03`, seed 1

**What is a potential drawback of job sharing and flextime?**

A. Increased flexibility
B. Reduced predictability ✓
C. Increased productivity
D. Improved work-life balance

- Forrással igazolt: nem; vakon megoldva: igen; pontszámok (1–5): helyesség 1, érthetőség 5, disztraktorok 1.0, szintillesztés 1
- A bíráló indoklása: The source material does not mention job sharing or flextime, so the marked answer is unsupported and the distractors are neither addressed nor contradicted.

## E5b – Szórás alapú darabolás

### Jó példa – `hu-coffee`, seed 3

**Melyik fajnak a koffeintartalma legnagyobb?**

A. Robusta ✓
B. Arabica
C. Excelsa
D. Libertena

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source explicitly states Robusta has almost double the caffeine of Arabica, making it the clear correct answer; the other options are either contradicted or not mentioned, and the question cleanly tests factual recall.
- Alátámasztó mondat: „Robusta alacsonyabb területeken is megél, sokkal ellenállóbb a kártevőkkel és az időjárással szemben, koffeintartalma pedig majdnem kétszerese az Arabicáénak.”

### Rossz példa – `en-humanities-medium-02`, seed 2

**What happens if a bill is not passed by the legislative body?**

A. It becomes law
B. It is sent to the executive branch
C. It is discarded ✓
D. It is returned to the committee

- Forrással igazolt: nem; vakon megoldva: –; pontszámok (1–5): helyesség 1, érthetőség 5, disztraktorok 1.0, szintillesztés 1
- A bíráló indoklása: The source material provides no information about the legislative process, so it cannot support the marked answer or evaluate the distractors; the question is clear but unrelated to the source.

## E0 – Alapmódszer

### Jó példa – `hu-immune`, seed 3

**Milyen jellegű a veleszületett immunitás?**

A. Specifikus
B. Nem specifikus ✓
C. Adaptív
D. Lassú

- Forrással igazolt: igen; vakon megoldva: igen; pontszámok (1–5): helyesség 5, érthetőség 5, disztraktorok 5.0, szintillesztés 5
- A bíráló indoklása: The source explicitly states that innate immunity is non‑specific, making option B correct; the other options are contradicted by the text but are plausible misconceptions, yielding a high‑quality MCQ.
- Alátámasztó mondat: „Ez az ág nem specifikus, ami azt jelenti, hogy minden betolakodóval szemben ugyanazokkal a fegyverekkel lép fel.”

### Rossz példa – `hu-gametheory`, seed 3

**Mikor kapja A 2 évet?**

A. Ha B hallgat ✓
B. Ha B vall
C. Ha B szerviz
D. Ha B konkurenccia

- Forrással igazolt: nem; vakon megoldva: nem; pontszámok (1–5): helyesség 1, érthetőség 4, disztraktorok 1.0, szintillesztés 2
- A bíráló indoklása: The source says A gets 2 years when B confesses, so the marked answer (A) is wrong; option B is actually correct.
