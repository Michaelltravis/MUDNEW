#!/usr/bin/env node
// Gauntlet evidence: blind A/B pairs. For each label, place the Misthollow shot
// and the reference shot side by side in a seeded-random order with only "A"
// and "B" captions. The answer key goes to pairs/key.json — the critic must
// never read it; only the lead decodes verdicts with it.
//
//   node tools/gauntlet/montage.js --run graphics-01 --round 1 [--ref browserquest] [--seed 42] [--only city,combat]
//   node tools/gauntlet/montage.js --sheet out.png label=a.png label=b.png ...   (contact sheet helper)
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
function arg(name, dflt) { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : dflt; }
function rng(seedStr) { let h = 1779033703 ^ seedStr.length; for (let i = 0; i < seedStr.length; i++) { h = Math.imul(h ^ seedStr.charCodeAt(i), 3432918353); h = h << 13 | h >>> 19; } return () => { h = Math.imul(h ^ h >>> 16, 2246822507); h = Math.imul(h ^ h >>> 13, 3266489909); return ((h ^= h >>> 16) >>> 0) / 4294967296; }; }
const b64 = f => fs.readFileSync(f).toString('base64');

async function render(html, out, width, height) {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width, height } });
  await page.setContent(html); await page.waitForTimeout(200);
  await page.screenshot({ path: out, fullPage: true }); await browser.close();
}

(async () => {
  if (process.argv.includes('--sheet')) {
    const [out, ...pairs] = process.argv.slice(process.argv.indexOf('--sheet') + 1);
    const cols = 3, W = 420, H = 236;
    const cells = pairs.map(p => { const [label, file] = p.split('='); return `<div class="c"><img src="data:image/png;base64,${b64(file)}"><span>${label}</span></div>`; }).join('');
    await render(`<style>body{margin:0;background:#111}.g{display:grid;grid-template-columns:repeat(${cols},${W}px);gap:4px}.c{position:relative;width:${W}px;height:${H}px}.c img{width:100%;height:100%;object-fit:cover}.c span{position:absolute;left:4px;top:4px;background:#000c;color:#fff;font:bold 15px sans-serif;padding:2px 6px}</style><div class="g">${cells}</div>`,
      out, cols * (W + 4), Math.ceil(pairs.length / cols) * (H + 4));
    console.log('sheet', out); return;
  }
  const RUN = arg('run', 'smoke'), ROUND = arg('round', '0'), REF = arg('ref', 'browserquest');
  const ONLY = (arg('only', '') || '').split(',').filter(Boolean);
  const roundDir = path.join(ROOT, 'docs', 'gauntlet', RUN, `round-${ROUND}`);
  const mhDir = path.join(roundDir, 'mh'), refDir = path.join(ROOT, 'docs', 'gauntlet', 'reference', REF);
  const outDir = path.join(roundDir, 'pairs'); fs.mkdirSync(outDir, { recursive: true });
  const seed = arg('seed', `${RUN}:${ROUND}`);
  const rand = rng(String(seed));
  const key = {};
  // ONE A/B order per round: the critic gives a single overall letter, which is
  // only decodable if every label in the round shares the same mapping.
  const mhFirst = rand() < 0.5;
  const labels = fs.readdirSync(mhDir).filter(f => f.endsWith('.png') && !f.startsWith('_')).map(f => f.replace(/\.png$/, ''))
    .filter(l => !ONLY.length || ONLY.includes(l));
  for (const label of labels) {
    const mh = path.join(mhDir, `${label}.png`), ref = path.join(refDir, `${label}.png`);
    if (!fs.existsSync(ref)) { console.warn(`no reference shot for ${label}, skipped`); continue; }
    const [A, B] = mhFirst ? [mh, ref] : [ref, mh];
    key[label] = { A: mhFirst ? 'mh' : 'ref', B: mhFirst ? 'ref' : 'mh' };
    const W = 1280, H = 720, S = 1;   // full scale so text size is judged as rendered
    const html = `<style>body{margin:0;background:#000}.row{display:flex;gap:8px;padding:8px}.p{position:relative;width:${W * S}px;height:${H * S}px}.p img{width:100%;height:100%;object-fit:contain;background:#000}.p span{position:absolute;left:8px;top:8px;background:#000d;color:#fff;font:bold 28px sans-serif;padding:2px 10px;border-radius:4px}</style>
      <div class="row"><div class="p"><img src="data:image/png;base64,${b64(A)}"><span>A</span></div><div class="p"><img src="data:image/png;base64,${b64(B)}"><span>B</span></div></div>`;
    await render(html, path.join(outDir, `${label}.png`), W * S * 2 + 24, H * S + 16);
    console.log('pair  ', label);
  }
  fs.writeFileSync(path.join(outDir, 'key.json'), JSON.stringify({ run: RUN, round: ROUND, reference: REF, seed, key }, null, 2));
  console.log(`wrote ${Object.keys(key).length} pairs + key.json to ${path.relative(ROOT, outDir)}`);
})().catch(e => { console.error(e); process.exit(1); });
