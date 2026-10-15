#!/usr/bin/env node
/* Build a single self-contained dashboard HTML.
   node scripts/build.js <dashboard.json> [out.html]
   Validates first; on any problem prints them and exits 1 without writing.
   Output inlines the JSON, schema and validator, so it opens with a double-click (no server). */
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', 'template');
const input = process.argv[2], out = process.argv[3] || 'dashboard.html';
if (!input) { console.error('usage: node build.js <dashboard.json> [out.html]'); process.exit(2); }
const V = require(path.join(ROOT, 'validate.js'));
let data;
try { data = JSON.parse(fs.readFileSync(input, 'utf8')); } catch (e) { console.error(`✗ ${input}: ${e.message}`); process.exit(1); }
const schema = JSON.parse(fs.readFileSync(path.join(ROOT, 'dashboard.schema.json'), 'utf8'));
const errs = V.validateDashboard(data, schema);
if (errs.length) {
  console.error(`✗ ${errs.length} problem${errs.length > 1 ? 's' : ''} in ${input}; nothing written\n`);
  errs.forEach(e => console.error(`  ${e.path}\n    ${e.message}\n`));
  process.exit(1);
}
const safe = s => s.replace(/<\/(script)/gi, '<\\/$1').replace(/<!--/g, '<\\!--');
let html = fs.readFileSync(path.join(ROOT, 'Dashboard.html'), 'utf8');
const validator = fs.readFileSync(path.join(ROOT, 'validate.js'), 'utf8').replace(/^#!.*\n/, '');
const tag = '<script src="validate.js"></script>';
if (!html.includes(tag)) { console.error('✗ template is missing the validate.js script tag'); process.exit(1); }
html = html.replace(tag, () => `<script>\n${safe(validator)}\n</script>`);
const blocks = `<script type="application/json" id="dashboard-data">${safe(JSON.stringify(data))}</script>\n<script type="application/json" id="dashboard-schema">${safe(JSON.stringify(schema))}</script>\n`;
const i = html.lastIndexOf('<script>');
html = html.slice(0, i) + blocks + html.slice(i);
fs.mkdirSync(path.dirname(path.resolve(out)), {recursive: true});
fs.writeFileSync(out, html);
const kb = Math.round(fs.statSync(out).size / 1024);
console.log(`✓ wrote ${out} (${kb} KB) · ${Object.keys(data.datasets).length} datasets, ${data.tabs.length} tabs`);
