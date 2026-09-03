#!/usr/bin/env node
// Gauntlet evidence: screenshot Misthollow's platformer client in a fixed set
// of situations. Deterministic where the game allows it (fixed hour/weather
// via admin commands, seeded Math.random in the page, first-run tips silenced).
//
//   xvfb-run -a node tools/gauntlet/capture.js --run graphics-01 --round 1 [--only city,combat] [--out DIR]
//
// Output: docs/gauntlet/<run>/round-<N>/mh/<label>.png  (+ capture.json manifest)
// Requires: the MUD running (./run.sh) with web_map (:4001) and web_client (:4003),
// global playwright (NODE_PATH=/opt/node22/lib/node_modules) and Chromium.
const fs = require('fs');
const path = require('path');
const net = require('net');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
const CFG = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'));
const ROOMS = JSON.parse(fs.readFileSync(path.join(__dirname, 'rooms.json'), 'utf8'));

function arg(name, dflt) { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : dflt; }
const RUN = arg('run', 'smoke'), ROUND = arg('round', '0');
const ONLY = (arg('only', '') || '').split(',').filter(Boolean);
const OUT = arg('out', path.join(ROOT, 'docs', 'gauntlet', RUN, `round-${ROUND}`, 'mh'));
const SEED = parseInt(arg('seed', '1337'), 10);

function portOpen(port, host = 'localhost') {
  return new Promise(res => { const s = net.connect(port, host); s.once('connect', () => { s.end(); res(true); }); s.once('error', () => res(false)); });
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

// mean pixel variance guard: a blank/black frame is not evidence
function isBlankPng(buf) {
  // cheap heuristic: PNG of a flat frame compresses extremely well
  return buf.length < 12000;
}

(async () => {
  for (const p of [CFG.mud.telnetPort, CFG.mud.mapPort, CFG.mud.cmdPort]) {
    if (!(await portOpen(p))) { console.error(`port ${p} closed: start the MUD with ./run.sh (needs aiohttp for :4003)`); process.exit(2); }
  }
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const ctx = await browser.newContext({ viewport: CFG.viewport, deviceScaleFactor: 1, reducedMotion: 'no-preference' });
  // determinism inside the page: seeded RNG + silence one-time teaching UI
  await ctx.addInitScript(({ seed }) => {
    let a = seed >>> 0;
    Math.random = function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
    try {
      localStorage.setItem('mh_welcome_seen', '1');
      localStorage.setItem('misthollow_hints_done', '1');
      for (const k of ['guard', 'sweetspot', 'poise', 'windup', 'flanked', 'trap', 'hazards', 'door', 'env', 'intent']) localStorage.setItem('mh_tip_' + k, '1');
      localStorage.setItem('misthollow_gfx_quality', 'high');
      localStorage.setItem('misthollow_gfx_motion', '0');
    } catch (_) {}
  }, { seed: SEED });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e).slice(0, 200)));

  await page.goto(`http://${CFG.mud.host}:${CFG.mud.mapPort}/platformer?gauntlet=1`, { waitUntil: 'load' });
  await page.waitForSelector('#login-name', { timeout: 20000 });
  await page.fill('#login-name', CFG.character.name);
  await page.fill('#login-pass', CFG.character.password);
  await page.click('#login-btn');
  let ok = false;
  for (let i = 0; i < 40 && !ok; i++) { await sleep(500); ok = await page.evaluate(() => !!(window.MH && MH.state.currentRoom)); }
  if (!ok) { console.error('login did not reach a room'); await page.screenshot({ path: path.join(OUT, '_login_failed.png') }); process.exit(3); }

  const send = async cmd => page.evaluate(c => MH.sendCommand(c, false), cmd);
  const roomName = () => page.evaluate(() => (MH.state.currentRoom && (MH.state.currentRoom.name || MH.state.currentRoom.vnum)) || '');
  // fixed world conditions (immortal-only commands; harmless if refused)
  await send(`advance ${CFG.character.name} ${CFG.character.level}`); await sleep(400);
  for (const c of CFG.setup) { await send(c); await sleep(300); }
  // dismiss any overlay that survived the localStorage flags
  await page.evaluate(() => { for (const id of ['welcome-overlay']) { const el = document.getElementById(id); if (el) el.classList.remove('show'); } });

  const manifest = { run: RUN, round: ROUND, seed: SEED, viewport: CFG.viewport, setup: CFG.setup, shots: [], errors };
  for (const r of ROOMS) {
    if (ONLY.length && !ONLY.includes(r.label)) continue;
    await send(`goto ${r.vnum}`);
    let arrived = false;
    for (let i = 0; i < 20 && !arrived; i++) { await sleep(250); arrived = await page.evaluate(v => !!(MH.state.currentRoom && String(MH.state.currentRoom.vnum) === String(v)), r.vnum); }
    for (const c of (r.cmds || [])) { await send(c); await sleep(200); }
    await sleep(r.waitMs || 4500);   // let the zone title card and arrival description fade
    const file = path.join(OUT, `${r.label}.png`);
    let buf;
    if (r.filmstrip) {
      // combat feel: N frames at a fixed interval composed into one storyboard
      const frames = [];
      for (let i = 0; i < r.filmstrip.frames; i++) {
        frames.push((await page.screenshot()).toString('base64'));
        await sleep(r.filmstrip.intervalMs);
      }
      const cols = r.filmstrip.cols || 4, W = 640, H = 360;
      const html = `<style>body{margin:0;background:#000}.g{display:grid;grid-template-columns:repeat(${cols},${W}px);gap:6px;padding:6px}.c{position:relative;width:${W}px;height:${H}px}.c img{width:100%;height:100%}.c span{position:absolute;left:6px;top:6px;background:#000c;color:#fff;font:bold 18px sans-serif;padding:1px 8px;border-radius:3px}</style><div class="g">${frames.map((b, i) => `<div class="c"><img src="data:image/png;base64,${b}"><span>${(i * r.filmstrip.intervalMs / 1000).toFixed(1)}s</span></div>`).join('')}</div>`;
      const strip = await ctx.newPage({ viewport: { width: cols * (W + 6) + 6, height: Math.ceil(frames.length / cols) * (H + 6) + 6 } });
      await strip.setContent(html); await sleep(200);
      buf = await strip.screenshot({ path: file, fullPage: true });
      await strip.close();
    } else {
      buf = await page.screenshot({ path: file });
    }
    const blank = isBlankPng(buf);
    manifest.shots.push({ label: r.label, vnum: r.vnum, room: await roomName(), arrived, file: path.relative(ROOT, file), bytes: buf.length, blank });
    console.log(`${blank ? 'BLANK ' : 'ok    '} ${r.label.padEnd(8)} ${await roomName()}`);
    for (const c of (r.after || [])) { await send(c); await sleep(400); }
  }
  await send('quit');
  await sleep(300);
  fs.writeFileSync(path.join(OUT, 'capture.json'), JSON.stringify(manifest, null, 2));
  await browser.close();
  const bad = manifest.shots.filter(s => s.blank || !s.arrived);
  if (bad.length) { console.error('problem shots:', bad.map(s => s.label).join(', ')); process.exit(4); }
  console.log(`wrote ${manifest.shots.length} shots to ${path.relative(ROOT, OUT)}`);
})().catch(e => { console.error(e); process.exit(1); });
