#!/usr/bin/env node
// Gauntlet evidence: screenshot the reference game (BrowserQuest) in the same
// situations as capture.js, so the critic can compare like with like.
//
//   node tools/gauntlet/capture-ref.js --setup      # clone + patch + install (once)
//   node tools/gauntlet/capture-ref.js --serve      # start game server :8000 + static client :8001
//   xvfb-run -a node tools/gauntlet/capture-ref.js  # capture -> docs/gauntlet/reference/browserquest/<label>.png
const fs = require('fs');
const path = require('path');
const net = require('net');
const { spawn, execSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..', '..');
const CFG = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'));
const ROOMS = JSON.parse(fs.readFileSync(path.join(__dirname, 'rooms.json'), 'utf8'));
const REF = CFG.reference;
const DIR = path.join(ROOT, REF.dir);
const OUT = path.join(ROOT, 'docs', 'gauntlet', 'reference', 'browserquest');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const has = f => process.argv.includes(f);
function portOpen(port) { return new Promise(res => { const s = net.connect(port, 'localhost'); s.once('connect', () => { s.end(); res(true); }); s.once('error', () => res(false)); }); }

function setup() {
  if (!fs.existsSync(DIR)) execSync(`git clone -q --depth 1 https://github.com/mozilla/BrowserQuest.git "${DIR}"`, { stdio: 'inherit' });
  // node-22 patches (the archived repo targets node 0.4)
  const w = (f, fn) => { const p = path.join(DIR, f); fs.writeFileSync(p, fn(fs.readFileSync(p, 'utf8'))); };
  fs.writeFileSync(path.join(DIR, 'package.json'), JSON.stringify({ name: 'BrowserQuest', version: '0.0.1', private: true,
    dependencies: { underscore: '1.13.7', log: '1.4.0', bison: '1.1.1', websocket: '1.0.35' } }, null, 2));
  w('server/js/utils.js', s => s.replace("sanitizer = require('sanitizer'),\n", '')
    .replace('return sanitizer.escape(sanitizer.sanitize(string));',
      "return String(string||'').replace(/<[^>]*>/g,'').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[c]));"));
  w('server/js/ws.js', s => s
    .replace('    wsserver = require("websocket-server"),\n    miksagoConnection = require(\'websocket-server/lib/ws/connection\'),\n', '')
    .replace(/        this\._miksagoServer = wsserver\.createServer\(\);[\s\S]*?        \}\);\n        \n/, '')
    .replace(/            \} else \{\n                \/\/ WebSocket hixie-75[\s\S]*?\n            \}\n        \}\);/, '            }\n        });'));
  w('server/js/map.js', s => s.replace('path.exists(', 'fs.exists('));
  w('client/js/main.js', s => s.includes('window.game = game') ? s : s.replace('game = new Game(app);', 'game = new Game(app); window.game = game;'));
  const cfg = JSON.stringify({ host: 'localhost', port: REF.serverPort, dispatcher: false }, null, 2);
  fs.writeFileSync(path.join(DIR, 'client/config/config_local.json'), cfg);
  fs.writeFileSync(path.join(DIR, 'client/config/config_build.json'), cfg);
  execSync('npm install --no-audit --no-fund', { cwd: DIR, stdio: 'inherit' });
  console.log('reference ready at', path.relative(ROOT, DIR));
}

async function serve() {
  if (!(await portOpen(REF.serverPort))) spawn('node', ['server/js/main.js'], { cwd: DIR, detached: true, stdio: 'ignore' }).unref();
  if (!(await portOpen(REF.clientPort))) spawn('http-server', [DIR, '-p', String(REF.clientPort), '-s'], { detached: true, stdio: 'ignore' }).unref();
  for (let i = 0; i < 20; i++) { if ((await portOpen(REF.serverPort)) && (await portOpen(REF.clientPort))) return true; await sleep(500); }
  return false;
}

async function capture() {
  if (!(await serve())) { console.error('reference servers did not come up'); process.exit(2); }
  const { chromium } = require('playwright');
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: CFG.viewport, deviceScaleFactor: 1 });
  await page.goto(REF.clientUrl, { waitUntil: 'load' });
  await page.waitForSelector('#nameinput', { timeout: 20000 });
  await sleep(1500);
  await page.click('#nameinput'); await page.keyboard.type('Critic'); await sleep(300);
  await page.click('#createcharacter .play');
  let started = false;
  for (let i = 0; i < 40 && !started; i++) { await sleep(500); started = await page.evaluate(() => !!(window.game && game.started && game.player)); }
  if (!started) { console.error('reference game did not start'); process.exit(3); }
  await sleep(1500);
  // close the "how to play" parchment (click inside the game area)
  await page.mouse.click(640, 400); await sleep(600);
  await page.evaluate(() => { const el = document.getElementById('instructions'); if (el) el.style.display = 'none'; });
  const manifest = { reference: REF.name, viewport: CFG.viewport, shots: [] };
  for (const r of ROOMS) {
    const ref = r.ref || {};
    if (ref.attackNearest) {
      // walk to the nearest mob (client Mob instances carry aggroRange) and attack it
      const found = await page.evaluate(() => {
        game.camera.lookAt(game.player);
        let best = null, bd = 1e9;
        for (const id in game.entities) {
          const e = game.entities[id];
          if (!e || e === game.player || e.aggroRange === undefined) continue;
          const d = Math.abs(e.gridX - game.player.gridX) + Math.abs(e.gridY - game.player.gridY);
          if (d < bd) { bd = d; best = e; }
        }
        if (!best) return null;
        game.makePlayerAttack(best);
        return { kind: best.kind, d: bd };
      });
      if (!found) console.warn('combat: no mob in range, shot will show the idle player');
      await sleep(2600);
      await page.evaluate(() => game.camera.lookAt(game.player));
      await sleep(200);
    } else if (ref.camera) {
      await page.evaluate(([x, y]) => { game.camera.setGridPosition(x, y); game.renderer.renderStaticCanvases(); }, ref.camera);
      await sleep(900);
    }
    const file = path.join(OUT, `${r.label}.png`);
    // clip to the game frame so page chrome (logo, share links) is not judged
    const frame = await page.$('#container');
    if (frame) await frame.screenshot({ path: file }); else await page.screenshot({ path: file });
    manifest.shots.push({ label: r.label, camera: ref.camera || null, note: ref.note || '', file: path.relative(ROOT, file) });
    console.log('ok    ', r.label);
  }
  fs.writeFileSync(path.join(OUT, 'capture.json'), JSON.stringify(manifest, null, 2));
  await browser.close();
  console.log(`wrote ${manifest.shots.length} reference shots to ${path.relative(ROOT, OUT)}`);
}

(async () => {
  if (has('--setup')) return setup();
  if (has('--serve')) { console.log((await serve()) ? 'reference serving' : 'failed'); return; }
  await capture();
})().catch(e => { console.error(e); process.exit(1); });
