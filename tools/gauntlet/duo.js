// Gauntlet evidence: two live clients (Gauntlet, Gauntletb) in one room.
// CMDS='[["A","goto 3014"],["B","goto 3014"],["B","follow Gauntlet"],["A","group Gauntletb"],["B","group accept"],["A","kill cityguard"]]' \
//   OUT=docs/gauntlet/<run>/round-<n>/mh NODE_PATH=/opt/node22/lib/node_modules xvfb-run -a node tools/gauntlet/duo.js
// Writes duo_A.png and duo_B.png. Both characters are admin accounts (see tools/gauntlet/README.md).
const { chromium } = require('playwright');
async function login(ctx, name) {
  const page = await ctx.newPage();
  page.on('pageerror', e => console.log(name, 'pageerror:', String(e).slice(0, 140)));
  await page.goto('http://localhost:4001/platformer?gauntlet=1', { waitUntil: 'load' });
  await page.waitForSelector('#login-name'); await page.fill('#login-name', name); await page.fill('#login-pass', 'gauntlet1'); await page.click('#login-btn');
  for (let i = 0; i < 40; i++) { await page.waitForTimeout(500); if (await page.evaluate(() => !!(window.MH && MH.state.currentRoom))) break; }
  await page.evaluate(() => { window.__out = []; MH.bus.on('terminal.output', t => __out.push(String(t.text).replace(/\s+/g, ' ').slice(0, 140))); });
  return page;
}
(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'] });
  const ctxA = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const ctxB = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const A = await login(ctxA, 'Gauntlet'), B = await login(ctxB, 'Gauntletb');
  const cmds = JSON.parse(process.env.CMDS || '[]');
  for (const [who, c] of cmds) { await (who === 'A' ? A : B).evaluate(x => MH.sendCommand(x, false), c); await A.waitForTimeout(900); }
  await A.waitForTimeout(3500);
  const info = await A.evaluate(() => ({ vnum: MH.state.player.vnum, group: MH.state.lastPayload && MH.state.lastPayload.group, keys: Object.keys(MH.state.lastPayload || {}), cur: MH.state.lastPayload.current_room && Object.keys(MH.state.lastPayload.current_room), out: __out.slice(-6) }));
  console.log('B:', JSON.stringify(await B.evaluate(() => ({ vnum: MH.state.player.vnum, out: __out.slice(-5) }))).slice(0, 700));
  console.log(JSON.stringify(info).slice(0, 600));
  await A.screenshot({ path: process.env.OUT + '/duo_A.png' }); await B.screenshot({ path: process.env.OUT + '/duo_B.png' });
  await A.evaluate(() => MH.sendCommand('quit', false)); await B.evaluate(() => MH.sendCommand('quit', false)); await browser.close();
})();
