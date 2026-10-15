#!/usr/bin/env node
/* Profile CSV / JSON files before modelling them.
   node scripts/profile.js <file.csv|file.json> [...more]
   Prints, per column: inferred field type, null count, distinct count, min/max, top values.
   JSON input: an array of objects. No dependencies. */
const fs = require('fs'), path = require('path');

function parseCSV(text) {
  const rows = []; let row = [], cell = '', q = false;
  const delim = (() => { const first = text.split(/\r?\n/, 1)[0]; return [',', ';', '\t'].sort((a, b) => first.split(b).length - first.split(a).length)[0]; })();
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += c; continue; }
    if (c === '"') q = true;
    else if (c === delim) { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; row.push(cell); rows.push(row); row = []; cell = ''; }
    else cell += c;
  }
  if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
  const [head, ...body] = rows.filter(r => r.some(x => x !== ''));
  return body.map(r => Object.fromEntries(head.map((h, i) => [h.trim(), r[i]])));
}
const isDate = v => /^\d{4}-\d{2}-\d{2}$/.test(v);
const isDateTime = v => /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/.test(v);
const isNum = v => v !== '' && !isNaN(Number(String(v).replace(/[$€£,%\s]/g, '')));
const isBool = v => /^(true|false|yes|no|0|1)$/i.test(v);
function infer(name, vals) {
  const s = vals.map(v => String(v).trim()), n = s.length, distinct = new Set(s).size, lname = name.toLowerCase();
  if (!n) return 'text';
  if (s.every(isDate)) return 'date';
  if (s.every(isDateTime)) return 'datetime';
  if (s.every(isBool) && distinct <= 2 && !s.every(isNum)) return 'boolean';
  if (s.every(isNum)) {
    if (/iso|country_code/.test(lname) && s.every(v => /^\d{3}$/.test(v))) return 'geo';
    if (s.some(v => /[$€£]/.test(v)) || /revenue|spend|cost|price|amount|sales|value|budget|cpa|cpc/.test(lname)) return 'currency';
    if (s.some(v => /%/.test(v)) || /rate|ratio|pct|percent|share|ctr|cvr/.test(lname)) return 'percent';
    if (/duration|seconds|time_on|session_length/.test(lname)) return 'duration';
    return 'number';
  }
  if (/(^|_)id$|uuid|sku|utm/.test(lname) || distinct > n * 0.9) return distinct > 50 ? 'id' : 'text';
  if (/country/.test(lname)) return 'category';
  return distinct <= Math.max(30, n * 0.05) ? 'category' : 'text';
}
for (const file of process.argv.slice(2)) {
  const raw = fs.readFileSync(file, 'utf8');
  const rows = path.extname(file).toLowerCase() === '.json' ? JSON.parse(raw) : parseCSV(raw);
  const cols = Object.keys(rows[0] || {});
  console.log(`\n${file}: ${rows.length} rows, ${cols.length} columns`);
  for (const c of cols) {
    const all = rows.map(r => r[c]), present = all.filter(v => v !== '' && v != null), t = infer(c, present);
    const counts = new Map(); present.forEach(v => counts.set(v, (counts.get(v) || 0) + 1));
    const top = [...counts].sort((a, b) => b[1] - a[1]).slice(0, 6).map(([v, k]) => `${v} (${k})`).join(', ');
    let range = '';
    if (['number', 'currency', 'percent', 'duration'].includes(t)) { const nums = present.map(v => Number(String(v).replace(/[$€£,%\s]/g, ''))); range = ` min ${Math.min(...nums)} max ${Math.max(...nums)}`; }
    if (t === 'date' || t === 'datetime') { const d = present.slice().sort(); range = ` ${d[0]} → ${d[d.length - 1]}`; }
    console.log(`  ${c.padEnd(24)} ${t.padEnd(9)} nulls ${all.length - present.length}  distinct ${counts.size}${range}`);
    if (['category', 'boolean', 'text', 'geo'].includes(t)) console.log(`  ${''.padEnd(24)} top: ${top}`);
  }
}
