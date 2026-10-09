// /play — the 3D client. Boots the engine, shows the login over a drifting backdrop, then
// builds the hero's zone as one continuous world and keeps it in step with the server:
// the hero walks freely and the server is told which room they entered (sync.js).
import * as THREE from 'three';
import { createEngine } from './engine.js';
import { loadKit, spawnCharacter } from './assets.js';
import { Zone, fetchZonemap, REV } from './zone.js';
import { ROOM_W, ROOM_H } from './terrain.js';
import { Controller, findPath } from './controller.js';
import { Sync } from './sync.js';
import { Entities, classModel } from './entities.js';
import { cutout } from './cutout.js';
import { attachPerf } from './perf.js';
import { buildDemo } from './demo.js';

const $ = s => document.querySelector(s);
const params = new URLSearchParams(location.search);
const pref = k => { try { return localStorage.getItem(k); } catch (_) { return null; } };
const engine = createEngine($('#stage'), { quality: params.get('q') || pref('mh3d_quality') || 'high' });
attachPerf(engine, $('#perf'));
const loaded = Promise.all(['dungeon', 'nature', 'town', 'furniture', 'graveyard'].map(k => loadKit(k)))
  .then(([dungeon, nature, town, furniture, graveyard]) => ({ dungeon, nature, town, furniture, graveyard }));

if (params.has('demo')) runDemo(); else runGame();

async function runDemo() {
  const kits = await loaded;
  if (params.get('gallery')) {
    const { showGallery, showMobGallery } = await import('./gallery.js');
    const g = params.get('gallery');
    const { showBeastGallery } = await import('./gallery.js');
    const extra = ['town', 'furniture', 'graveyard'].includes(g) ? await loadKit(g) : null;
    const at = g === 'mobs' ? await showMobGallery(engine) : g === 'beasts' ? await showBeastGallery(engine)
      : showGallery(engine, extra || (g === 'nature' ? kits.nature : kits.dungeon), Number(params.get('scale')) || 1);
    engine.rig.target.copy(at); engine.placeCamera(true);
    window.MH3D = { engine, THREE };
  } else {
    const banner = $('#banner');
    const demo = await buildDemo(engine, kits, {
      interactive: true,
      banner: name => { banner.querySelector('.room').textContent = name; banner.style.opacity = 1; setTimeout(() => { banner.style.opacity = 0; }, 2000); },
    });
    engine.onTick((dt, t) => demo.update(dt, t));
    window.MH3D = { engine, demo, THREE };
  }
  $('#login').classList.add('hidden');
  $('#loading').classList.add('done');
}

async function runGame() {
  const [{ createHud }, { createMinimap }, { setupLogin }] = await Promise.all([
    import('./hud/hud.js'), import('./hud/minimap.js'), import('./hud/login.js')]);
  const kits = await loaded;
  const hud = createHud();
  setupLogin();
  let backdrop = await buildDemo(engine, kits, { interactive: false });
  $('#loading').classList.add('done');

  const ents = new Entities(engine, $('#plates'));
  const mm = createMinimap($('#minimap'), room => travelTo(room));
  let zone = null, hero = null, ctl = null, sync = null, heroRoom = null;
  let starting = null, slide = null, hop = null, lastPayload = null, leashToast = 0, doorToast = 0;

  // ---- server events ----
  MH.bus.on('map', payload => {
    lastPayload = payload;
    if (payload.player) hud.setPlayer(payload.player);
    if (!payload.player || !payload.player.vnum) return;
    if (!zone) { if (!starting) starting = start(payload).catch(err => { console.error(err); hud.toast('Could not load the world: ' + err.message); }).finally(() => { starting = null; }); return; }
    if (starting) return;
    ents.sync(payload, MH.state.playerName);
    mm.setExplored((payload.rooms || []).map(r => r.vnum));
    mm.setTime(payload.time);
    sync.onMap(payload);
  });
  MH.bus.on('combat.update', p => {
    if (MH.state.player) hud.setPlayer(MH.state.player);
    ents.combat(p);
    const t = ents.targeted;
    if (t) hud.setTarget({ kind: t.kind, ...t.data });
    // each round: the hero swings at whoever they fight
    if (hero && p.in_combat !== false && MH.state.inCombat) {
      const foe = t && t.root && t.vnum === (heroRoom && heroRoom.vnum) ? t : null;
      if (foe) ctl.face(foe.root.position.x, foe.root.position.z);
      ctl.swing(['1H_Melee_Attack_Chop', '1H_Melee_Attack_Slice_Diagonal', '1H_Melee_Attack_Stab'][Math.floor(Math.random() * 3)]);
    }
  });
  MH.bus.on('move.result', res => { if (sync) sync.onResult(res); });
  MH.bus.on('target.set', t => hud.setTarget(t));
  MH.bus.on('target.clear', () => hud.setTarget(null));

  // ---- start: the first map payload after login ----
  async function start(payload) {
    const v = payload.player.vnum;
    const zm = await fetchZonemap(`vnum=${v}`);
    if (backdrop) { backdrop.dispose(); backdrop = null; }
    enterZone(zm);
    const room = zone.rooms.get(v);
    const look = classModel(payload.player.char_class);
    hero = await spawnCharacter(look.model, { tint: look.tint });
    engine.scene.add(hero.root);
    ctl = new Controller(engine, hero, blockedFor);
    sync = new Sync({
      heroRoomVnum: () => heroRoom && heroRoom.vnum,
      confirmed: v2 => onConfirmed(v2),
      refused: res => onRefused(res),
      relocate: v2 => relocate(v2),
    });
    sync.start(v);
    zone.prebuild(room, 1);
    placeHero(room, zone.centre(room));
    engine.rig.target.copy(hero.root.position);
    engine.placeCamera(true);
    hud.showGame(true);
    hud.banner(room.name, zone.name);
    ents.sync(payload, MH.state.playerName);
    mm.setExplored((payload.rooms || []).map(r => r.vnum));
    mm.setTime(payload.time);
    window.MH3D = { engine, zone: () => zone, hero, ctl, sync, ents, THREE };
  }

  function enterZone(zm) {
    if (zone) zone.dispose();
    zone = new Zone(engine, kits, zm);
    ents.setZone(zone);
    mm.setZone(zone);
  }

  // hero's body is blocked by walls, and by any crossing into another room that is not an
  // open exit — or any crossing at all while fighting (the server would refuse it)
  function blockedFor(x, z, fx, fz) {
    const from = zone.roomAt(fx, fz);
    const to = zone.roomAt(x, z);
    if (from && to !== from && MH.state.inCombat) {
      if (performance.now() - leashToast > 2500) { leashToast = performance.now(); hud.toast("You're fighting! Flee to escape."); }
      return true;
    }
    return zone.blocked(x, z, from);
  }

  function placeHero(room, pos) {
    hero.root.position.set(pos.x, 0, pos.z);
    setHeroRoom(room);
  }
  function setHeroRoom(room) {
    heroRoom = room;
    mm.setRoom(room);
    const L = zone.layoutOf(room);
    const hour = lastPayload && lastPayload.time ? lastPayload.time.hour : 12;
    const dark = L.dark || L.theme === 'dungeon' || L.theme === 'cave';
    const mood = dark ? 'crypt' : L.theme === 'inside' ? 'interior'
      : (hour >= 20 || hour < 5) ? 'night' : (hour >= 18 || hour < 7) ? 'dusk' : L.theme === 'forest' ? 'forest' : 'day';
    engine.setMood(mood);
  }

  // ---- walking between rooms ----
  function heroWalkedInto(from, to) {
    setHeroRoom(to);
    sync.walked(from.vnum, to.vnum);
    hud.banner(to.name, '');
  }
  function onConfirmed(v) {
    if (hop && hop.to === v) finishHop(v);
  }
  function onRefused(res) {
    hud.toast(res.reason || "You can't go that way.");
    if (hop) {
      const h = hop; hop = null;
      $('#vignette').style.background = '';
      if (heroRoom && heroRoom.vnum === res.room) {
        slide = { from: hero.root.position.clone(), to: zone.entry(heroRoom, h.dir), t: 0, room: heroRoom };
        return;
      }
    }
    const back = zone.rooms.get(res.room);
    if (!back) return relocate(res.room);
    // slide back through the shared opening into the room the server kept us in
    const d = heroRoom && zone.openDir(back, heroRoom);
    const target = d ? zone.entry(back, d) : zone.centre(back);
    slide = { from: hero.root.position.clone(), to: target, t: 0, room: back };
    ctl.stop();
  }
  async function relocate(v) {
    const room = zone.rooms.get(v);
    if (room) {
      const d = heroRoom && zone.openDir(heroRoom, room);
      if (d) { slide = { from: hero.root.position.clone(), to: zone.entry(room, REV[d]), t: 0, room }; return; }
      return teleport(room, zone.centre(room));
    }
    // another zone: load it, arrive by the exit that leads back where we were
    const oldV = heroRoom && heroRoom.vnum;
    const zm = await fetchZonemap(`vnum=${v}`);
    enterZone(zm);
    const r = zone.rooms.get(v);
    let at = zone.centre(r);
    for (const [d, e] of Object.entries(r.data.exits)) if (e.to === oldV) { at = REV[d] ? zone.entry(r, d) : at; break; }
    teleport(r, at);
    hud.banner(r.name, zone.name);
    if (lastPayload) ents.sync(lastPayload, MH.state.playerName);
  }
  function teleport(room, pos) {
    zone.prebuild(room, 1);
    placeHero(room, pos);
    ctl.stop();
    engine.rig.target.copy(hero.root.position);
    engine.placeCamera(true);
    flashDip();
  }
  function flashDip() {
    const v = $('#vignette');
    v.style.transition = 'none'; v.style.background = 'rgba(4,4,8,.85)';
    requestAnimationFrame(() => { v.style.transition = 'background .45s'; v.style.background = ''; });
  }

  // ---- passages: exits that hop (misaligned rooms, stairs, portals, zone borders) ----
  function startHop(ps) {
    hop = { from: heroRoom, dir: ps.dir, to: ps.exit.to, kind: ps.exit.kind, at: performance.now() };
    ctl.stop();
    sync.walked(heroRoom.vnum, ps.exit.to);
    const v = $('#vignette');
    v.style.transition = 'background .25s'; v.style.background = 'rgba(4,4,8,.7)';
  }
  async function finishHop(v) {
    const h = hop; hop = null;
    if (h.kind === 'zone' || !zone.rooms.get(v)) {
      const zm = await fetchZonemap(`vnum=${v}`);
      enterZone(zm);
      const r = zone.rooms.get(v);
      let at = zone.centre(r);
      for (const [d, e] of Object.entries(r.data.exits)) if (e.to === h.from.vnum && REV[d]) { at = zone.entry(r, d); break; }
      teleport(r, at);
      hud.banner(r.name, zone.name);
      if (lastPayload) ents.sync(lastPayload, MH.state.playerName);
      return;
    }
    const r = zone.rooms.get(v);
    teleport(r, zone.arrival(r, h.from, h.dir));
    hud.banner(r.name, '');
  }

  // ---- travel: click a room on the minimap ----
  function travelTo(room) {
    if (!heroRoom || room === heroRoom) return;
    const path = zone.roomPath(heroRoom, room);
    if (!path) return hud.toast('No open path there from here.');
    // through the middle of each room and each shared opening (roomgen keeps those lanes clear)
    const pts = [];
    for (let i = 0; i < path.length; i++) {
      const r = path[i];
      if (i > 0) {
        const d = zone.openDir(path[i - 1], r);
        pts.push(zone.entry(path[i - 1], d), zone.entry(r, REV[d]));
      }
      if (i === path.length - 1 || i > 0) pts.push(zone.centre(r));
    }
    const p0 = hero.root.position;
    const lead = pts.length ? findPath(p0.x, p0.z, pts[0].x, pts[0].z, (ax, az, bx, bz) => !blockedFor(bx + 0.5, bz + 0.5, ax + 0.5, az + 0.5)) || [] : [];
    ctl.follow((lead.length ? lead : pts.slice(0, 1)).concat(pts.slice(1)).map(p => ({ x: p.x, z: p.z })));
  }

  // ---- targeting and actions ----
  const canvas = engine.renderer.domElement;
  canvas.addEventListener('pointerdown', e => {
    if (e.button !== 0 || !ctl) return;
    const hit = ents.pick(e.clientX, e.clientY);
    if (hit) { ents.setTarget(hit.key); return; }
    const g = ctl.groundAt(e.clientX, e.clientY);
    if (g) ctl.walkTo(g.x, g.z);
  });
  canvas.addEventListener('dblclick', e => {
    const hit = ents.pick(e.clientX, e.clientY);
    if (hit && hit.kind === 'mob') { ents.setTarget(hit.key); attack(); }
  });
  canvas.addEventListener('contextmenu', e => e.preventDefault());
  MH.bus.on('hud.untarget', () => ents.setTarget(null));
  MH.bus.on('hud.cycleTarget', () => {
    if (!hero) return;
    const p = hero.root.position;
    const list = [...ents.list.values()].filter(e => e.kind === 'mob' && e.root && e.root.position.distanceTo(p) < 22)
      .sort((a, b) => (b.data.hostile - a.data.hostile) || a.root.position.distanceTo(p) - b.root.position.distanceTo(p));
    if (!list.length) return hud.toast('Nothing nearby to target.');
    const i = list.findIndex(e => e.key === ents.target);
    ents.setTarget(list[(i + 1) % list.length].key);
  });
  const keyword = t => MH.mobKeyword(t.data.name);
  // the server fights within one room: walk into the target's room first, then strike
  function inReach(t, then) {
    if (heroRoom && t.vnum === heroRoom.vnum && hero.root.position.distanceTo(t.root.position) < 3.2) return then();
    ctl.walkTo(t.root.position.x, t.root.position.z, () => { if (heroRoom && t.vnum === heroRoom.vnum) then(); });
  }
  function attack() {
    const t = ents.targeted;
    if (!t || !t.root) return hud.toast('No target — click a creature or press Tab.');
    if (t.kind !== 'mob') return hud.toast('You cannot attack that.');
    inReach(t, () => {
      ctl.face(t.root.position.x, t.root.position.z);
      ctl.swing();
      if (!MH.state.inCombat) MH.sendCommand(`kill ${keyword(t)}`);
    });
  }
  MH.bus.on('hud.attack', attack);
  MH.bus.on('hud.flee', () => MH.sendCommand('flee'));
  MH.bus.on('hud.ability', ab => {
    const t = ents.targeted;
    const name = ab.id.replace(/_/g, ' ');
    const base = ab.spell ? `cast '${name}'` : name;
    if (ab.self || !t || t.kind !== 'mob') {
      if (!ab.self && !t) return hud.toast('No target — click a creature or press Tab.');
      ctl.swing(ab.spell ? 'Spellcast_Shoot' : '1H_Melee_Attack_Stab');
      return MH.sendCommand(base);
    }
    inReach(t, () => {
      ctl.face(t.root.position.x, t.root.position.z);
      ctl.swing(ab.spell ? 'Spellcast_Shoot' : '1H_Melee_Attack_Stab');
      MH.sendCommand(`${base} ${keyword(t)}`);
    });
  });
  // doors: E opens the nearest closed door of this room
  window.addEventListener('keydown', e => {
    if (!hero || e.repeat || /INPUT|TEXTAREA/.test(e.target.tagName)) return;
    if (e.key.toLowerCase() !== 'e') return;
    const d = nearestDoor(3.5);
    if (d) MH.sendCommand(`open ${d.dir}`);
  });
  function nearestDoor(maxDist) {
    if (!heroRoom) return null;
    const p = hero.root.position, L = zone.layoutOf(heroRoom);
    let best = null;
    for (const [dir, info] of Object.entries(heroRoom.doors)) {
      const g = L.gaps[dir];
      if (!g || !info.closed) continue;
      const x = heroRoom.ox + (dir === 'east' ? ROOM_W : dir === 'west' ? 0 : (g.x0 + g.x1 + 1) / 2);
      const z = heroRoom.oz + (dir === 'south' ? ROOM_H : dir === 'north' ? 0 : (g.y0 + g.y1 + 1) / 2);
      const dist = Math.hypot(p.x - x, p.z - z);
      if (dist < maxDist && (!best || dist < best.dist)) best = { dir, dist };
    }
    return best;
  }

  // ---- the frame ----
  engine.onTick((dt, t) => {
    if (!hero) { if (backdrop) backdrop.update(dt, t); return; }
    if (slide) {
      slide.t = Math.min(1, slide.t + dt / 0.3);
      const k = 1 - Math.pow(1 - slide.t, 3);
      hero.root.position.lerpVectors(slide.from, slide.to, k);
      if (slide.t >= 1) { setHeroRoom(slide.room); slide = null; }
    } else if (!hop) {
      ctl.update(dt);
    }
    const p = hero.root.position;
    engine.rig.target.set(p.x, 0, p.z);
    cutout.update(engine.camera, p);
    zone.update(dt, t, p, ctl.vel);
    hero.update(dt);
    if (!slide && !hop) {
      const r = zone.roomAt(p.x, p.z);
      if (r && heroRoom && r !== heroRoom) heroWalkedInto(heroRoom, r);
      const ps = heroRoom && zone.passageAt(heroRoom, p, ctl.vel);
      if (ps) startHop(ps);
      else if (ctl.vel.lengthSq() > 1 && nearestDoor(1.4) && performance.now() - doorToast > 4000) {
        doorToast = performance.now();
        hud.toast('The way is shut — press E to open it.');
      }
    }
    if (hop && performance.now() - hop.at > 6000) { hop = null; $('#vignette').style.background = ''; }
    ents.update(dt, t, p);
    mm.update(p, ctl.yaw);
    sync.tick();
  });
}
