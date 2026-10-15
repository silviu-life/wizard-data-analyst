---
name: wizard-data-dashboard
argument-hint: "[aprofundată|standard|rapidă] <folder cu date>"
description: Turn a user's business data (sales, marketing, ad campaigns, orders, customers; CSV, JSON, exports) into an interactive analysis dashboard as one HTML file. It has tabs, sortable tables, filters, split-by segments, and charts that react to the filters (lines, bars, waterfall, treemap, heatmaps, cohorts, world map and more). Use when the user asks for a dashboard, a report on their data, analysis of their sales/marketing/ad data, or "show me what's going on in this data"; in Romanian: „fă-mi o analiză pe datele astea", „vreau un dashboard", „raport din vânzări / reclame / clienți", „analizează folderul date/".
---

# Data dashboard

You don't write HTML for this skill. `template/Dashboard.html` is a finished renderer: it draws everything from one `dashboard.json`, including brand, sidebar, tabs, filters, charts, labels and data. Your job is to understand the data, decide what analysis is worth showing, and write that JSON.

## Files

- `template/Dashboard.html`: the renderer. **Never edit it.** If the template can't show something, change the JSON instead.
- `template/dashboard.schema.json`: the JSON structure, with a description on every property.
- `template/validate.js`: the validator. `node template/validate.js dashboard.json template/dashboard.schema.json`
- `reference/GUIDE.md`: field types, filter rules, split-by, all 16 module types, the analysis plan format, checklist. **Read it before writing JSON.**
- `examples/dashboard.example.json`: a complete working example (4 tabs, 7 datasets, every module type). Copy its patterns.
- `scripts/profile.js`: profiles CSV/JSON files: inferred type, nulls, distinct values, ranges. `node scripts/profile.js data/*.csv`
- `scripts/build.js`: validates, then writes one self-contained HTML. `node scripts/build.js dashboard.json out/dashboard.html`
- `scripts/assemble.js`: merges `<work>/datasets/*.json` into a skeleton dashboard. `node scripts/assemble.js skeleton.json work/datasets dashboard.json`
- `workflows/deep-analysis.js`: the multi-agent workflow for the deep level.
- `scripts/check.js`: opens the built HTML in headless Chromium, clicks every tab and fails on errors or empty cards. `node scripts/check.js dashboard.html screenshots/`

## Step 0: arguments and depth

First check that `node -v` works. If it doesn't, stop and suggest `/wizard-data-install` (it installs Node.js, Playwright and Python for beginners), then continue once it's done.

The skill takes a depth and a data folder, or only the data folder: `/wizard-data-dashboard [depth] <data folder>`.

- `/wizard-data-dashboard aprofundată date/`: both are given, so go straight to that depth.
- `/wizard-data-dashboard date/`: only the folder is given, so ask for the depth (below).
- `/wizard-data-dashboard`: nothing is given. Ask for the depth, then ask in plain text where the data is.

Depth words, in any language and case: `aprofundată`/`aprofundat`/`deep` → Aprofundată; `standard`/`medie`/`medium` → Standard; `rapidă`/`rapid`/`quick` → Rapidă. Anything else in the arguments is the data folder or files. If the folder doesn't exist, say so and ask again.

Ask for the depth with `AskUserQuestion`:

- question: "Cât de detaliată să fie analiza?" · header: "Analiză"
- options:
  1. **Aprofundată**: "Mai mulți agenți în paralel, fiecare pe o parte din date, plus o verificare încrucișată a cifrelor. Cea mai completă, durează cel mai mult."
  2. **Standard (Recomandat)**: "Agentul principal face planul, iar 2–4 sub-agenți prelucrează câte un grup de surse. Echilibrul dintre profunzime și timp."
  3. **Rapidă**: "Agentul principal face totul singur. Bună pentru puține fișiere sau o primă privire."

Ask in the user's language; the Romanian text above is the default.

## Output folder

Every analysis gets its own folder, `analize/<slug>/`, under the current working directory. The slug is `<company>-<topic>-<YYYY-MM-DD>`, lowercase ASCII kebab-case (`lumora-saas-2026-10-15`). Add `-2`, `-3`… if the folder exists. Never overwrite an earlier analysis. All levels use this folder as the work directory (`<work>` below). When done it holds:

```
analize/<slug>/
  dashboard.html      the report (self-contained, opens with a double-click)
  dashboard.json      the full config with all data, the exact input of the HTML
  datasets/*.json     every dataset on its own ({label, description, fields, rows})
  skeleton.json       dashboard.json without datasets
  plan.md             the analysis plan
  scripts/            the cleaning scripts, so the analysis can be re-run
  screenshots/        one screenshot per tab from the final check
```

Every level writes `<work>/plan.md` per "The analysis plan" in `reference/GUIDE.md` before cleaning any data. Every level builds datasets as files in `<work>/datasets/` and merges them with `scripts/assemble.js`; never paste rows into `dashboard.json` by hand.

## Depth levels

### Rapidă: main agent only
Follow steps 1–8 below yourself, without subagents. Keep the plan short (sources, datasets, layout). Use 2–3 tabs and 3–5 findings.

### Standard: main agent plans, subagents process
1. Skim the sources yourself: list every file, run `scripts/profile.js` on one file per family, read a sample of the rest. Don't clean anything yet.
2. Write the full `<work>/plan.md` (all 7 sections of "The analysis plan" in `reference/GUIDE.md`), with 2–4 tasks split by business area.
3. Launch one subagent per task with the `Agent` tool, all in one message so they run in parallel. Give each one: the plan path, its task id, its sources and datasets, and the "Rules for task owners" from `reference/GUIDE.md`. Each one writes `<work>/datasets/<name>.json` and returns its findings with numbers, its plan changes and the data issues it handled.
4. Spot-check the headline numbers yourself against the datasets. Then write `<work>/skeleton.json` (everything except `datasets`), run `scripts/assemble.js`, and do steps 6–8.

### Aprofundată: Claude Code workflow
Call the `Workflow` tool with `scriptPath: "<this skill dir>/workflows/deep-analysis.js"` and pass `args` as a JSON object (not a string):
`{ "skill": "<absolute skill dir>", "data": "<data dir or files>", "work": "<absolute path of analize/<slug>>", "language": "<user language>", "today": "YYYY-MM-DD" }`.
The workflow runs four phases:
1. A planner inventories all data and writes the plan, including the dashboard layout and up to 6 tasks.
2. One agent per task cleans its sources, builds its datasets and analyses its area.
3. A skeptical reviewer recomputes every finding and adds cross-area findings.
4. An assembler writes, validates, builds and browser-checks the dashboard.

When it finishes, check that `dashboard.valid` and `dashboard.checked` are true. If either is false, finish steps 6–8 yourself from `<work>/`. Report the headline findings, plus any failed tasks or rejected findings.

## Steps (all depths)

These are the steps every depth goes through; the depth decides who does them. At Standard and Deep, steps 2–4 belong to the task owners.

1. **Collect the data.** Ask where the files are if the user hasn't said. Accept CSV, JSON, XLSX (convert to CSV first) or pasted tables. Note each file's grain, e.g. "one row per order", "one row per campaign per day".
2. **Profile each source.** Run `scripts/profile.js` on it. For every column decide: field name (snake_case), field type, and whether it's a dimension (filter or split candidate) or a measure. Flag dirty values: currency strings, mixed date formats, country names that need ISO numeric codes, `%` strings that must become fractions.
3. **Model datasets.** Clean and reshape with a script you write (Node or Python). Output one dataset per grain with raw rows. Rules:
   - Use one name for one concept across datasets (`channel`, `region`, `date`). Filters join on the name.
   - Don't pre-aggregate anything a chart can compute. Do pre-aggregate when the raw data is huge (>50k rows): roll up to day × dimensions.
   - Dates as `YYYY-MM-DD`, percents as fractions, durations in seconds, countries as ISO 3166-1 numeric strings ("840") with a name column.
   - Only include columns some module, filter or split uses.
4. **Analyse.** Before laying out anything, write down 5–10 findings worth showing. Examples: which channel grew, which campaigns lose money, where customers are, when orders peak, how retention decays. Agents can take one area each (sales, marketing, paid media, customers). Each finding picks the module that shows it best (see "Choosing modules").
5. **Write `<work>/skeleton.json`, then assemble.** Start from `examples/dashboard.example.json`, leaving out `datasets`. Fill in brand (the user's company name), sidebar sources (real file names and row counts), `meta.updated` (now), `time`, `datasets`, `measures`, `filters`, `tabs`. Translate every string in `labels` if the user's language isn't English, and set `locale` and `currency`. Then run `node scripts/assemble.js <work>/skeleton.json <work>/datasets <work>/dashboard.json`.
6. **Validate.** Run `node template/validate.js <work>/dashboard.json template/dashboard.schema.json` (always pass the schema; without it only references and data are checked), fix every line it prints, and repeat until you get ✓. Don't hand-wave errors away; the page refuses to render an invalid file.
7. **Build.** Run `node scripts/build.js <work>/dashboard.json <work>/dashboard.html`.
8. **Test the report.** Run `node scripts/check.js <work>/dashboard.html <work>/screenshots`. It must print ✓. Fix every problem it lists, then rebuild and re-check. Then look at the screenshots yourself and fix anything that renders but reads wrong: unreadable labels, a chart dominated by one outlier, a misleading scale. Only then tell the user the folder path and give 3–5 findings in plain sentences. Don't describe the JSON. If Node.js or Playwright is missing, don't skip the test silently: tell the user to run `/wizard-data-install`, which explains and installs everything step by step.

## Choosing modules

| to show | use |
|---|---|
| Headline numbers with change | `kpi` (compare + sparkline) |
| A measure over time | `line` (measures switch, segments) |
| How parts add up over time | `area` stacked |
| Ranking of a dimension | `bar` ranked |
| This period vs previous by category | `bar` grouped |
| Biggest movers up and down | `bar` diverging |
| Mix within each group | `bar` stacked-100 |
| Share of a total (≤6 parts) | `donut` |
| Detail rows people will sort | `table` (+ status pills) |
| Step-by-step drop-off | `funnel` |
| Actual vs goal | `bullet` |
| Efficiency vs scale, outliers | `scatter` (reference lines + quadrants) |
| What moved a total | `waterfall` |
| Two-dimension intensity (weekday × hour) | `heatmap` |
| Retention or decay by cohort | `cohort` |
| Hierarchical share | `treemap` |
| Daily pattern over a year | `calendar` |
| Where (by country) | `choropleth` |

## Layout rules

- Use 3–5 tabs, named by the question each answers: "Overview", "Sales", "Customers", "Ad campaigns". The first tab is the overview: KPIs, the main trend, a breakdown, a table.
- On a 12-column grid, typical spans are 12 (KPIs, map, table), 8+4, 6+6 and 7+5. Don't leave a row half empty.
- Give each card a title that says what it shows. If something non-obvious affects it, put that in the description: "Not affected by filters", "Last 90 days".
- Add `segments` wherever a breakdown is obvious (channel, region, product). Make one or two filters `primary`; the rest stay advanced.
- Rates (ROAS, CPA, CTR, conversion rate) must be `ratio` measures. Never sum them.
- Use `theme.colors` so each channel keeps one colour everywhere. Keep the template's warm palette.
- Don't invent data. If a source lacks something a module needs (targets, cohorts), skip the module or ask the user for it.

## Limits

- The world map needs internet once (it loads the geometry from jsDelivr). Charts need d3 and topojson from unpkg.
- A single build file over ~15 MB gets slow. Roll up rows before that.
- The template has no export button. If the user asks for a PDF, they can print the page from the browser.
