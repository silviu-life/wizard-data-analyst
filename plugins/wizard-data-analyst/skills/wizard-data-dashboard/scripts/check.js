#!/usr/bin/env node
/* Open a built dashboard in headless Chromium and check that it really works.
   node scripts/check.js <dashboard.html> [screenshots-dir]
   Fails (exit 1) on: the "can't be shown" validation screen, JS errors, a card that shows an error, a card with nothing drawn.
   Warns on: cards showing an empty state, failed network requests (d3/topojson/map CDN).
   Writes one full-page screenshot per tab when a screenshots dir is given. Needs Playwright (local or global npm). */
const path = require('path'), fs = require('fs'), { execSync } = require('child_process');
const [file, shots] = process.argv.slice(2);
if (!file) { console.error('usage: node check.js <dashboard.html> [screenshots-dir]'); process.exit(2); }

function loadPlaywright() {
  try { return require('playwright'); } catch {}
  try { return require(path.join(execSync('npm root -g').toString().trim(), 'playwright')); } catch {}
  console.error('✗ Playwright not found. Install it once: npm i -g playwright && npx playwright install chromium');
  process.exit(2);
}

(async () => {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [], warnings = [];
  page.on('pageerror', e => errors.push(`JS error: ${e.message}`));
  page.on('console', m => { if (m.type() === 'error') errors.push(`console: ${m.text()}`); });
  page.on('requestfailed', r => warnings.push(`request failed: ${r.url()} (${r.failure()?.errorText})`));
  await page.goto('file://' + path.resolve(file));
  await page.waitForSelector('#nav a, .inv', { timeout: 30000 });
  if (await page.$('.inv')) {
    console.error('✗ the page shows the validation screen:\n' + (await page.$$eval('.inv li', ls => ls.map(l => '  ' + l.innerText).join('\n'))));
    process.exit(1);
  }
  if (shots) fs.mkdirSync(shots, { recursive: true });
  const tabs = await page.$$eval('#nav a', as => as.map(a => ({ id: a.dataset.tab, label: a.innerText.trim() })));
  let cards = 0;
  for (const [i, t] of tabs.entries()) {
    await page.click(`#nav a[data-tab="${t.id}"]`);
    await page.waitForTimeout(1500);  // charts draw after d3 transitions
    const res = await page.$$eval('article.card', cs => cs.map(c => {
      const b = c.querySelector('.body');
      return {
        title: (c.querySelector('.card-t')?.innerText || '').trim(),
        err: c.querySelector('.err')?.innerText,
        empty: !!c.querySelector('.empty'),
        drawn: !!b && (b.querySelector('svg *, table, canvas, .tbl-r, .coh-c, .rk') !== null || b.innerText.trim().length > 0),
      };
    }));
    cards += res.length;
    const bad = res.filter(r => r.err || !r.drawn);
    bad.forEach(r => errors.push(`tab "${t.label}" · card "${r.title}": ${r.err || 'nothing drawn'}`));
    res.filter(r => r.empty && !r.err).forEach(r => warnings.push(`tab "${t.label}" · card "${r.title}" shows an empty state`));
    console.log(`  ${bad.length ? '✗' : '✓'} ${t.label.padEnd(24)} ${res.length} cards`);
    if (shots) await page.screenshot({ path: path.join(shots, `${String(i + 1).padStart(2, '0')}-${t.id}.png`), fullPage: true });
  }
  await browser.close();
  warnings.forEach(w => console.log(`  ! ${w}`));
  if (errors.length) { console.error(`✗ ${errors.length} problem(s):\n` + [...new Set(errors)].map(e => '  ' + e).join('\n')); process.exit(1); }
  console.log(`✓ ${file}: ${tabs.length} tabs, ${cards} cards, all rendered`);
})().catch(e => { console.error('✗ ' + e.message); process.exit(1); });
