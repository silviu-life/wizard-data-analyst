#!/usr/bin/env node
/* Dashboard validator. No dependencies.
   CLI:     node validate.js [dashboard.json] [dashboard.schema.json]
   Browser: <script src="validate.js"></script> → window.DashboardValidator.validateDashboard(json, schema)
   Two passes: (1) structure against dashboard.schema.json, (2) references and data:
   every dataset, field, measure and filter a chart names must exist, and every row must match its field types. */
(function (root) {
  'use strict';
  const FIELD_TYPES = ['date', 'datetime', 'category', 'ordinal', 'text', 'id', 'number', 'currency', 'percent', 'boolean', 'geo', 'duration'];
  const NUMERIC = new Set(['number', 'currency', 'percent', 'duration']);
  const CONTROL_TYPES = {
    chips: ['category', 'ordinal', 'boolean'], dropdown: ['category', 'ordinal', 'geo', 'text', 'id'], 'search-multi': ['category', 'ordinal', 'geo', 'text', 'id'],
    range: ['number', 'currency', 'percent', 'duration'], toggle: ['boolean'], search: ['text', 'id', 'category'], 'date-range': ['date', 'datetime']
  };
  const PRIMARY_OK = new Set(['chips', 'dropdown', 'toggle', 'search']);
  const SEGMENTABLE = new Set(['line', 'area', 'bar', 'donut', 'scatter']);
  const MAX_ROW_ERRORS = 5;

  function controlFor(field, filter, nValues) {
    if (filter && filter.control) return filter.control;
    switch (field.type) {
      case 'date': case 'datetime': return 'date-range';
      case 'boolean': return 'toggle';
      case 'text': case 'id': return 'search';
      case 'geo': return 'search-multi';
      case 'ordinal': return nValues <= 6 ? 'chips' : 'dropdown';
      case 'category': return nValues <= 6 ? 'chips' : 'search-multi';
      default: return 'range';
    }
  }

  const typeOf = v => v === null ? 'null' : Array.isArray(v) ? 'array' : typeof v === 'number' ? (Number.isInteger(v) ? 'integer' : 'number') : typeof v;
  const isType = (v, t) => { const a = typeOf(v); return a === t || (t === 'number' && a === 'integer'); };
  const key = (path, k) => /^[A-Za-z_$][\w$]*$/.test(k) ? `${path}.${k}` : `${path}[${JSON.stringify(k)}]`;

  /* ---------- pass 1: JSON Schema subset ---------- */
  function validateSchema(data, schema) {
    const errors = [];
    const res = ref => ref.replace(/^#\//, '').split('/').reduce((o, k) => o && o[k.replace(/~1/g, '/').replace(/~0/g, '~')], schema);
    const cond = s => Object.entries((s && s.properties) || {}).filter(([, p]) => p.const !== undefined).map(([k, p]) => `${k} is ${JSON.stringify(p.const)}`).join(' and ');
    function v(x, s, path, out, ctx) {
      if (!s || s === true) return;
      if (s.$ref) { v(x, res(s.$ref), path, out, ctx); if (Object.keys(s).length === 1) return; }
      if (s.type) { const ts = [].concat(s.type); if (!ts.some(t => isType(x, t))) { out.push({path, message: `should be ${ts.join(' or ')}, got ${typeOf(x)}`}); return; } }
      if (s.const !== undefined && x !== s.const) out.push({path, message: `should be ${JSON.stringify(s.const)}, got ${JSON.stringify(x)}`});
      if (s.enum && !s.enum.includes(x)) out.push({path, message: `should be one of ${s.enum.map(e => JSON.stringify(e)).join(', ')}; got ${JSON.stringify(x)}`});
      if (typeof x === 'string') {
        if (s.minLength != null && x.length < s.minLength) out.push({path, message: `should not be empty`});
        if (s.maxLength != null && x.length > s.maxLength) out.push({path, message: `should be at most ${s.maxLength} characters`});
        if (s.pattern && !new RegExp(s.pattern).test(x)) out.push({path, message: `"${x}" doesn't match ${s.pattern}`});
      }
      if (typeof x === 'number') {
        if (s.minimum != null && x < s.minimum) out.push({path, message: `should be ≥ ${s.minimum}`});
        if (s.maximum != null && x > s.maximum) out.push({path, message: `should be ≤ ${s.maximum}`});
        if (s.exclusiveMinimum != null && x <= s.exclusiveMinimum) out.push({path, message: `should be > ${s.exclusiveMinimum}`});
      }
      if (Array.isArray(x)) {
        if (s.minItems != null && x.length < s.minItems) out.push({path, message: `should have at least ${s.minItems} item(s)`});
        if (s.maxItems != null && x.length > s.maxItems) out.push({path, message: `should have at most ${s.maxItems} item(s)`});
        if (s.items && path !== '$.datasets.*.rows') x.forEach((it, i) => v(it, s.items, `${path}[${i}]`, out));
      }
      if (typeOf(x) === 'object') {
        (s.required || []).forEach(k => { if (!(k in x)) out.push({path, message: `missing required property "${k}"${ctx ? ` (required when ${ctx})` : ''}`}); });
        if (s.minProperties != null && Object.keys(x).length < s.minProperties) out.push({path, message: `should have at least ${s.minProperties} entr${s.minProperties > 1 ? 'ies' : 'y'}`});
        const props = s.properties || {};
        for (const k of Object.keys(x)) {
          if (props[k]) v(x[k], props[k], key(path, k), out);
          else if (s.additionalProperties === false) { if (s.properties) out.push({path: key(path, k), message: `unknown property "${k}"`}); }
          else if (s.additionalProperties && typeof s.additionalProperties === 'object') v(x[k], s.additionalProperties, key(path, k), out);
        }
      }
      if (s.allOf) s.allOf.forEach(sub => v(x, sub, path, out, ctx));
      if (s.if) { const t = []; v(x, s.if, path, t); if (!t.length) { if (s.then) v(x, s.then, path, out, cond(s.if)); } else if (s.else) v(x, s.else, path, out, ctx); }
      for (const kw of ['anyOf', 'oneOf']) {
        if (!s[kw]) continue;
        const tries = s[kw].map(sub => { const t = []; v(x, sub, path, t); return t; }), ok = tries.filter(t => !t.length).length;
        if (!ok) out.push(...(s.errorMessage ? [{path, message: s.errorMessage}] : tries.reduce((a, b) => b.length < a.length ? b : a)));
        else if (kw === 'oneOf' && ok > 1) out.push({path, message: 'matches more than one allowed shape'});
      }
    }
    // rows are checked in pass 2 with typed messages; skip per-row schema noise
    const rowsSchema = schema.$defs && schema.$defs.dataset && schema.$defs.dataset.properties.rows;
    const saved = rowsSchema && rowsSchema.items; if (rowsSchema) delete rowsSchema.items;
    try { v(data, schema, '$', errors); } finally { if (rowsSchema) rowsSchema.items = saved; }
    return errors;
  }

  /* ---------- pass 2: references + data ---------- */
  function checkValue(f, x) {
    if (x === null || x === undefined) return f.nullable ? null : 'is empty; set "nullable": true on the field to allow it';
    switch (f.type) {
      case 'date': return typeof x === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(x) && !isNaN(Date.parse(x)) ? null : `should be a date "YYYY-MM-DD", got ${JSON.stringify(x)}`;
      case 'datetime': return typeof x === 'string' && !isNaN(Date.parse(x)) ? null : `should be an ISO 8601 datetime, got ${JSON.stringify(x)}`;
      case 'category': case 'ordinal':
        if (typeof x !== 'string') return `should be text, got ${typeOf(x)}`;
        return f.values && !f.values.includes(x) ? `"${x}" is not one of the field's values (${f.values.join(', ')})` : null;
      case 'text': case 'id': return typeof x === 'string' || typeof x === 'number' ? null : `should be text, got ${typeOf(x)}`;
      case 'geo': return typeof x === 'string' && /^\d{3}$/.test(x) ? null : `should be a 3-digit ISO 3166-1 numeric code as text, e.g. "840", got ${JSON.stringify(x)}`;
      case 'boolean': return typeof x === 'boolean' ? null : `should be true or false, got ${JSON.stringify(x)}`;
      case 'duration': return typeof x === 'number' && isFinite(x) && x >= 0 ? null : `should be seconds (number ≥ 0), got ${JSON.stringify(x)}`;
      default: return typeof x === 'number' && isFinite(x) ? null : `should be a number, got ${JSON.stringify(x)}`;
    }
  }

  function validateRefs(D) {
    const E = [], err = (path, message) => E.push({path, message});
    const datasets = D.datasets || {}, measures = D.measures || {}, FI = {};
    const fieldsOf = id => { const d = datasets[id]; return d && Array.isArray(d.fields) ? new Map(d.fields.map(f => [f.name, f])) : new Map(); };

    for (const [id, d] of Object.entries(datasets)) {
      if (!d || !Array.isArray(d.fields)) continue;
      const p = key('$.datasets', id), seen = new Set();
      d.fields.forEach((f, i) => {
        if (!f || !f.name) return;
        if (seen.has(f.name)) err(`${p}.fields[${i}]`, `duplicate field "${f.name}"`); seen.add(f.name);
        if (f.labelField && !d.fields.some(g => g.name === f.labelField)) err(`${p}.fields[${i}].labelField`, `"${f.labelField}" is not a field in this dataset`);
        if (f.values && !['category', 'ordinal'].includes(f.type)) err(`${p}.fields[${i}].values`, `only category and ordinal fields take values`);
        (FI[f.name] = FI[f.name] || []).push({ds: id, f});
      });
      if (!Array.isArray(d.rows)) continue;
      if (!d.rows.length) err(`${p}.rows`, 'has no rows');
      let bad = 0;
      d.rows.forEach((r, ri) => {
        if (bad > MAX_ROW_ERRORS) return;
        const rp = `${p}.rows[${ri}]`;
        if (!Array.isArray(r)) { bad++; return err(rp, `should be an array of ${d.fields.length} values`); }
        if (r.length !== d.fields.length) { bad++; return err(rp, `has ${r.length} values; fields are [${d.fields.map(f => f.name).join(', ')}]`); }
        d.fields.forEach((f, fi) => { const m = checkValue(f, r[fi]); if (m && bad <= MAX_ROW_ERRORS) { bad++; err(`${rp}[${fi}]`, `${f.name} ${m}`); } });
      });
      if (bad > MAX_ROW_ERRORS) err(`${p}.rows`, `stopped after ${MAX_ROW_ERRORS} row errors`);
    }
    // same field name must mean the same type everywhere
    for (const [name, list] of Object.entries(FI)) {
      const types = [...new Set(list.map(x => x.f.type))];
      if (types.length > 1) err('$.datasets', `field "${name}" has different types across datasets (${list.map(x => `${x.ds}: ${x.f.type}`).join(', ')}); filters treat same-named fields as one`);
    }

    const measureFields = (mid, seen = new Set()) => {
      const m = measures[mid]; if (!m || seen.has(mid)) return [];
      seen.add(mid);
      return m.ratio ? m.ratio.flatMap(r => measureFields(r, seen)) : m.field ? [m.field] : [];
    };
    for (const [mid, m] of Object.entries(measures)) {
      const p = key('$.measures', mid);
      if (m.field) {
        if (!FI[m.field]) err(`${p}.field`, `no dataset has a field "${m.field}"`);
        else if (m.agg !== 'distinct' && m.agg !== 'count' && !FI[m.field].some(x => NUMERIC.has(x.f.type))) err(`${p}.field`, `"${m.field}" is ${FI[m.field][0].f.type}; ${m.agg || 'sum'} needs a number, currency, percent or duration field`);
      }
      (m.ratio || []).forEach((r, i) => { if (!measures[r]) err(`${p}.ratio[${i}]`, `unknown measure "${r}"`); else if (r === mid) err(`${p}.ratio[${i}]`, 'a ratio cannot reference itself'); });
    }

    const T = D.time;
    if (T && T.field) {
      if (!FI[T.field]) err('$.time.field', `no dataset has a field "${T.field}"`);
      else if (!FI[T.field].every(x => x.f.type === 'date' || x.f.type === 'datetime')) err('$.time.field', `"${T.field}" must be a date or datetime field in every dataset`);
      if (T.presets && T.default != null && !T.presets.some(pr => pr.days === T.default)) err('$.time.default', `${T.default} is not one of the presets' days (${T.presets.map(pr => pr.days).join(', ')})`);
    }

    const checkFilters = (list, p, taken) => (list || []).forEach((f, i) => {
      const fp = `${p}[${i}]`;
      if (!f || !f.field) return;
      if (!FI[f.field]) return err(`${fp}.field`, `no dataset has a field "${f.field}"`);
      if (T && f.field === T.field) err(`${fp}.field`, `"${f.field}" is the time field; it is already filtered by "time"`);
      if (taken.has(f.field)) err(`${fp}.field`, `"${f.field}" is already a filter${taken.get(f.field)}`);
      taken.set(f.field, ` at ${fp}`);
      const def = FI[f.field][0].f, ctl = controlFor(def, f, (def.values || []).length || 99);
      if (f.control && !CONTROL_TYPES[f.control].includes(def.type)) err(`${fp}.control`, `"${f.control}" can't filter a ${def.type} field; use ${Object.keys(CONTROL_TYPES).filter(c => CONTROL_TYPES[c].includes(def.type)).join(' or ')}`);
      if (f.placement === 'primary' && !PRIMARY_OK.has(ctl)) err(`${fp}.placement`, `a ${ctl} control can't be primary; only ${[...PRIMARY_OK].join(', ')} fit the filter bar`);
    });
    const globals = new Map(); checkFilters(D.filters, '$.filters', globals);
    const allFilterFields = new Set((D.filters || []).map(f => f.field));

    const colors = (D.theme && D.theme.colors) || {};
    for (const k of Object.keys(colors)) if (!FI[k]) err(key('$.theme.colors', k), `no dataset has a field "${k}"`);

    const ids = new Map(), tabIds = new Set();
    const REFS = {
      kpi: {m: ['measures']}, line: {m: ['measures']}, area: {f: ['x', 'stackBy', 'color'], m: ['measure']}, bar: {f: ['groupBy', 'stackBy', 'color'], m: ['measure']},
      donut: {f: ['groupBy', 'color'], m: ['measure']}, table: {f: ['groupBy']}, funnel: {}, bullet: {}, scatter: {f: ['groupBy', 'color'], m: ['x', 'y', 'size']},
      waterfall: {f: ['label', 'value', 'kind']}, heatmap: {f: ['rows', 'columns'], m: ['measure']}, cohort: {f: ['cohort', 'size', 'period', 'value']},
      treemap: {f: ['groupBy', 'color'], m: ['measure']}, calendar: {f: ['x'], m: ['measure']}, choropleth: {f: ['key', 'name'], m: ['measures']}
    };
    const LAYOUTS = {bar: ['ranked', 'grouped', 'diverging', 'stacked-100'], area: ['stacked']};
    function checkModule(m, p, tabFilters) {
      if (!m || !m.type) return;
      if (m.type === 'stack') return (m.modules || []).forEach((c, i) => { if (c && c.type === 'stack') err(`${p}.modules[${i}]`, 'stacks cannot be nested'); else checkModule(c, `${p}.modules[${i}]`, tabFilters); });
      if (m.id) { if (ids.has(m.id)) err(`${p}.id`, `duplicate module id "${m.id}" (also at ${ids.get(m.id)})`); else ids.set(m.id, p); }
      if (m.layout && LAYOUTS[m.type] && !LAYOUTS[m.type].includes(m.layout)) err(`${p}.layout`, `${m.type} supports ${LAYOUTS[m.type].join(', ')}`);
      if (m.layout && !LAYOUTS[m.type]) err(`${p}.layout`, `${m.type} has no layouts`);
      if (!m.dataset) return;
      if (!datasets[m.dataset]) return err(`${p}.dataset`, `unknown dataset "${m.dataset}"; datasets are ${Object.keys(datasets).join(', ')}`);
      const F = fieldsOf(m.dataset), ds = m.dataset;
      const needField = (v, pp, types) => {
        if (v == null) return;
        if (!F.has(v)) return err(pp, `"${v}" is not a field of dataset "${ds}" (fields: ${[...F.keys()].join(', ')})`);
        if (types && !types.includes(F.get(v).type)) err(pp, `"${v}" is ${F.get(v).type}; expected ${types.join(' or ')}`);
      };
      const needMeasure = (mid, pp) => {
        if (mid == null) return;
        if (!measures[mid]) return err(pp, `unknown measure "${mid}"; measures are ${Object.keys(measures).join(', ')}`);
        const miss = measureFields(mid).filter(f => !F.has(f));
        if (miss.length) err(pp, `measure "${mid}" needs field(s) ${miss.join(', ')}, which dataset "${ds}" doesn't have`);
      };
      const r = REFS[m.type] || {};
      (r.f || []).forEach(k => { const v = m[k]; if (k === 'columns' && Array.isArray(v)) return; [].concat(v ?? []).forEach((x, i) => needField(x, Array.isArray(v) ? `${p}.${k}[${i}]` : `${p}.${k}`)); });
      (r.m || []).forEach(k => [].concat(m[k] ?? []).forEach((x, i) => needMeasure(x, Array.isArray(m[k]) ? `${p}.${k}[${i}]` : `${p}.${k}`)));
      if (m.type === 'heatmap') needField(m.columns, `${p}.columns`);
      if (m.type === 'table' && Array.isArray(m.columns)) m.columns.forEach((c, i) => { const cp = `${p}.columns[${i}]`; needField(c.field, `${cp}.field`); needMeasure(c.measure, `${cp}.measure`); (c.sub || []).forEach((s, j) => needField(s, `${cp}.sub[${j}]`)); if (c.status) needMeasure(c.status.measure, `${cp}.status.measure`); if (!c.field && !c.measure && !c.status) err(cp, 'needs "field", "measure" or "status"'); });
      if (m.type === 'table' && m.sort && m.sort.by && Array.isArray(m.columns) && !m.columns.some(c => (c.measure || c.field || (c.status && c.status.measure)) === m.sort.by)) err(`${p}.sort.by`, `"${m.sort.by}" is not one of the table's columns`);
      if (m.type === 'funnel') (m.steps || []).forEach((s, i) => needMeasure(s.measure, `${p}.steps[${i}].measure`));
      if (m.type === 'bullet') (m.items || []).forEach((s, i) => needMeasure(s.measure, `${p}.items[${i}].measure`));
      if (m.type === 'treemap' && !Array.isArray(m.groupBy)) err(`${p}.groupBy`, 'treemap needs [parent, child], e.g. ["product", "item"]');
      if (m.type !== 'treemap' && Array.isArray(m.groupBy)) err(`${p}.groupBy`, 'only treemap takes two groupBy fields');
      if (m.type === 'choropleth') needField(m.key, `${p}.key`, ['geo']);
      if (m.type === 'calendar' || m.type === 'area') needField(m.x, `${p}.x`, ['date', 'datetime']);
      if (['line', 'area', 'kpi'].includes(m.type) && !T) err(p, `${m.type} needs a "time" block at the root`);
      if (['line', 'area'].includes(m.type) && T && !F.has(T.field)) err(`${p}.dataset`, `${m.type} needs dataset "${ds}" to have the time field "${T.field}"`);
      if (m.segments) {
        if (!SEGMENTABLE.has(m.type)) err(`${p}.segments`, `${m.type} can't be split; segments work on ${[...SEGMENTABLE].join(', ')}`);
        m.segments.forEach((s, i) => needField(s, `${p}.segments[${i}]`));
        if (m.split != null && !m.segments.includes(m.split) && m.split !== m.groupBy && m.split !== m.stackBy) err(`${p}.split`, `"${m.split}" is not in segments`);
      }
      Object.keys(m.where || {}).forEach(k => needField(k, key(`${p}.where`, k)));
      (m.ignoreFilters || []).forEach((k, i) => { if (k !== 'time' && !allFilterFields.has(k) && !tabFilters.has(k)) err(`${p}.ignoreFilters[${i}]`, `"${k}" is not a filter field (or "time")`); });
    }
    (D.tabs || []).forEach((t, ti) => {
      const p = `$.tabs[${ti}]`;
      if (!t) return;
      if (tabIds.has(t.id)) err(`${p}.id`, `duplicate tab id "${t.id}"`); tabIds.add(t.id);
      const taken = new Map(globals); checkFilters(t.filters, `${p}.filters`, taken);
      const tf = new Set((t.filters || []).map(f => f.field));
      (t.modules || []).forEach((m, i) => checkModule(m, `${p}.modules[${i}]`, tf));
    });
    return E;
  }

  function validateDashboard(D, schema) {
    if (typeOf(D) !== 'object') return [{path: '$', message: 'dashboard must be a JSON object'}];
    const errors = schema ? validateSchema(D, schema) : [];
    try { errors.push(...validateRefs(D)); } catch (e) { errors.push({path: '$', message: `could not check references: ${e.message}`}); }
    const seen = new Set();
    return errors.filter(e => { const k = e.path + e.message; if (seen.has(k)) return false; seen.add(k); return true; });
  }

  const api = {validateDashboard, validateSchema, validateRefs, controlFor, FIELD_TYPES, CONTROL_TYPES, SEGMENTABLE: [...SEGMENTABLE]};
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.DashboardValidator = api;

  if (typeof require !== 'undefined' && typeof module !== 'undefined' && require.main === module) {
    const fs = require('fs'), path = require('path');
    const file = process.argv[2] || 'dashboard.json';
    let D, schema = null;
    try { D = JSON.parse(fs.readFileSync(file, 'utf8')); } catch (e) { console.error(`✗ ${file}: ${e.message}`); process.exit(1); }
    const schemaFile = process.argv[3] || path.join(path.dirname(file), D.$schema || 'dashboard.schema.json');
    try { schema = JSON.parse(fs.readFileSync(schemaFile, 'utf8')); } catch (e) { console.warn(`! No schema at ${schemaFile}; checking references and data only.`); }
    const errs = validateDashboard(D, schema);
    if (!errs.length) {
      const count = ms => (ms || []).reduce((a, m) => a + (m.type === 'stack' ? count(m.modules) : 1), 0);
      console.log(`✓ ${file} is valid · ${Object.keys(D.datasets).length} datasets, ${D.tabs.length} tabs, ${D.tabs.reduce((a, t) => a + count(t.modules), 0)} modules`);
      process.exit(0);
    }
    console.error(`✗ ${errs.length} problem${errs.length > 1 ? 's' : ''} in ${file}\n`);
    errs.forEach(e => console.error(`  ${e.path}\n    ${e.message}\n`));
    process.exit(1);
  }
})(typeof window !== 'undefined' ? window : globalThis);
