#!/usr/bin/env node
/* Merge dataset files into a dashboard skeleton.
   node scripts/assemble.js <skeleton.json> <datasets-dir> <out dashboard.json>
   Each <datasets-dir>/<name>.json is one dataset ({label, description, fields, rows}) and becomes datasets.<name>.
   Datasets already in the skeleton are kept unless a file with the same name replaces them. */
const fs = require('fs'), path = require('path');
const [skel, dir, out] = process.argv.slice(2);
if (!out) { console.error('usage: node assemble.js <skeleton.json> <datasets-dir> <out.json>'); process.exit(2); }
const d = JSON.parse(fs.readFileSync(skel, 'utf8'));
d.datasets = d.datasets || {};
for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort()) {
  const ds = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
  d.datasets[path.basename(f, '.json')] = ds;
  console.log(`  ${path.basename(f, '.json').padEnd(28)} ${ds.rows.length} rows`);
}
fs.writeFileSync(out, JSON.stringify(d));
console.log(`✓ wrote ${out} · ${Object.keys(d.datasets).length} datasets`);
