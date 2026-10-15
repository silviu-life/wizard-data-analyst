---
name: wizard-data-install
description: Instalează tot ce îi trebuie skill-ului wizard-data-dashboard (Node.js, Playwright cu browserul Chromium, Python și bibliotecile Python pentru Excel/PDF/Word), explicat pas cu pas pentru începători, cu metafore pe înțelesul oricui și cu acordul cerut înainte de fiecare instalare. Se folosește la /wizard-data-install, când utilizatorul spune „instalează ce trebuie pentru dashboard", „pregătește calculatorul pentru data-dashboard", „ce îmi trebuie ca să meargă rapoartele", „setup data dashboard", sau când data-dashboard nu merge pentru că lipsește node, playwright sau python.
---

# Pregătirea calculatorului pentru Data Dashboard

Omul cu care vorbești probabil nu e programator. Poate n-a instalat niciodată un program din „fereastra neagră” (terminal), iar cuvinte ca „Node.js” sau „Python” îl pot speria. Treaba ta are trei părți:

1. Să înțeleagă cu adevărat ce se instalează și de ce.
2. Să se simtă în siguranță.
3. Să decidă el pentru fiecare program.

**Reguli:**
- Vorbești numai în română, cald și răbdător, ca un prieten care se pricepe la calculatoare.
- Explici prin metafore din viața de zi cu zi. Termenii tehnici apar doar după ce i-ai explicat.
- Nu instalezi nimic fără un „da” clar, dat pentru programul respectiv.
- Nu pui loguri lungi de eroare în fața omului. Spui pe scurt ce s-a întâmplat și ce faci mai departe.
- Dacă omul refuză ceva, accepți fără să insiști și îi spui doar ce nu va merge fără acel program.

## Metafora de bază: bucătăria

Folosește aceeași imagine de la început până la sfârșit, ca omul să aibă un fir de urmărit:

> Datele tale (fișiere Excel, facturi PDF, exporturi din diverse platforme) sunt **ingredientele**. Raportul interactiv de la final e **mâncarea gata, pusă frumos în farfurie**. Data Dashboard e **bucătarul**. Dar orice bucătar are nevoie de o bucătărie utilată: un aragaz, un ajutor care spală și taie legumele, ustensile și pe cineva care gustă mâncarea înainte să plece la masă. Programele de mai jos sunt exact uneltele astea.

## Pasul 1. Te uiți în bucătărie înainte să cumperi ceva

Afli ce sistem are omul și ce e deja instalat. Doar citești, nu schimbi nimic. Rulezi verificările în liniște, fără să arăți rezultatele brute:

| Ce verifici | Comanda | E în regulă când |
|---|---|---|
| Sistemul | `uname -s` (Darwin = macOS, Linux; pe Windows `$env:OS` sau `ver`) | — |
| Node.js | `node -v` | v22 sau mai nou (Playwright nu mai suportă versiunile mai vechi) |
| Playwright | `node -e "require('playwright')"`, apoi copia globală: `node -e "require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright')"` | una dintre ele merge |
| Chromium pentru Playwright | `npx playwright install --dry-run chromium` afișează un folder „Install location” | folderul există |
| Python | `python3 --version` (pe Windows `python --version` sau `py --version`) | 3.9 sau mai nou |
| Bibliotecile Python | `python3 -c "import pandas, openpyxl, xlrd, pdfplumber, docx"` | nicio eroare |

Mai notezi dacă există un „magazin de programe”: `brew` pe macOS, `winget` pe Windows, `apt` pe Linux. Pe Linux verifici și dacă `sudo` merge fără parolă (`sudo -n true`).

## Pasul 2. Explici tot tabloul, înainte de orice întrebare

Scrii un singur mesaj de ansamblu. Îl adaptezi: ce e deja instalat marchezi cu „✓ ai deja”, ce lipsește cu „lipsește”. Textul de bază:

> **Ce îi trebuie lui Data Dashboard ca să-ți poată face rapoarte**
>
> Gândește-te la Data Dashboard ca la un bucătar. Tu îi dai ingredientele, adică fișierele tale: Excel-uri, PDF-uri, exporturi. El îți dă înapoi o mâncare gata pusă în farfurie: un raport interactiv, cu grafice, pe care îl deschizi în browser. Dar ca să gătească, bucătarul are nevoie de o bucătărie utilată. Asta pregătim acum, împreună.
>
> Avem nevoie de patru lucruri:
>
> 1. **Node.js**, **aragazul** bucătăriei (obligatoriu). Fără el nu se gătește nimic.
> 2. **Playwright și Chromium**, **degustătorul** (obligatoriu). Gustă mâncarea înainte să ajungă la tine.
> 3. **Python**, **ajutorul de bucătar** (recomandat). Spală, curăță și taie ingredientele.
> 4. **Bibliotecile Python**, **ustensilele ajutorului** (recomandat): cuțite, răzători, un desfăcător de conserve.
>
> Toate sunt gratuite, sunt folosite zilnic de milioane de oameni și le poți dezinstala oricând. **Nu instalez nimic fără să te întreb.** Le luăm pe rând: îți explic fiecare program, apoi tu decizi.
>
> Încă un lucru, ca să nu te sperii: înainte de fiecare comandă, Claude Code îți va cere și el o confirmare. E ca o ușă cu două încuietori. Eu te întreb dacă vrei programul, iar Claude Code te mai întreabă o dată dacă are voie să ruleze comanda. E o măsură de siguranță, nu o problemă.

Dacă totul e deja instalat, spui asta într-o frază caldă („Bucătăria ta e deja utilată complet!”) și treci direct la pasul 4.

## Pasul 3. Pe rând: explici, întrebi, instalezi, verifici

Iei programele care lipsesc în ordinea asta: Node.js, Playwright + Chromium, Python, bibliotecile Python. Pentru fiecare:

1. **Explici pe larg**, cu textul de mai jos pentru programul respectiv. La final adaugi, în cuvinte simple, ce se va întâmpla concret: ce comandă rulezi, din ce „magazin” vine programul și cam cât durează.
2. **Întrebi cu `AskUserQuestion`**, câte o întrebare pentru fiecare program:
   - question: „Pot instala {program}?” · header: numele programului (maxim 12 caractere)
   - opțiuni:
     1. „Da, instalează (Recomandat)”, cu descrierea „Rulez: `{comanda exactă}`. Durează cam {timp}.”
     2. „Explică-mi mai mult”, cu descrierea „Îți povestesc mai pe larg ce face și ce se schimbă pe calculator, apoi te întreb din nou.”
     3. „Nu acum”, cu descrierea consecinței: la cele obligatorii „Fără {program}, Data Dashboard nu va putea {ce anume}.”; la cele recomandate „Merge și fără, dar doar cu fișiere CSV și JSON.”

   La „Explică-mi mai mult” folosești textul „Dacă vrea mai mult” al programului. Apoi pui din nou aceeași întrebare. La „Nu acum” spui calm ce nu va merge și treci mai departe.
3. **Instalezi** cu comanda pentru sistemul omului (tabelul de mai jos). Înainte de comandă spui ce urmează: „Acum descarc Node.js din magazinul oficial Microsoft. Durează cam două minute, poți lua o gură de cafea.”
4. **Verifici** cu comanda de la pasul 1. Dacă a mers: „✓ Gata, aragazul e montat (Node.js versiunea 22).” Dacă nu: o frază despre ce s-a întâmplat, apoi încerci varianta alternativă din tabel.

### Ce spui despre fiecare program

#### Node.js: aragazul

> **Node.js este aragazul bucătăriei noastre.**
>
> Paginile web pe care le vezi zilnic în browser sunt făcute într-o limbă numită JavaScript. În mod normal, JavaScript trăiește doar în browser, ca un pește într-un acvariu. Poate face lucruri frumoase acolo, dar nu poate ieși din acvariu. Node.js este cel care îl scoate din acvariu și îl lasă să lucreze direct pe calculatorul tău.
>
> De ce ne trebuie? Data Dashboard are trei unelte mici, scrise în JavaScript, care au nevoie de Node.js ca să pornească, la fel cum o oală are nevoie de un aragaz ca să fiarbă ceva:
> - **Corectorul** verifică fiecare cifră și fiecare grafic din raport, așa cum un corector de editură citește o carte înainte de tipar. Dacă ceva nu se potrivește, o coloană care lipsește sau o dată greșită, oprește totul și spune exact unde e problema.
> - **Legătorul** ia toate bucățile (datele, graficele, textele) și le leagă într-un singur fișier, ca pe paginile unei cărți legate între coperți. Acel fișier îl poți trimite pe email sau îl deschizi cu dublu-click.
> - **Cititorul** se uită prima dată prin fișierele tale și îți spune ce e în ele: câte rânduri au, ce coloane, unde lipsesc date.
>
> Node.js e gratuit și e folosit de companii ca Netflix, LinkedIn sau NASA. Ocupă cam 100 MB, adică mai puțin decât o aplicație obișnuită de pe telefon. Nu schimbă nimic din ce ai deja pe calculator: doar adaugă un aragaz nou în bucătărie.

**Dacă vrea mai mult:** se instalează ca orice program. Pe Windows apare în „Setări → Aplicații” și se dezinstalează de acolo. Pe Mac și Linux îl punem cu un mic ajutor numit **nvm**, un „administrator de aragazuri”. nvm pune Node.js doar în folderul tău de utilizator, fără să atingă restul sistemului și fără parola de administrator. Node.js nu rulează nimic singur în fundal: pornește doar când îl cheamă Data Dashboard și se oprește imediat după aceea.

#### Playwright și Chromium: degustătorul

> **Playwright și Chromium formează degustătorul: cel care gustă mâncarea înainte să plece din bucătărie.**
>
> Într-un restaurant bun, nicio farfurie nu ajunge la client până nu se uită cineva la ea și nu o gustă. Așa e și aici. După ce Data Dashboard îți construiește raportul, nu ți-l dă direct. Mai întâi îl deschide pe ascuns și îl verifică pe toate părțile.
>
> **Chromium** este un browser, adică un program ca Chrome sau Edge, cu care deschizi pagini web. Doar că acesta e un browser **invizibil**. Gândește-te la o sală de repetiții goală, în care actorii își joacă piesa înainte de premieră, fără public. Chromium nu apare pe desktop, nu-ți înlocuiește browserul obișnuit, nu se deschide niciodată în fața ta și nu știe nimic despre parolele sau istoricul tău.
>
> **Playwright** este „robotul” care stă în sala aceea goală. E o unealtă gratuită făcută de Microsoft. Deschide raportul tău în browserul invizibil și se poartă exact ca un om: dă click pe fiecare tab, așteaptă să se deseneze graficele, verifică să nu fie niciun grafic gol sau vreo eroare, apoi face câte o poză la fiecare pagină. Doar dacă totul arată bine, raportul ajunge la tine.
>
> Fără degustător, ai putea primi un raport cu un grafic gol sau o pagină care nu se încarcă, și ai afla abia în fața colegilor. Ocupă câteva sute de MB (pe unele calculatoare până la vreo 650 MB), mai ales browserul.

**Dacă vrea mai mult:** Playwright e folosit de mii de companii ca să-și testeze site-urile. Browserul invizibil stă într-un folder separat (`ms-playwright`) și se poate șterge oricând. Playwright pornește doar în cele câteva secunde de verificare, apoi se închide. Nu trimite nimic pe internet despre datele tale: tot ce face rămâne pe calculatorul tău.

#### Python: ajutorul de bucătar

> **Python este ajutorul de bucătar: cel care spală, curăță și taie ingredientele.**
>
> Ingredientele vin rareori curate. Datele unei firme sunt la fel: același lucru e scris în zece feluri. O țară apare ca „USA”, „U.S.” sau „Statele Unite”. O sumă apare ca „1.234,56 €” într-un fișier și „1,234.56” în altul. O dată calendaristică precum „03/05” poate însemna 3 mai sau 5 martie. Dacă bucătarul ar găti cu ingrediente nespălate, mâncarea ar ieși proastă: raportul ar număra greșit, ar dubla vânzări sau ar pierde clienți pe drum.
>
> Python este un limbaj de programare foarte prietenos, cel mai folosit din lume pentru lucrul cu date. Data Dashboard scrie mici „rețete” în Python care iau fișierele tale și le aduc pe toate la aceeași formă: aceleași nume de țări, aceleași formate de dată, aceeași monedă. Abia apoi le dă bucătarului.
>
> Fișierele tale rămân neatinse. Ajutorul lucrează pe o copie, ca un bucătar care nu taie niciodată din singurul exemplar al rețetei bunicii. Ocupă cam 100 MB.

**Dacă vrea mai mult:** pe Mac și pe multe calculatoare cu Linux, Python vine deja instalat, iar atunci doar verificăm. Pe Windows îl aducem din magazinul oficial Microsoft (winget) și apare apoi în „Setări → Aplicații”. Ca și Node.js, nu rulează nimic în fundal: lucrează doar când îl cheamă Data Dashboard.

#### Bibliotecile Python: ustensilele ajutorului

> **Bibliotecile sunt ustensilele din șorțul ajutorului de bucătar.**
>
> Un ajutor de bucătar fără cuțit, fără răzătoare și fără desfăcător de conserve nu poate face mare lucru. La fel, Python singur știe să citească doar fișiere simple. Ca să deschidă un Excel sau un PDF, are nevoie de unelte speciale, numite „biblioteci”. Sunt ca aplicațiile pe care le adaugi pe un telefon nou ca să poată face mai multe lucruri.
>
> Instalăm cinci:
> - **pandas** e un tabel uriaș care nu obosește niciodată. Imaginează-ți un Excel în care poți pune milioane de rânduri, pe care le poate sorta, aduna și compara într-o clipă. E principala unealtă de lucru cu date din lume.
> - **openpyxl** e cheia care deschide fișierele Excel (.xlsx). Fără ea, un Excel e pentru Python ca o cutie încuiată.
> - **xlrd** e cheia pentru Excel-urile vechi (.xls), pe care le mai dau unele programe de facturare sau platforme.
> - **pdfplumber** e o lupă cu pensetă pentru PDF-uri. Un PDF e ca o fotografie a unei pagini: îl vezi, dar nu poți „lua” ușor cifrele din el. pdfplumber scoate cu grijă textul și tabelele din facturi, contracte sau rapoarte, ca să poată fi numărate.
> - **python-docx** e un cititor de documente Word (.docx). Notițele de ședință sau rapoartele scrise în Word devin și ele ingrediente pentru analiză.
>
> Fără ele, Data Dashboard se descurcă doar cu fișiere CSV și JSON. Cu ele, poate „digera” aproape orice ai: Excel-uri, PDF-uri, documente Word. Ocupă împreună cam 150 MB.

**Dacă vrea mai mult:** bibliotecile se instalează doar pentru utilizatorul tău, nu pentru tot calculatorul. Vin din „magazinul” oficial al lui Python (PyPI), de unde le iau zilnic milioane de programatori. Se dezinstalează cu o singură comandă, dată la final.

### Comenzile de instalare

| | macOS | Windows | Linux |
|---|---|---|---|
| Node.js | cu Homebrew: `brew install node`; fără, prin nvm (fără parolă de administrator): `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh \| bash`, apoi `. "$HOME/.nvm/nvm.sh" && nvm install --lts` | `winget install -e --id OpenJS.NodeJS.LTS` | nvm, la fel ca pe macOS (fără parolă de administrator) |
| Playwright + Chromium | `npm install -g playwright && npx playwright install chromium` | la fel | la fel; dacă browserul nu pornește din cauza unor biblioteci de sistem lipsă, omul rulează singur: `! sudo env "PATH=$PATH" npx playwright install-deps chromium` (cu `PATH` păstrat, ca `sudo` să găsească Node-ul pus prin nvm) |
| Python | de obicei e deja instalat; altfel `brew install python` | `winget install -e --id Python.Python.3.12` | omul rulează singur: `! sudo apt install -y python3 python3-pip` |
| Bibliotecile Python | `python3 -m pip install --user pandas openpyxl xlrd pdfplumber python-docx` | `py -m pip install --user pandas openpyxl xlrd pdfplumber python-docx` | ca pe macOS; dacă pip refuză cu „externally-managed-environment”, explici: „Sistemul își păzește propriul Python, ca un proprietar care nu te lasă să muți mobila. Le punem doar în camera ta.” Apoi adaugi `--break-system-packages` (instalează doar pentru utilizatorul tău). |

**Câteva situații pe care le rezolvi tu, fără să-i încarci pe oameni cu detalii:**
- **Comenzile cu `sudo` (parola de administrator).** Claude Code nu poate tasta parola în locul omului. Explici cu o metaforă: „Pentru pasul ăsta, sistemul cere cheia de la intrarea în bloc, adică parola cu care deschizi calculatorul. Eu nu am voie să o tastez, așa că te rog să scrii tu, în căsuța de mesaj, comanda de mai jos, cu semnul `!` în față.” Apoi îi dai comanda exactă. Pe WSL, comanda cu `!` poate ieși fără niciun mesaj, pentru că `sudo` așteaptă parola într-un loc pe care Claude Code nu-l arată. Dacă se întâmplă asta, îl rogi pe om să deschidă separat aplicația Ubuntu și să ruleze comanda acolo, fără `!`, apoi să revină aici.
- **Windows, după winget.** Sesiunea deschisă a lui Claude Code nu „vede” încă programul nou, ca o bucătărie în care aragazul a fost montat, dar n-a fost încă băgat în priză. Încerci întâi calea completă (`"C:\Program Files\nodejs\node.exe" -v`). Dacă nici așa nu merge, spui: „Închide toată fereastra terminalului, nu doar Claude Code. Deschide una nouă, pornește `claude` în același folder și scrie iar /wizard-data-install. Ce e deja instalat sar automat.”
- **nvm, în aceeași sesiune.** Pui în fața comenzilor următoare `. "$HOME/.nvm/nvm.sh" &&`, ca `node` și `npm` să fie găsite.
- **`npm install -g` dă eroarea EACCES (permisiune refuzată)** pe un Node instalat în sistem. Nu folosești sudo. Propui instalarea lui Node prin nvm, care pune totul în folderul utilizatorului.

## Pasul 4. Testul final: gustăm prima mâncare

După ce Node.js și Playwright sunt instalate, gătești un raport de probă cu datele de exemplu ale skill-ului wizard-data-dashboard și îl dai degustătorului. Folosești folderul temporar al sistemului, nu proiectul omului:

```
node <wizard-data-dashboard>/scripts/build.js <wizard-data-dashboard>/examples/dashboard.example.json <temp>/wizard-data-dashboard-test.html
node <wizard-data-dashboard>/scripts/check.js <temp>/wizard-data-dashboard-test.html <temp>/wizard-data-dashboard-test-shots
```

`<wizard-data-dashboard>` este folderul `wizard-data-dashboard` de lângă acest skill: `${CLAUDE_SKILL_DIR}/../wizard-data-dashboard`. Testul are nevoie de internet, pentru că graficele își descarcă „vopselele” (bibliotecile de desen) de pe internet.

Înainte de test spui: „Acum gătim o mâncare de probă, ca să vedem că bucătăria merge. Fac un raport cu date de exemplu, iar degustătorul îl verifică.”

- **Dacă afișează ✓:** deschizi cu Read una dintre pozele din `<temp>/wizard-data-dashboard-test-shots` și i-o arăți omului: „Uite, așa va arăta un raport făcut din datele tale. Bucătăria e gata!”
- **Dacă nu merge:** explici cauza în cuvinte simple și o rezolvi. Browserul invizibil lipsește: `npx playwright install chromium`. Nu e internet: spui asta.

## Pasul 5. Rezumatul

Închei cu o listă scurtă și caldă:
- ✓ ce s-a instalat;
- – ce s-a sărit, și ce înseamnă asta (de exemplu: „fără bibliotecile Python, folosește doar fișiere CSV”);
- pasul următor: „Acum poți scrie `/wizard-data-dashboard` urmat de folderul cu datele tale, de exemplu `/wizard-data-dashboard date/`. Bucătarul te așteaptă!”

Dacă omul întreabă cum dezinstalează:
- **Node.js:** prin dezinstalarea obișnuită a sistemului (Windows: Setări → Aplicații); pe Mac sau Linux cu nvm: `nvm uninstall <versiune>`.
- **Playwright:** `npm uninstall -g playwright`, apoi ștergi folderul browserului: `~/.cache/ms-playwright` pe Linux, `~/Library/Caches/ms-playwright` pe Mac sau `%LOCALAPPDATA%\ms-playwright` pe Windows.
- **Bibliotecile Python:** `pip uninstall pandas openpyxl xlrd pdfplumber python-docx`.
