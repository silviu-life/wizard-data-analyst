# Building a dashboard.json

`template/Dashboard.html` draws everything from one JSON file: brand, sidebar, tabs, filters, charts, labels and the data. You write the JSON. You never edit the HTML.

Files that ship together:

- `Dashboard.html`: the renderer.
- `dashboard.json`: your configuration and data.
- `dashboard.schema.json`: the structure. Every property is described there.
- `validate.js`: checks the JSON. The page runs it too and refuses to render an invalid file.

## Workflow

1. **Inspect the sources.** For each file, list its columns, sample values and row count.
2. **Model datasets.** Keep one dataset per grain, e.g. "one row per campaign per day". Keep rows raw. The page aggregates, filters and compares periods itself, so don't pre-sum anything a chart can compute.
3. **Type every field.** See the field types below. Use the same field name in every dataset where it means the same thing (`channel`, `region`). A filter on that name then applies to all of them.
4. **Define measures.** These are the numbers charts show. Use `ratio` for rates (ROAS, CPA, CTR) so they stay correct under any filter.
5. **Choose filters.** List the fields people should filter by. The page picks the control.
6. **Lay out tabs and modules.** Use a 12-column grid. Lead with KPIs, then a trend, then breakdowns.
7. **Validate.** Run `node validate.js dashboard.json`, fix every line it prints, and run it again until it prints ✓.

## Field types

| type | value in rows | notes |
|---|---|---|
| `date` | `"2026-10-13"` | Use it as the `time` field |
| `datetime` | `"2026-10-13T09:12:00Z"` | |
| `category` | `"Meta"` | Optional `values` sets the allowed values and their order |
| `ordinal` | `"Pro"` | `values` is required, listed low → high |
| `text` | `"Spring sale"` | Free text |
| `id` | `"gads-brand"` | Identifiers |
| `number` | `1240` | |
| `currency` | `412.5` | In the root `currency` |
| `percent` | `0.25` | A fraction: 0.25 = 25% |
| `boolean` | `true` | |
| `geo` | `"840"` | ISO 3166-1 numeric code as a string. Needs `labelField` pointing at the name column |
| `duration` | `134` | Seconds |

Set `"nullable": true` on a field if its rows may contain `null`.

## Filters

There are two levels of filter:

- `time`: the main date filter, always shown in the bar. It has presets, an optional custom from/to picker, and a Compare toggle (`compare: "on" | "off" | "hidden"`).
- `filters` (root) applies on every tab. `tabs[].filters` adds filters for one tab only.

A filter is just `{ "field": "channel" }`. The page picks the control from the field type:

| field type | control |
|---|---|
| category, ≤6 values | chips |
| category, more values | searchable multi-select |
| ordinal | chips (≤6) or dropdown |
| boolean | toggle |
| number / currency / percent / duration | range slider |
| text / id | text search |
| geo | searchable multi-select |
| date (other than the time field) | from/to dates |

To force a different control, set `control`. The validator rejects controls that don't fit the field type.

**Placement.** Filters go in the **Advanced filters** drawer by default. Set `"placement": "primary"` to put a filter in the bar. Only chips, dropdown, toggle and search can be primary. Keep one or two primary filters per tab. Active advanced filters show as removable chips under the bar.

A filter applies to every dataset that has the field, and is skipped for datasets that don't. To make a module ignore a filter, use `ignoreFilters: ["time", "region"]`.

## Split by (segments)

Add `segments: ["channel", "region"]` to a module and its card gets a **Split by** menu. Each type reacts differently:

- `line`: one line per value (top 8).
- `bar` grouped: bars stacked by the split field.
- `area`, `bar` stacked-100: changes the stack field (the default is `stackBy`).
- `scatter`: changes the color field (the default is `color`).
- `donut`, `bar` ranked, `bar` diverging: regroups by the split field (the default is `groupBy`).

Set `split` to choose what is selected on load. Use `{split}` in a title to name the current split, e.g. `"Revenue by {split}"`.

## Click to filter

Clicking a slice, bar, legend item, table row, bubble, tile or country filters the current tab to that value. If the field has a declared filter, that filter is set. Otherwise a tab-only chip marked "From chart" appears. Clicking the same value again clears it.

## Modules

These properties work on every module: `id` (required, unique), `type`, `span` (1–12), `height`, `title`, `description`, `dataset`, `where`, `ignoreFilters`.

| type | required | useful options |
|---|---|---|
| `kpi` | measures | compare, sparkline |
| `line` | measures | compare, bucket, segments |
| `area` | x, stackBy, measure | layout `stacked`, bucket, segments |
| `bar` | layout, groupBy, measure | `ranked` / `grouped` / `diverging` / `stacked-100` (+stackBy), compare, limit, segments |
| `donut` | groupBy, measure | segments |
| `table` | groupBy, columns | sort, limit; columns take field, measure, sub, color, strong, status |
| `funnel` | steps | `rate` text with `{rate}` |
| `bullet` | items | targetDays scales targets to the selected range |
| `scatter` | groupBy, x, y, size | color, reference, quadrants, labelTop, segments |
| `waterfall` | label, value, kind | Rows in order. kind is `total` or `change`; a `total` with null value uses the running sum |
| `heatmap` | rows, columns, measure | |
| `cohort` | cohort, size, period, value | cohortLabel, sizeLabel, periodLabel |
| `treemap` | groupBy [parent, child], measure | color |
| `calendar` | x, measure | colorSteps; usually `ignoreFilters: ["time"]` |
| `choropleth` | key (geo), name, measures | listTop, colorSteps |
| `stack` | modules | Stacks cards in one grid column |

Placeholders in titles and descriptions: `{measure}`, `{split}`, `{n}` (days), `{range}`, `{count}` (table rows).

## Text and colours

- Every UI string lives in `labels`. Translate them all for non-English dashboards, and set `locale` and `currency`.
- Use `theme.colors.<field>.<value>` to keep each channel the same colour everywhere. Values without a fixed colour take the `theme.categorical` palette in the field's value order.

## Validation

```
node <skill>/template/validate.js dashboard.json <skill>/template/dashboard.schema.json
```

It runs two passes:

1. **Structure**: checks against `dashboard.schema.json`, including unknown properties, wrong types and properties a module type requires.
2. **References and data**: checks that every dataset, field, measure and filter a module names exists, and that each measure's fields are in the module's dataset. It also checks that every row has the right number of values of the right type, that same-named fields share a type, and that control/placement choices are allowed.

Each problem prints a JSON path and a fix, e.g. `$.tabs[3].modules[0].groupBy — "chanel" is not a field of dataset "ads"`. The page runs the same checks on load. If any fail, it shows the list and nothing else.

## The analysis plan

Write the plan before cleaning any data, at every depth. It is the contract between whoever plans and whoever processes. At Standard and Deep depth, agents work only from it. Save it as `<work>/plan.md`.

### Sections

**1. Sources.** One line per file or file family: path, format, grain, rows, and what needs cleaning.

```
billing/stripe/*.csv (33 files) · CSV · one row per charge · ~95k · format changes 2025-07 (amounts in cents), overlapping months → dedupe on id
marketing/meta_ads/*.csv · CSV · campaign × day · ~4k · spend in EUR → convert to USD
```

**2. Datasets.** These are the datasets the dashboard will get. Give each one its name, grain, owner (a task id, or `main`), and its fields as `name:type`. Mark each field as a dimension (D) or a measure (M). Shared concepts use one name everywhere (`date`, `region`, `country`, `channel`, `plan`).

```
payments  · one row per successful charge · owner T1
  date:date D, customer_id:id D, plan:category D, region:category D, country:geo D, country_name:category D, channel:category D, revenue_usd:currency M, seats:number M
```

**3. Measures.** List each measure with its formula. Rates are `ratio` (numerator ÷ denominator), never `sum`.

**4. Filters.** For each filter give the field, whether it is primary or advanced, and which datasets it reaches.

**5. Layout.** List the tabs in order. For each card give: id, module type, span, dataset, measures, groupBy/segments, default sort, and the question it answers. Every row must add up to 12.

```
Tab "Ad campaigns"
  kpi-ads    kpi      12  ads       spend, customers, cac, roas                       — are we buying customers efficiently?
  cac-scat   scatter   7  ads       x=spend y=cac by campaign, ref line = blended CAC  — which campaigns are outliers?
  camp-tbl   table     5  ads       sort cac desc, status pill on cac > 2× blended     — which to pause
```

**6. Hypotheses.** List 5–10 things to confirm or reject in the data, each with the dataset that will answer it.

**7. Tasks** (Standard and Deep only). Each task owns a group of sources and the datasets built from them. Tasks must not overlap: one source has one owner. The usual split is by business area: billing/revenue, marketing/acquisition, product/support, finance/sales.

```
T1 Revenue & customers — sources: billing/**, crm/** — datasets: payments, mrr_monthly, cohorts, customers_by_country — hypotheses: H1, H3
```

### Rules for task owners

- Write each dataset to `<work>/datasets/<name>.json` as `{"label", "description", "fields", "rows"}`, using exactly the fields and order from the plan. Rows are arrays in field order. See `examples/dashboard.example.json` → `datasets`.
- Do the cleaning in a script saved under `<work>/scripts/`, never by hand. This keeps the result reproducible.
- If the data contradicts the plan, change the dataset and report the change. Examples: a field doesn't exist, the grain is different. Don't invent values.
- Return findings as sentences with numbers ("Meta Advantage+ CAC $3,360, 5× the blended $650"). Name the dataset that shows each finding.

## Checklist

- [ ] `node validate.js` prints ✓
- [ ] Every tab opens with the most important numbers
- [ ] Rates are `ratio` measures, never summed
- [ ] Fields that mean the same thing share one name across datasets
- [ ] At most two primary filters per tab
- [ ] Charts with an obvious breakdown have `segments`
- [ ] Every UI string is in `labels`
