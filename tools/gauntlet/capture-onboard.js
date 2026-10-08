#!/usr/bin/env node
// Gauntlet evidence for the ONBOARDING piece ("easy to start"): two labels,
// filmed as a brand-new player sees them, with nothing dismissed.
//   start — the moment you choose who you are (our class step / BrowserQuest's name screen)
//   first — the first screen in the world, with whatever the game shows a newcomer
// Misthollow side forges a fresh level-1 character through the real wizard
// (random name, human, --class warrior, keep stats) and lands in the temple.
// Reference side plays BrowserQuest from its intro screen.
//
//   xvfb-run -a node tools/gauntlet/capture-onboard.js --run onboard-01 --round 1 [--class warrior] [--ref]
const fs = require('fs'); const path = require('path'); const net = require('net');
const { chromium } = require('playwright');
const ROOT = path.resolve(__dirname, '..', '..');
const CFG = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'));
function arg(name, dflt) { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : dflt; }
const RUN = arg('run', 'onboard-01'), ROUND = arg('round', '1'), CLASS = arg('class', 'warrior');
const DO_REF = process.argv.includes('--ref');
const OUT = path.join(ROOT, 'docs', 'gauntlet', RUN, `round-${ROUND}`, 'mh');
const REF_OUT = path.join(ROOT, 'docs', 'gauntlet', 'reference', 'browserquest');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const until = async (fn, tries = 40, ms = 500) => { for (let i = 0; i < tries; i++) { if (await fn()) return true; await sleep(ms); } return false; };

async function mh(browser) {
  fs.mkdirSync(OUT, { recursive: true });
  const ctx = await browser.newContext({ viewport: CFG.viewport, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errors = []; page.on('pageerror', e => errors.push(String(e).slice(0, 200)));
  await page.goto(`http://${CFG.mud.host}:${CFG.mud.mapPort}/platformer?gauntlet=1`, { waitUntil: 'load' });
  await page.waitForSelector('#login-name', { timeout: 20000 }); await sleep(2500);
  const name = 'New' + Math.random().toString(36).replace(/[^a-z]/g, '').slice(0, 5).replace(/^./, c => c.toUpperCase());
  await page.fill('#login-name', name); await page.fill('#login-pass', 'newcomer1');
  await page.click('#create-btn');
  const t = () => page.evaluate(() => (document.getElementById('cw-title') || {}).textContent || '');
  if (!(await until(async () => /LINEAGE/.test(await t())))) throw new Error('wizard: no race step');
  await page.click('.cw-pick[data-v="human"]');
  if (!(await until(async () => /CALLING/.test(await t())))) throw new Error('wizard: no class step');
  await sleep(2200);
  await page.hover(`.cw-pick[data-v="${CLASS}"]`); await sleep(500);
  await page.click(`.cw-pick[data-v="${CLASS}"]`);   // focus the class (big preview + Choose button)
  await sleep(600);
  await page.screenshot({ path: path.join(OUT, 'start.png') });
  await page.evaluate(() => { const b = document.getElementById('cw-choose'); if (b) b.click(); });   // (a real click is swallowed by the animating preview canvas under Playwright's stability check)
  if (!(await until(async () => /FATE/.test(await t())))) throw new Error('wizard: no stats step; title=' + await t() + '; status=' + await page.evaluate(() => (document.getElementById('cw-status') || {}).textContent) + '; errors=' + JSON.stringify(errors));
  await page.click('#cw-keep');
  if (!(await until(() => page.evaluate(() => !!(window.MH && MH.state.currentRoom)), 60))) throw new Error('did not reach a room');
  // the first screen exactly as a newcomer gets it: welcome card, Guide, three buttons
  await sleep(6000);
  await page.screenshot({ path: path.join(OUT, 'first.png') });
  const info = await page.evaluate(() => ({ room: MH.state.currentRoom && MH.state.currentRoom.name, level: MH.state.player && MH.state.player.level,
    guide: (document.getElementById('guide') || {}).innerText, slots: document.querySelectorAll('.hotslot:not(.locked)').length }));
  fs.writeFileSync(path.join(OUT, 'capture.json'), JSON.stringify({ run: RUN, round: ROUND, character: name, class: CLASS, info, errors }, null, 2));
  console.log('mh', name, JSON.stringify(info));
  await ctx.close();
}

async function ref(browser) {
  const REF = CFG.reference;
  const ctx = await browser.newContext({ viewport: CFG.viewport, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  await page.goto(REF.clientUrl, { waitUntil: 'load' });
  await page.waitForSelector('#nameinput', { timeout: 20000 }); await sleep(2000);
  await page.click('#nameinput'); await page.keyboard.type('Newcomer'); await sleep(400);
  await page.screenshot({ path: path.join(REF_OUT, 'start.png') });
  await page.click('#createcharacter .play');
  await until(() => page.evaluate(() => !!(window.game && game.started && game.player)));
  await sleep(6000);   // the "how to play" parchment stays, as a newcomer sees it
  await page.screenshot({ path: path.join(REF_OUT, 'first.png') });
  console.log('ref start+first');
  await ctx.close();
}

(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  try {
    if (DO_REF) await ref(browser);
    await mh(browser);
  } catch (e) { console.error(String(e)); process.exitCode = 1; }
  await browser.close();
})();
