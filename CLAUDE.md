# wizard-data-analyst

Repo-ul e un marketplace Claude Code (`.claude-plugin/marketplace.json`) cu un singur plugin, `plugins/wizard-data-analyst`, publicat ca `silviu-life/wizard-data-analyst`. Pentru test local: `claude --plugin-dir plugins/wizard-data-analyst`. Orice schimbare publicată cere `version` crescut în `plugins/wizard-data-analyst/.claude-plugin/plugin.json`.

Pluginul conține două skill-uri:
- `wizard-data-dashboard` transformă un folder de date într-un dashboard HTML. Are trei niveluri (Rapidă, Standard, Aprofundată), iar fiecare analiză merge în `analize/<slug>/`. Fluxul complet e în `SKILL.md`; formatul planului și tipurile de module sunt în `reference/GUIDE.md`.
- `wizard-data-install` instalează pas cu pas, cu acordul userului și cu explicații pentru începători, ce îi trebuie primului (Node.js, Playwright + Chromium, Python, pandas/openpyxl/pdfplumber/python-docx).

## Reguli

- `template/Dashboard.html`, `template/validate.js` și `template/dashboard.schema.json` nu se editează. Dacă un raport nu poate arăta ceva, se schimbă JSON-ul.
- `validate.js` primește schema ca al doilea argument. Fără ea, verifică doar referințele și datele.
- După orice schimbare în `wizard-data-dashboard/scripts/` sau `workflows/`, rulează verificarea rapidă din README (build pe exemplu, apoi `check.js`). Trebuie să iasă ✓.
- Workflow-ul (`workflows/deep-analysis.js`) e JavaScript simplu, fără TypeScript, fără `Date.now()` / `Math.random()`. Data vine prin `args.today`. Verificarea sintaxei se face din README sau cu `new Function` după ce scoți `export`.
- `demo/genereaza_date_demo.py` scrie `./date/` în folderul curent. Cheia cu poveștile ascunse e în `demo/ce_e_ascuns_in_date.md`. Dacă schimbi generatorul, actualizează și cheia. README-ul îl descarcă de pe `main` prin raw.githubusercontent.com.
- Textele pentru utilizator sunt în română.
