export const meta = {
  name: 'wizard-data-dashboard-deep',
  description: 'Deep data analysis: plan, process each data area in parallel, cross-check findings, assemble and build the dashboard',
  whenToUse: 'Run by the wizard-data-dashboard skill when the user picks the "Aprofundată" depth',
  phases: [
    { title: 'Plan', detail: 'inventory all sources, write plan.md: datasets, measures, filters, layout, tasks' },
    { title: 'Process', detail: 'one agent per task: clean, model datasets, find patterns' },
    { title: 'Cross-check', detail: 'verify key numbers against raw data, join areas' },
    { title: 'Assemble', detail: 'dashboard.json → validate → build HTML → browser check' },
  ],
}

// args: { skill, data, work, language, today }
//   skill: absolute path of the skill directory · data: directory or files to analyse · work: the analysis folder analize/<slug>
//   (plan, scripts, datasets, dashboard.json, dashboard.html, screenshots) · language: user's language (labels) · today: YYYY-MM-DD (scripts cannot read the clock)
const A = args || {}
const MAX_TASKS = 6
const S = A.skill, W = A.work
const CONTEXT = `
Skill directory: ${S}. Read ${S}/SKILL.md and ${S}/reference/GUIDE.md for how dashboards work, the section "The analysis plan" in GUIDE.md for the plan format,
${S}/examples/dashboard.example.json for a complete working dashboard.json, ${S}/template/dashboard.schema.json for every property.
Data to analyse: ${A.data}. Work directory: ${W} (plan at ${W}/plan.md, datasets in ${W}/datasets/, your scripts in ${W}/scripts/).
User language: ${A.language || 'English'}. Today: ${A.today}. Never invent data; if something is missing, say so.`

const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    brand: { type: 'string', description: 'company name as it appears in the data' },
    summary: { type: 'string', description: 'what the data is, in 2-3 sentences' },
    tasks: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' }, title: { type: 'string' },
          sources: { type: 'array', items: { type: 'string' } },
          datasets: { type: 'array', items: { type: 'string' } },
          brief: { type: 'string', description: 'what this owner must produce and which hypotheses to test' },
        },
        required: ['id', 'title', 'sources', 'datasets', 'brief'],
      },
    },
  },
  required: ['brand', 'summary', 'tasks'],
}
const FINDINGS = {
  type: 'array',
  items: { type: 'object', properties: { text: { type: 'string' }, dataset: { type: 'string' } }, required: ['text', 'dataset'] },
}
const PROCESS_SCHEMA = {
  type: 'object',
  properties: {
    datasets: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, rows: { type: 'number' } }, required: ['name', 'rows'] } },
    findings: FINDINGS,
    plan_changes: { type: 'array', items: { type: 'string' } },
    issues: { type: 'array', items: { type: 'string' }, description: 'data problems found and how they were handled' },
  },
  required: ['datasets', 'findings', 'plan_changes', 'issues'],
}
const CROSS_SCHEMA = {
  type: 'object',
  properties: {
    verified: {
      type: 'array',
      items: {
        type: 'object',
        properties: { text: { type: 'string' }, status: { type: 'string', enum: ['confirmed', 'corrected', 'rejected'] }, note: { type: 'string' } },
        required: ['text', 'status'],
      },
    },
    cross_findings: FINDINGS,
  },
  required: ['verified', 'cross_findings'],
}
const ASSEMBLE_SCHEMA = {
  type: 'object',
  properties: {
    html: { type: 'string' }, dashboard_json: { type: 'string' }, valid: { type: 'boolean' },
    checked: { type: 'boolean', description: 'scripts/check.js printed ✓ on the final HTML' },
    tabs: { type: 'array', items: { type: 'string' } },
    headline_findings: { type: 'array', items: { type: 'string' }, description: '3-5 most important findings, plain sentences in the user language' },
  },
  required: ['html', 'dashboard_json', 'valid', 'checked', 'tabs', 'headline_findings'],
}

phase('Plan')
const plan = await agent(`You plan a deep business-data analysis that other agents will execute.${CONTEXT}

1. Inventory every source under the data path: list files, group file families, run \`node ${S}/scripts/profile.js\` on representative files
   (convert XLSX to CSV first; extract text from PDFs, DOCX, EML, MD to judge what they hold). Note grain, row counts, dirty values.
2. Write ${W}/plan.md following "The analysis plan" in ${S}/reference/GUIDE.md exactly: sources, datasets (fields name:type, owner), measures, filters, layout
   (3-5 tabs, 12-column rows, every module type that the data honestly supports), hypotheses, tasks.
3. Split the work into at most ${MAX_TASKS} tasks by business area. Every source has exactly one owner. Prefer fewer, larger tasks over many small ones.
Return the task list.`, { label: 'planner', schema: PLAN_SCHEMA })

if (!plan) return { error: 'planner failed' }
let tasks = plan.tasks
if (tasks.length > MAX_TASKS) {
  log(`planner returned ${tasks.length} tasks; merging the extra ones into task ${tasks[MAX_TASKS - 1].id}`)
  const extra = tasks.slice(MAX_TASKS)
  const last = tasks[MAX_TASKS - 1]
  tasks = [...tasks.slice(0, MAX_TASKS - 1), {
    ...last,
    sources: [...last.sources, ...extra.flatMap(t => t.sources)],
    datasets: [...last.datasets, ...extra.flatMap(t => t.datasets)],
    brief: [last.brief, ...extra.map(t => `${t.id} ${t.title}: ${t.brief}`)].join('\n'),
  }]
}
log(`${plan.brand}: ${tasks.length} tasks · ${tasks.map(t => t.title).join(' · ')}`)

const processed = await parallel(tasks.map(t => () => agent(`You own task ${t.id} "${t.title}" of a planned analysis.${CONTEXT}

Read ${W}/plan.md first; it is your contract. Your sources: ${t.sources.join(', ')}. Your datasets: ${t.datasets.join(', ')}.
Brief: ${t.brief}

1. Write a cleaning script in ${W}/scripts/${t.id}.(py|js) that reads the raw sources and writes each dataset to ${W}/datasets/<name>.json
   as {"label","description","fields","rows"} with the plan's field names, types and order (rows are arrays in field order).
   Clean thoroughly: dedupe, unify formats and currencies, map countries to ISO 3166-1 numeric strings plus a name column, percents as fractions, dates YYYY-MM-DD.
   Roll up to day × dimensions if a dataset would exceed ~50k rows.
2. Run it, then check the output against the raw data with a second, independent calculation of the main totals.
3. Analyse your area: test the hypotheses in your brief and look for anything else that moved. Each finding is one sentence with numbers.
Report plan changes (renamed/added/dropped fields or datasets) and data problems you handled.`,
  { label: `process:${t.id}`, phase: 'Process', schema: PROCESS_SCHEMA })))

const done = processed.map((r, i) => r && { task: tasks[i], ...r }).filter(Boolean)
const failed = tasks.filter((_, i) => !processed[i])
if (failed.length) log(`failed tasks: ${failed.map(t => t.id).join(', ')}; the dashboard will skip their datasets`)
const allFindings = done.flatMap(r => r.findings.map(f => `[${r.task.id}] ${f.text} (dataset: ${f.dataset})`))
const changes = done.flatMap(r => r.plan_changes.map(c => `[${r.task.id}] ${c}`))

phase('Cross-check')
const cross = await agent(`You are the skeptical reviewer of a multi-agent analysis.${CONTEXT}

Datasets are in ${W}/datasets/. Findings from the task agents:
${allFindings.join('\n')}

1. For every finding, recompute its numbers yourself from the datasets, and for the most important ones from the raw sources too.
   Mark each confirmed, corrected (give the right numbers) or rejected (say why). Default to rejected if you cannot reproduce it.
2. Look across areas, which no single task agent could do: acquisition cost vs revenue actually collected, support load vs churn,
   targets/budgets vs actuals, platform-reported vs real conversions. If a cross-area view needs its own dataset, write it to ${W}/datasets/
   and append it to ${W}/plan.md. Return the cross-area findings.`, { label: 'cross-check', schema: CROSS_SCHEMA })

const verified = cross ? cross.verified.filter(v => v.status !== 'rejected').map(v => v.status === 'corrected' ? `${v.text} → corrected: ${v.note}` : v.text) : allFindings
const crossFindings = cross ? cross.cross_findings.map(f => `${f.text} (dataset: ${f.dataset})`) : []
if (cross) log(`findings: ${cross.verified.filter(v => v.status === 'confirmed').length} confirmed, ${cross.verified.filter(v => v.status === 'corrected').length} corrected, ${cross.verified.filter(v => v.status === 'rejected').length} rejected, ${crossFindings.length} cross-area`)

phase('Assemble')
const built = await agent(`You assemble the final dashboard.${CONTEXT}

Plan: ${W}/plan.md. Datasets: ${W}/datasets/*.json. Plan changes made by task agents:
${changes.join('\n') || '(none)'}
Verified findings:
${[...verified, ...crossFindings].join('\n')}

1. Write ${W}/skeleton.json: a full dashboard.json without the datasets (copy the patterns of ${S}/examples/dashboard.example.json).
   Brand "${plan.brand}"; sidebar sources = the real source files with row counts; meta.updated = ${A.today}; translate every labels string to ${A.language || 'English'}
   and set locale/currency. Follow the plan's layout, but let the verified findings decide what leads each tab, and give cards descriptions that state the finding.
2. node ${S}/scripts/assemble.js ${W}/skeleton.json ${W}/datasets ${W}/dashboard.json
3. node ${S}/template/validate.js ${W}/dashboard.json ${S}/template/dashboard.schema.json. Fix the skeleton (or a dataset) for every line it prints, re-assemble, repeat until ✓.
4. node ${S}/scripts/build.js ${W}/dashboard.json ${W}/dashboard.html
5. node ${S}/scripts/check.js ${W}/dashboard.html ${W}/screenshots. It must print ✓; fix, rebuild and re-check until it does.
   Then look at every screenshot and fix what renders but reads wrong (unreadable labels, one outlier flattening a chart, misleading scales).
Return the paths, whether it validated and passed the check, the tab names and the 3-5 headline findings in ${A.language || 'English'}.`, { label: 'assemble', schema: ASSEMBLE_SCHEMA })

return {
  brand: plan.brand,
  plan: `${W}/plan.md`,
  failed_tasks: failed.map(t => t.id),
  dashboard: built,
  findings: verified,
  cross_findings: crossFindings,
  rejected: cross ? cross.verified.filter(v => v.status === 'rejected').map(v => `${v.text} — ${v.note || ''}`) : [],
}
