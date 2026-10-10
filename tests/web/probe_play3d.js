// Browser probe for /play against a local server (./run.sh), with the gauntlet admin account.
//   NODE_PATH=/opt/node22/lib/node_modules node tests/web/probe_play3d.js stairs|doors|camera|menu|autotarget|creatures [outdir]
// CommonJS on purpose (the global Playwright only resolves through NODE_PATH with require).
// WebGL may render at ~1 fps in a container, so the probe places the hero directly and waits
// on frames instead of walking in real time.
//   stairs: the zone map download is delayed 3 s (the race that sent every zone hop twice);
//           taking the temple's ▲ stairs must send exactly one move, show no "can't go", land
//           beside the destination's ▼ stairs, and a key held into them must not hop back.
//   doors:  the oak door at 921 east: the prompt says what E does, E opens it (one webdoor),
//           and a locked door without the key says which key it needs.
//   camera: a right-drag turns the view (no menu), W follows the camera, drag up tilts, Home
//           snaps back north.
//   menu:   a right-click on a creature offers Attack/Consider (naming it exactly), on the
//           hero "You".
//   autotarget: a creature that hits you becomes your target; a foe you picked stays.
//   creatures: a blob, a mimic, a statue, a chess rook, a stone golem, a goblin farmer, a brownie,
//           a living book and the Sewer King each get the right body (looks.js, from the payload's
//           short description and room line).
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const MODE = process.argv[2] || 'stairs';
const OUT = process.argv[3] || '/tmp';
const CFG = JSON.parse(fs.readFileSync(path.join(__dirname, '../../tools/gauntlet/config.json'), 'utf8'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
const results = [];
const check = (ok, what) => { results.push([ok, what]); console.log(`${ok ? 'ok  ' : 'FAIL'} ${what}`); };

async function waitFor(page, fn, arg, secs = 60) {
  for (let i = 0; i < secs * 4; i++) {
    if (await page.evaluate(fn, arg).catch(() => false)) return true;
    await sleep(250);
  }
  return false;
}

(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'] });
  const page = await (await browser.newContext({ viewport: { width: 960, height: 540 } })).newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e).slice(0, 300)));
  if (MODE === 'stairs') {
    await page.route('**/zonemap*', async route => { await sleep(3000); await route.continue(); });
  }
  await page.goto(`http://${CFG.mud.host}:${CFG.mud.mapPort}/play?q=low`, { waitUntil: 'load' });
  await waitFor(page, () => document.getElementById('loading').classList.contains('done'));
  await page.fill('#login-name', CFG.character.name);
  await page.fill('#login-pass', CFG.character.password);
  await page.click('#login-btn');
  check(await waitFor(page, () => !!(window.MH3D && MH3D.hero), null, 120), 'logged in, hero in the world');
  await page.evaluate(() => {
    window.__sent = [];
    const real = MH.sendCommand;
    MH.sendCommand = (cmd, echo) => { window.__sent.push(String(cmd)); return real(cmd, echo); };
    window.__toasts = [];
    new MutationObserver(m => { for (const r of m) for (const n of r.addedNodes) window.__toasts.push(n.textContent); })
      .observe(document.getElementById('toasts'), { childList: true });
  });
  const goto = async v => {
    await page.evaluate(v => MH.sendCommand(`goto ${v}`, false), v);
    return waitFor(page, v => MH3D.heroRoom() && MH3D.heroRoom().vnum === v && !MH3D.hop(), v, 90);
  };

  if (MODE === 'stairs') {
    check(await goto(3001), 'in the Temple of Midgaard (3001)');
    await sleep(1500);
    // stand 1.3 m west of the ▲ stairs and walk onto them on purpose
    const info = await page.evaluate(() => {
      const z = MH3D.zone(), r = MH3D.heroRoom(), sp = z.passageWorld(r, 'up');
      MH3D.hero.root.position.set(sp.x - 1.3, 0, sp.z);
      window.__sent.length = 0; window.__toasts.length = 0;
      MH3D.walkToPassage('up');
      return { to: r.data.exits.up && r.data.exits.up.to, kind: r.data.exits.up && r.data.exits.up.kind };
    });
    check(!!info.to, `the temple has stairs up (to ${info.to}, ${info.kind})`);
    // the bounce case: a key held through the hop, toward the stairs you arrive beside
    await waitFor(page, () => !!MH3D.hop(), null, 60);
    await page.evaluate(() => MH3D.ctl.keys.add('a'));
    const landed = await waitFor(page, to => MH3D.heroRoom() && MH3D.heroRoom().vnum === to && !MH3D.hop(), info.to, 120);
    check(landed, `took the stairs to ${info.to}`);
    const dist = await page.evaluate(() => {
      const z = MH3D.zone(), r = MH3D.heroRoom(), p = MH3D.hero.root.position;
      const sp = r.data.exits.down ? z.passageWorld(r, 'down') : null;
      return sp ? Math.hypot(p.x - sp.x, p.z - sp.z) : null;
    });
    check(dist != null && dist < 2.4, `landed beside the stairs back down (${dist && dist.toFixed(2)} m)`);
    await sleep(8000);                                  // still holding the key toward them
    await page.evaluate(() => MH3D.ctl.keys.delete('a'));
    const moves = await page.evaluate(() => window.__sent.filter(c => c.startsWith('webmove')));
    check(moves.length === 1 && / up$/.test(moves[0]), `exactly one move sent, no bounce back: ${JSON.stringify(moves)}`);
    const toasts = await page.evaluate(() => window.__toasts.join(' | '));
    check(!/can't go/i.test(toasts), `no "can't go that way" (${toasts || 'no toasts'})`);
    await page.screenshot({ path: path.join(OUT, 'stairs-landed.png') });
    // a deliberate return: stand still a moment, then walk onto them
    await sleep(1500);
    await page.evaluate(() => { window.__sent.length = 0; MH3D.walkToPassage('down'); });
    const back = await waitFor(page, () => window.__sent.some(c => / down$/.test(c)), null, 60);
    check(back, 'walking onto them on purpose takes them back down');
  }

  if (MODE === 'doors') {
    check(await goto(921), 'at the oak door (921)');
    await page.evaluate(() => { MH.sendCommand('open east', false); });
    await sleep(800);
    await page.evaluate(() => MH.sendCommand('close east', false));
    await waitFor(page, () => MH3D.heroRoom().doors.east && MH3D.heroRoom().doors.east.closed, null, 20);
    const at = await page.evaluate(() => {
      const r = MH3D.heroRoom();
      const p = MH3D.hero.root.position;
      p.set(r.ox + 24 - 1.6, 0, r.oz + 7.5);
      return [p.x, p.z];
    });
    await sleep(2500);
    const text = await page.evaluate(() => !document.getElementById('prompt').classList.contains('hidden') && document.querySelector('#prompt span').textContent);
    check(/open the oak door/i.test(text || ''), `prompt: "${text}"`);
    await page.screenshot({ path: path.join(OUT, 'door-prompt.png') });
    await page.evaluate(() => { window.__sent.length = 0; });
    await page.keyboard.press('e');
    const opened = await waitFor(page, () => MH3D.heroRoom().doors.east && !MH3D.heroRoom().doors.east.closed, null, 20);
    const sent = await page.evaluate(() => window.__sent.filter(c => c.startsWith('webdoor')));
    check(opened && sent.length === 1 && sent[0] === 'webdoor 921 east open', `E opened it with one webdoor: ${JSON.stringify(sent)}`);
    const meshOpen = await page.evaluate(() => {
      const r = MH3D.heroRoom();
      const m = r.built && r.built.doors && r.built.doors.east;
      return m ? m.userData.open : 'no mesh';
    });
    check(meshOpen === true, `the door mesh swung open (${meshOpen})`);
    // lock it without the key: the prompt names the key
    await page.evaluate(() => { for (const c of ['oload 900', 'close east', 'lock east', 'drop key', 'drop key', 'drop key', 'purge']) MH.sendCommand(c, false); });
    await sleep(2500);
    await page.evaluate(() => MH.refreshState && MH.refreshState());   // keys are per viewer: ask again
    await waitFor(page, () => MH3D.heroRoom().doors.east && MH3D.heroRoom().doors.east.locked, null, 20);
    await sleep(2500);
    const locked = await page.evaluate(() => document.querySelector('#prompt span').textContent);
    check(/needs a golden key/i.test(locked || ''), `locked prompt: "${locked}"`);
    await page.screenshot({ path: path.join(OUT, 'door-locked.png') });
    // leave it as the zone keeps it
    await page.evaluate(() => { for (const c of ['oload 900', 'unlock east', 'open east', 'drop key', 'drop key', 'drop key', 'purge']) MH.sendCommand(c, false); });
    await sleep(2000);
  }

  if (MODE === 'camera') {
    check(await goto(3001), 'in the Temple of Midgaard (3001)');
    await sleep(1500);
    const box = await page.evaluate(() => { const r = MH3D.engine.renderer.domElement.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; });
    // right-drag 120 px to the right: the view turns right, and no menu opens
    await page.mouse.move(box.x, box.y);
    await page.mouse.down({ button: 'right' });
    await page.mouse.move(box.x + 120, box.y, { steps: 8 });
    await page.mouse.up({ button: 'right' });
    await sleep(500);
    const yaw = await page.evaluate(() => MH3D.engine.rig.yaw);
    check(Math.abs(yaw - -0.78) < 0.06, `right-drag 120 px turned the view (yaw ${yaw.toFixed(3)})`);
    check(await page.evaluate(() => document.getElementById('ctx-menu').classList.contains('hidden')), 'a drag opens no menu');
    const w = await page.evaluate(() => { MH3D.ctl.keys.add('w'); const v = MH3D.ctl.wish(); MH3D.ctl.keys.delete('w'); return [v.x, v.y]; });
    check(Math.abs(w[0] - Math.sin(-yaw)) < 0.02 && Math.abs(w[1] + Math.cos(yaw)) < 0.02, `W walks away from the turned camera (${w.map(n => n.toFixed(2))})`);
    // drag up: a higher view (tilt), kept within limits
    await page.mouse.move(box.x, box.y);
    await page.mouse.down({ button: 'right' });
    await page.mouse.move(box.x, box.y - 400, { steps: 8 });
    await page.mouse.up({ button: 'right' });
    const tilt = await page.evaluate(() => MH3D.engine.rig.tilt);
    check(tilt > 9.9 && tilt <= 10, `dragging up tilts the view, to its limit (${tilt.toFixed(1)}°)`);
    await page.screenshot({ path: path.join(OUT, 'camera-turned.png') });
    await page.keyboard.press('Home');
    await waitFor(page, () => !MH3D.engine.rig.snap, null, 30);
    const back = await page.evaluate(() => [MH3D.engine.rig.yaw, MH3D.engine.rig.tilt]);
    check(back[0] === 0 && back[1] === 0, `Home: north up again (${back})`);
  }

  if (MODE === 'menu' || MODE === 'autotarget') {
    check(await goto(18620), 'in the crypt (18620)');
    await page.evaluate(() => { for (const c of ['purge', 'mload 18610', 'mload 18610']) MH.sendCommand(c, false); });
    await sleep(1500);
    await page.evaluate(() => MH.state.mapSocket.send(JSON.stringify({ type: 'subscribe', player: MH.state.playerName, mode: 'near' })));
    const two = await waitFor(page, () => [...MH3D.ents.list.values()].filter(e => e.kind === 'mob' && e.vnum === 18620 && e.root).length >= 2, null, 60);
    check(two, 'two spectres drawn');
    const ids = await page.evaluate(() => [...MH3D.ents.list.values()].filter(e => e.kind === 'mob' && e.vnum === 18620).map(e => e.data.id));
    if (MODE === 'menu') {
      await sleep(1500);
      const at = await page.evaluate(id => {
        const e = MH3D.ents.list.get(`m${id}`), cv = MH3D.engine.renderer.domElement, r = cv.getBoundingClientRect();
        const v = e.root.position.clone().setY(e.root.position.y + 1.1).project(MH3D.engine.camera);
        return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
      }, ids[1]);
      await page.mouse.click(at.x, at.y, { button: 'right' });
      await sleep(400);
      const items = await page.evaluate(() => [...document.querySelectorAll('#ctx-menu button')].map(b => b.textContent));
      check(items.includes('Attack') && items.includes('Consider'), `right-click on a spectre: ${JSON.stringify(items)}`);
      await page.screenshot({ path: path.join(OUT, 'menu-mob.png') });
      await page.evaluate(() => { window.__sent.length = 0; });
      await page.evaluate(() => [...document.querySelectorAll('#ctx-menu button')].find(b => b.textContent === 'Consider').click());
      await sleep(300);
      const sent = await page.evaluate(() => window.__sent.slice());
      check(sent.includes(`consider #${ids[1]}`), `Consider names that exact spectre: ${JSON.stringify(sent)}`);
      // the hero
      const me = await page.evaluate(() => {
        const cv = MH3D.engine.renderer.domElement, r = cv.getBoundingClientRect(), p = MH3D.hero.root.position;
        const v = p.clone().setY(p.y + 1.1).project(MH3D.engine.camera);
        return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
      });
      await page.mouse.click(me.x, me.y, { button: 'right' });
      await sleep(400);
      const title = await page.evaluate(() => (document.querySelector('#ctx-menu .ctx-title') || {}).textContent);
      check(title === 'You', `right-click on yourself: "${title}"`);
      await page.keyboard.press('Escape');
    } else {
      const name = await page.evaluate(() => MH.state.playerName);
      await page.evaluate(() => MH3D.ents.setTarget(null));
      await page.evaluate(({ id, name }) => MH.bus.emit('combat.events', { events: [{ k: 'attack', src: { m: id }, dst: { p: name }, res: 'hit' }] }), { id: ids[0], name });
      await sleep(300);
      check(await page.evaluate(id => MH3D.ents.target === `m${id}`, ids[0]), 'a creature that hits you becomes your target');
      // you pick the other one by hand and it fights you: the first one's blows don't steal it
      await page.evaluate(id => { const e = MH3D.ents.list.get(`m${id}`); e.data.fighting = true; MH3D.ents.setTarget(e.key, { byHand: true }); }, ids[1]);
      await page.evaluate(({ id, name }) => MH.bus.emit('combat.events', { events: [{ k: 'attack', src: { m: id }, dst: { p: name }, res: 'hit' }] }), { id: ids[0], name });
      await sleep(300);
      check(await page.evaluate(id => MH3D.ents.target === `m${id}`, ids[1]), 'your chosen foe stays targeted');
    }
    await page.evaluate(() => MH.sendCommand('purge', false));
    await sleep(800);
  }

  if (MODE === 'creatures') {
    check(await goto(3001), 'in the Temple of Midgaard (3001)');
    const want = { 3068: 'slime', 5202: 'chest', 5423: 'knight still', 3602: 'knight', 3016: 'knight', 23506: 'greendemon', 6115: 'mage', 6402: 'book_single', 3014: 'rat' };
    await page.evaluate(vs => { for (const c of ['purge', ...vs.map(v => `mload ${v}`)]) MH.sendCommand(c, false); }, Object.keys(want));
    await sleep(1500);
    await page.evaluate(() => MH.state.mapSocket.send(JSON.stringify({ type: 'subscribe', player: MH.state.playerName, mode: 'near' })));
    const n = Object.keys(want).length;
    check(await waitFor(page, n => [...MH3D.ents.list.values()].filter(e => e.kind === 'mob' && e.vnum === 3001 && e.root).length >= n, n, 90), `all ${n} drawn`);
    const got = await page.evaluate(() => [...MH3D.ents.list.values()].filter(e => e.kind === 'mob' && e.vnum === 3001).map(e => {
      const l = e.look || {}, b = l.beast;
      return { pv: e.data.pv, short: e.data.short, long: e.data.long, body: b ? (b.mob || b.proc || b.prop[1]) : l.model + (l.still ? ' still' : ''), fly: e.fly, y: +e.root.position.y.toFixed(2) };
    }));
    for (const [pv, body] of Object.entries(want)) {
      const g = got.find(x => String(x.pv) === pv);
      check(g && g.body === body, `${pv} ${g ? g.short : '?'}: ${g ? g.body : 'missing'} (want ${body})`);
    }
    const book = got.find(x => x.pv === 6402);
    check(book && book.fly > 0 && book.y > 0.5, `the living book flies (${book && book.y} m)`);
    check(got.some(x => x.pv === 3014 && /rat-man/.test(x.long || '')), 'the payload carries the room line');
    // stand back from them for a picture
    await page.evaluate(() => {
      const ms = [...MH3D.ents.list.values()].filter(e => e.kind === 'mob' && e.vnum === 3001 && e.root);
      const c = ms.reduce((a, e) => a.add(e.root.position), new MH3D.THREE.Vector3()).multiplyScalar(1 / ms.length);
      MH3D.hero.root.position.set(c.x, 0, c.z + 7);
    });
    await sleep(4000);
    await page.screenshot({ path: path.join(OUT, 'creatures.png') });
    await page.evaluate(() => MH.sendCommand('purge', false));
    await sleep(800);
  }

  check(errors.length === 0, `no page errors${errors.length ? ': ' + errors.join(' / ') : ''}`);
  await browser.close();
  const bad = results.filter(r => !r[0]).length;
  console.log(bad ? `${bad} FAILED` : 'ALL OK');
  process.exit(bad ? 1 : 0);
})();
