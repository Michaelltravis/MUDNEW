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
import { FX } from './fx.js';
import { CombatView } from './combat.js';
import { CombatCues } from './combatcues.js';
import { createBubbles } from './hud/bubbles.js';
import { PassageGate, HOP_TIMEOUT_MS } from './passages.js';
import { doorPrompt, doorVerbs, doorAnchor, cap } from './doorlogic.js';
import { createPrompt } from './hud/prompt.js';
import { createCastbar } from './hud/castbar.js';
import { createContextMenu } from './hud/contextmenu.js';
import { attachWorldInput } from './input.js';
import { isHostile, shouldRetarget, retargetOnDeath, refFor, abilityCommand } from './targeting.js';
import { verbsFor } from './hud/verbs.js';
import { attachPerf } from './perf.js';
import { buildDemo } from './demo.js';
import { sound } from './audio.js';
import { ActionClock } from './actionclock.js';
import { musicFor, bedFor, surfaceFor } from './soundtable.js';
import { interiorKind } from './terrain-town.js';

const $ = s => document.querySelector(s);
const WATER_TILE = 4;   // zone.js / terrain.js tile kinds
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
    const { showBeastGallery, showAbilityGallery, showIconGallery, showSoundGallery } = await import('./gallery.js');
    const extra = ['town', 'furniture', 'graveyard'].includes(g) ? await loadKit(g) : null;
    const at = g === 'mobs' ? await showMobGallery(engine) : g === 'beasts' ? await showBeastGallery(engine, kits)
      : g === 'abilities' ? await showAbilityGallery(engine)
      : g === 'icons' ? (await showIconGallery()) || new THREE.Vector3()
      : g === 'sounds' ? (await showSoundGallery()) || new THREE.Vector3()
      : showGallery(engine, extra || (g === 'nature' ? kits.nature : kits.dungeon), Number(params.get('scale')) || 1);
    engine.rig.target.copy(at); engine.placeCamera(true);
    window.MH3D = { engine, THREE, gallery: window.MH3D_gallery };
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

  // ranges and round timing, one source of truth on the server (combat_range.py)
  let ranges = { melee: 2.5, auto: {}, abilities: {}, spellDefault: 14 };
  // real-time combat (action_combat.py): your swing clock and the global cooldown, as the
  // server last told them (Settings -> Real-time combat; off: the 3-s round)
  const clock = MH.actionClock = new ActionClock();
  const actionMode = () => MH.combatMode === 'action' && !(ranges.action && ranges.action.on === false);
  fetch('/combatdata').then(r => r.json()).then(d => { ranges = d; hud.setRanges(d); clock.configure(d.action); }).catch(() => {});
  const myClass = () => String(MH.state.player && MH.state.player.char_class || '').toLowerCase();
  const reachOf = () => (ranges.auto[myClass()] || { range: ranges.melee || 2.5 }).range;
  const ents = new Entities(engine, $('#plates'), kits);
  const fx = new FX(engine, $('#fct'));
  const combat = new CombatView({
    engine, fx, ents,
    getHero: () => hero && { actor: hero, ctl, cls: (MH.state.player && MH.state.player.char_class || '').toLowerCase() },
    heroName: () => MH.state.playerName,
    onOutOfRange: e => outOfRange(e),
    onWound: ent => { if (ents.targeted === ent) hud.setTarget({ kind: ent.kind, ...ent.data }); },
    onAggro: id => aggro(id),
  });
  // fights made easy to read: a ring under your target, your reach while you hover an
  // ability, STEP OUT under a marked blow, STRIKE NOW at a staggered foe
  const cues = new CombatCues({ engine, ents, getHero: () => hero && { actor: hero, ctl }, callout: $('#callout'),
    rangeOf: id => { const r = rangeOf(id, (hud.player && (hud.player.spells || {})[id] != null)); return r || null; },
    onStrike: () => hud.suggestStrike() });
  // sound (audio.js): heard from where the camera looks, turned with it
  combat.onSound = (name, at, opts) => sound.play(name, { at, ...(opts || {}) });
  sound.listener = () => ({ x: engine.rig.target.x, z: engine.rig.target.z, yaw: engine.rig.yaw });
  MH.bus.on('combat.state', on => sound.setBattle(!!on));
  combat.onTelegraph = (k, d) => cues.telegraph(k, d);
  // stepping out of a marked blow's ground: the server hears where you stand at once
  cues.onLeave = () => { posClock = 0; };
  combat.onTelegraphEnd = k => cues.telegraphEnd(k);
  combat.onOpening = src => cues.opening(src);
  MH.bus.on('hud.abilityHover', a => cues.hoverAbility(a && a.id));
  // speech over the speaker's head: "Sage Aldric says, '...'" (NPCs, other players, you)
  const bubbles = createBubbles($('#plates'), engine);
  engine.onLateTick(() => { if (hero) bubbles.update(); });
  MH.bus.on('terminal.output', ({ html, text }) => {
    if (!hero || !MH.state.isLoggedIn) return;
    const plain = String(text || html || '').replace(/<[^>]+>/g, '').replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&');
    for (const line of plain.split(/\r?\n/)) {
      const m = /^\s*(.+?) (?:says?|exclaims?|asks?|whispers?|sings?)(?: to you)?,? ['"\u2018\u201c](.+?)['"\u2019\u201d]\s*$/.exec(line);
      if (!m) continue;
      const who = m[1].trim().toLowerCase(), words = m[2].trim();
      if (who === 'you') { bubbles.say(hero.root, words, { npc: false }); continue; }
      const e = [...ents.list.values()].find(x => x.root && x.data && String(x.data.name || '').toLowerCase() === who)
        || [...ents.list.values()].find(x => x.root && x.data && who.includes(String(x.data.name || '~').toLowerCase()));
      if (e) bubbles.say(e.root, words, { npc: e.kind !== 'player', lift: (e.plateY || 2.2) + 0.55 });
    }
  });
  engine.onTick((dt, t) => { if (hero) cues.update(dt, t); });
  MH.bus.on('combat.events', p => {
    // the server's word on your swing clock (private to you)
    for (const e of p.events || []) if (e.k === 'swing' && combat.isHero(e.src)) clock.told(e, performance.now());
    if (hero) combat.handle(p.events, p.room);
    for (const e of p.events || []) if (e.k === 'death' && e.dst && e.dst.p && combat.isHero(e.dst)) hud.fallen();
    // the target's wind-up shows on the target frame as a cast bar
    const t = ents.targeted;
    if (!t || t.kind !== 'mob') return;
    for (const e of p.events || []) {
      if (!e.src || e.src.m !== t.data.id) continue;
      if (e.k === 'windup') hud.targetCast({ label: e.label, ms: e.ms });
      else if (e.k === 'resolve') hud.targetCast({ end: 'landed' });
      else if (e.k === 'cancel' && e.reason !== 'death') hud.targetCast({ end: 'broken' });
    }
  });
  // your group: frames, the invite popup, loot rolls; click a member to target them (heals and
  // blessings go to your target), right-click for more
  MH.bus.on('group.update', e => hud.party.update(e && e.group));
  MH.bus.on('group.invite', e => hud.party.showInvite(e));
  MH.bus.on('loot.roll', r => hud.party.lootRoll(r));
  MH.bus.on('loot.result', r => hud.party.lootResult(r));
  // the marquee quest: an offer, a group member's embarking, its stages, the reward
  MH.bus.on('quest.offer', e => { sound.play('ui_offer'); hud.quest.offer(e.quest); });
  MH.bus.on('quest.embark', e => hud.quest.showEmbark(e));
  MH.bus.on('quest.stage', e => { sound.play('quest_stage'); hud.quest.stage(e); });
  MH.bus.on('quest.done', e => { sound.play('quest_done'); hud.quest.done(e); });
  MH.bus.on('ability.improve', () => sound.play('improve'));
  MH.bus.on('quest.mark', vnum => mm.setQuestMark(vnum == null ? null : vnum));
  // a level gained: a column of light on the hero, stars thrown up around them
  MH.bus.on('hud.levelup', () => {
    sound.play('levelup');
    if (!hero) return;
    const p = hero.root.position;
    fx.pillar(p, { school: 'holy', radius: 1.3, height: 10, time: 1.6 });
    fx.shockwave(p, { color: 0xffd86a, radius: 6, time: 0.9 });
    fx.glyph(p.clone().setY(1), { glyph: 'star', count: 34, color: 0xffe8a0, speed: 4, up: 3, life: 1.5, size: 0.5, gravity: 2, spin: 4 });
    fx.light(p.clone().setY(2), 0xffe0a0, 8, 1.2);
  });
  MH.bus.on('hud.targetPlayer', name => {
    const e = ents.list.get(`p${name}`);
    if (e) ents.setTarget(e.key, { byHand: true });
    else hud.toast(`${name} isn't in sight`);
  });
  MH.bus.on('hud.partyMenu', ({ name, x, y, leader }) => ctxMenu.show(x, y, name, [
    { label: 'Target', run: () => MH.bus.emit('hud.targetPlayer', name) },
    { label: 'Whisper…', run: () => hud.whisper(name) },
    { label: 'Follow', run: () => MH.sendCommand(`follow ${name}`) },
    ...(leader ? [{ label: 'Make leader', run: () => MH.sendCommand(`group leader ${name}`) },
      { label: 'Remove from group', run: () => MH.sendCommand(`group kick ${name}`) }] : []),
    { label: 'Leave group', run: () => MH.sendCommand('group leave') },
  ]));
  // other players: where they walk (relayed ~5x a second) and when they change rooms
  MH.bus.on('player.presence', p => ents.presence(p));
  MH.bus.on('player.move', p => { if (p && p.name && p.name !== MH.state.playerName) ents.playerMoved(p); });
  // another login took this character over: say so, then back to the login screen
  MH.bus.on('session.revoked', () => {
    hud.toast('This character was just logged in somewhere else.');
    setTimeout(() => location.reload(), 2600);
  });
  // creatures that take the stairs or a far passage leave and arrive in a puff of dust
  ents.onSnap = (from, to) => {
    for (const q of [from, to]) fx.p.emit(q.clone().setY(0.4), { count: 18, color: 0xd8d0c0, speed: 1.6, up: 0.6, life: 0.7, size: 0.4, grow: 0.5, drag: 1.5 });
  };
  const mmSmall = createMinimap($('#minimap'), room => travelTo(room), () => engine.snapNorth());
  // the big map (M): the same drawing, larger — the whole zone at a glance, click to walk there
  const bigEl = $('#bigmap');
  const mmBig = createMinimap(bigEl, room => { bigEl.classList.add('hidden'); travelTo(room); }, null, { cell: 1.7 });
  bigEl.querySelector('.bm-close').addEventListener('click', () => bigEl.classList.add('hidden'));
  MH.bus.on('hud.map', on => {
    const show = on === undefined || on === null ? bigEl.classList.contains('hidden') : !!on;
    bigEl.classList.toggle('hidden', !show);
    if (show) mmBig.redraw();
  });
  const mm = {
    setZone: z => { mmSmall.setZone(z); mmBig.setZone(z); },
    setExplored: l => { mmSmall.setExplored(l); mmBig.setExplored(l); },
    setGuild: g => { mmSmall.setGuild(g); mmBig.setGuild(g); },
    setQuestMark: v => { mmSmall.setQuestMark(v); mmBig.setQuestMark(v); },
    setRoom: r => { mmSmall.setRoom(r); mmBig.setRoom(r); },
    setTime: t => { mmSmall.setTime(t); mmBig.setTime(t); },
    update: (p, yaw, cam) => { mmSmall.update(p, yaw, cam); if (!bigEl.classList.contains('hidden')) mmBig.update(p, yaw, cam); },
  };
  const prompt = createPrompt($('#prompt'));
  const castbar = createCastbar($('#castbar'));
  const ctxMenu = createContextMenu($('#ctx-menu'));
  let zone = null, hero = null, ctl = null, sync = null, heroRoom = null;
  let starting = null, slide = null, hop = null, lastPayload = null, leashToast = 0, doorToast = 0;
  // stairs and other passages: a gate keeps the ones you arrived beside quiet until you mean
  // them (passages.js); `climb` is the short step onto or off the stairs around a hop
  const gate = new PassageGate();
  let heroSpots = [], lastActive = 0, climb = null, travel = null, relocating = null;
  let stepSurface = 'step_dirt', stride = 0;   // footsteps: what is underfoot, distance since the last

  // ---- server events ----
  MH.bus.on('map', payload => {
    lastPayload = payload;
    if (payload.player) { hud.setPlayer(payload.player); ents.heroLevel = payload.player.level || 1; }
    if ('group' in payload) hud.party.update(payload.group);
    if (payload.player && 'quest' in payload.player) hud.quest.update(payload.player.quest);
    if (!payload.player || !payload.player.vnum) return;
    if (!zone) { if (!starting) starting = start(payload).catch(err => { console.error(err); hud.toast('Could not load the world: ' + err.message); }).finally(() => { starting = null; }); return; }
    if (starting) return;
    ents.sync(payload, MH.state.playerName);
    applyPendingAggro();
    mm.setExplored((payload.rooms || []).map(r => r.vnum));
    mm.setTime(payload.time);
    mm.setGuild(payload.player.guild);
    sync.onMap(payload);
  });
  MH.bus.on('combat.update', p => {
    if (p && 'group' in p) hud.party.update(p.group);
    if (MH.state.player) hud.setPlayer(MH.state.player);
    ents.combat(p);
    const t = ents.targeted;
    if (t) hud.setTarget({ kind: t.kind, ...t.data });
    // (swings, hits and casts are drawn from the server's combat events: combat.js)
  });
  MH.bus.on('move.result', res => { if (sync) sync.onResult(res); });
  MH.bus.on('target.set', t => hud.setTarget(t));
  MH.bus.on('target.clear', () => hud.setTarget(null));

  // ---- start: the first map payload after login ----
  async function start(payload) {
    const v = payload.player.vnum;
    const zm = await fetchZonemap(`vnum=${v}`);
    if (backdrop) { backdrop.dispose(); backdrop = null; }
    engine.rig.yaw = 0;          // the title screen's drift ends: play starts north up
    enterZone(zm);
    const room = zone.rooms.get(v);
    const look = classModel(payload.player.char_class);
    hero = await spawnCharacter(look.model, { tint: look.tint });
    engine.scene.add(hero.root);
    ctl = new Controller(engine, hero, blockedFor);
    ctl.avoidDefault = avoidStairs();
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
    window.MH3D = { engine, zone: () => zone, hero, ctl, sync, ents, fx, combat, hud, cues, THREE, sound,
      heroRoom: () => heroRoom, hop: () => hop, gate, lastPayload: () => lastPayload,
      // for probes: walk onto a passage of this room on purpose (what clicking it does)
      walkToPassage: dir => { const sp = zone.passageWorld(heroRoom, dir); ctl.walkTo(sp.x, sp.z, null, { goal: { room: heroRoom.vnum, dir }, avoid: null }); } };
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
    const changed = heroRoom !== room;
    heroRoom = room;
    mm.setRoom(room);
    if (changed) {
      heroSpots = zone.passageSpots(room);
      const p = hero.root.position;
      gate.enterRoom(heroSpots, { x: p.x - room.ox, z: p.z - room.oz });
    }
    const L = zone.layoutOf(room);
    const look = { theme: L.theme, zoneKey: L.zoneKey, dark: L.dark, snowy: L.snowy, icy: L.icy,
      interior: L.theme === 'inside' ? interiorKind(L) : null };
    sound.setZoneMusic(musicFor(look));
    sound.ambience(bedFor(look));
    stepSurface = surfaceFor(look);
    const hour = lastPayload && lastPayload.time ? lastPayload.time.hour : 12;
    const dark = L.dark || L.theme === 'dungeon' || L.theme === 'cave';
    const mood = dark ? 'crypt' : L.theme === 'inside' ? 'interior'
      : (hour >= 20 || hour < 5) ? 'night' : (hour >= 18 || hour < 7) ? 'dusk' : L.theme === 'forest' ? 'forest' : 'day';
    engine.setMood(mood);
  }

  // ---- walking between rooms ----
  function heroWalkedInto(from, to) {
    setHeroRoom(to);
    sync.walked(from.vnum, to.vnum, zone.openDir(from, to));
    hud.banner(to.name, '');
  }
  function onConfirmed(v) {
    if (hop && hop.to === v && !hop.loading) finishHop(v);
  }
  function onRefused(res) {
    // an empty reason is the server saying "you are not where you think": just resync
    if (res.reason) hud.toast(res.reason);
    if (hop) {
      const h = hop; hop = null; climb = null;
      $('#vignette').style.background = '';
      if (heroRoom && heroRoom.vnum === res.room) {
        // step back off the stairs you tried (beside them, not across the room)
        slide = { from: hero.root.position.clone(), to: zone.side(heroRoom, h.dir), t: 0, room: heroRoom };
        gate.disarm(h.dir);
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
  // a room change the client did not ask for (flee, recall, goto, a portal, following a
  // leader): the server's room wins. One at a time: a second request waits for the first.
  async function relocate(v) {
    if (hop && hop.to === v) return;          // our own hop is already taking us there
    if (relocating) { relocating.next = v; return; }
    relocating = { next: null };
    try {
      const room = zone.rooms.get(v);
      const oldV = heroRoom && heroRoom.vnum;
      if (room) {
        const d = heroRoom && zone.openDir(heroRoom, room);
        if (d) { slide = { from: hero.root.position.clone(), to: zone.entry(room, REV[d]), t: 0, room }; return; }
        return teleport(room, oldV != null ? zone.arrival(room, oldV, null) : zone.centre(room));
      }
      // another zone: load it, arrive by the exit that leads back where we were
      const zm = await fetchZonemap(`vnum=${v}`);
      enterZone(zm);
      const r = zone.rooms.get(v);
      teleport(r, oldV != null ? zone.arrival(r, oldV, null) : zone.centre(r));
      hud.banner(r.name, zone.name);
      if (lastPayload) ents.sync(lastPayload, MH.state.playerName);
    } finally {
      const next = relocating && relocating.next;
      relocating = null;
      if (next != null && (!heroRoom || next !== heroRoom.vnum)) relocate(next);
    }
  }
  function teleport(room, pos) {
    sound.play('teleport');
    zone.prebuild(room, 1);
    placeHero(room, pos);
    ctl.halt();
    engine.rig.target.copy(hero.root.position);
    engine.placeCamera(true);
    flashDip();
    gate.landed(performance.now());
  }
  function flashDip() {
    const v = $('#vignette');
    v.style.transition = 'none'; v.style.background = 'rgba(4,4,8,.85)';
    requestAnimationFrame(() => { v.style.transition = 'background .45s'; v.style.background = ''; });
  }

  // ---- passages: exits that hop (misaligned rooms, stairs, portals, zone borders) ----
  // The hop stays in flight until the arrival is applied (including loading another zone),
  // so the frame loop can never send the same move twice.
  function startHop(ps) {
    const spot = zone.passageWorld(heroRoom, ps.dir);
    const stairs = ps.dir === 'up' || ps.dir === 'down';
    hop = { from: heroRoom, dir: ps.dir, to: ps.exit.to, kind: ps.exit.kind, at: performance.now() };
    ctl.halt();
    sound.play(stairs ? stepSurface : 'hop');
    sync.walked(heroRoom.vnum, ps.exit.to, ps.dir);
    // step onto the stairs (a little up, or down into the stairwell) while the screen dims
    climb = { from: hero.root.position.clone(), to: spot.setY(stairs ? (ps.dir === 'up' ? 0.5 : -0.6) : 0), t: 0, dur: 0.35 };
    const v = $('#vignette');
    v.style.transition = 'background .25s'; v.style.background = 'rgba(4,4,8,.9)';
  }
  async function finishHop(v) {
    const h = hop;
    if (!h) return;
    h.loading = true;
    try {
      if (h.kind === 'zone' || !zone.rooms.get(v)) {
        let zm = null;
        try { zm = await fetchZonemap(`vnum=${v}`); } catch (_) {
          try { zm = await fetchZonemap(`vnum=${v}`); } catch (err) { zm = null; }
        }
        if (!zm) { hop = null; climb = null; return relocate(v); }
        enterZone(zm);
        const r = zone.rooms.get(v);
        land(r, zone.arrival(r, h.from.vnum, h.dir), h.from.vnum);
        hud.banner(r.name, zone.name);
        if (lastPayload) ents.sync(lastPayload, MH.state.playerName);
      } else {
        const r = zone.rooms.get(v);
        land(r, zone.arrival(r, h.from.vnum, h.dir), h.from.vnum);
        hud.banner(r.name, '');
      }
    } finally {
      if (hop === h) hop = null;
    }
    // minimap travel goes on across the stairs
    if (travel && heroRoom !== travel.target) setTimeout(() => { if (travel) travelTo(travel.target, travel.hops + 1); }, 60);
    else travel = null;
  }
  // arrive: appear on the passage that leads back, then step off it to the arrival point
  function land(room, at, fromVnum) {
    zone.prebuild(room, 1);
    const side = Object.keys(room.data.exits).find(d => room.data.exits[d].to === fromVnum && room.data.exits[d].kind !== 'open');
    const from = side ? zone.passageWorld(room, side) : at.clone();
    placeHero(room, at);
    ctl.halt();
    engine.rig.target.copy(at);
    engine.placeCamera(true);
    climb = { from: from.setY(side === 'up' ? 0.5 : side === 'down' ? -0.6 : 0), to: at.clone(), t: 0, dur: 0.3 };
    hero.root.position.copy(climb.from);
    flashDip();
    gate.landed(performance.now());
  }

  // ---- travel: click a room on the minimap ----
  // Walk through shared openings to the first passage on the way (stairs, a misaligned
  // doorway), take it on purpose, then plan again from the other side (up to 8 hops).
  function travelTo(room, hops = 0) {
    if (!heroRoom || room === heroRoom || hops > 8) { travel = null; return; }
    const path = zone.roomPath(heroRoom, room, { passages: true });
    if (!path) { travel = null; return hud.toast('No open path there from here.'); }
    const pts = [];
    let goal = null;
    for (let i = 1; i < path.length; i++) {
      const a = path[i - 1], b = path[i];
      const d = zone.openDir(a, b);
      if (d) {
        pts.push(zone.entry(a, d), zone.entry(b, REV[d]));
        if (i === path.length - 1) pts.push(zone.centre(b));
        continue;
      }
      goal = { room: a.vnum, dir: zone.linkDir(a, b) };
      pts.push(zone.passageWorld(a, goal.dir));
      break;
    }
    travel = goal ? { target: room, hops } : null;
    const p0 = hero.root.position;
    const gx = pts.length ? Math.floor(pts[0].x) : 0, gz = pts.length ? Math.floor(pts[0].z) : 0;
    const avoid = avoidStairs();
    const lead = pts.length ? findPath(p0.x, p0.z, pts[0].x, pts[0].z, (ax, az, bx, bz) =>
      !blockedFor(bx + 0.5, bz + 0.5, ax + 0.5, az + 0.5) && !((bx !== gx || bz !== gz) && avoid(bx, bz))) || [] : [];
    ctl.follow((lead.length ? lead : pts.slice(0, 1)).concat(pts.slice(1)).map(p => ({ x: p.x, z: p.z })), null, { goal });
  }
  // stairs and portal tiles: paths go around them unless they are where you are going
  function avoidStairs() {
    return (tx, tz) => {
      const r = zone && zone.roomAt(tx + 0.5, tz + 0.5);
      return !!r && zone.avoidTile(r, tx - r.ox, tz - r.oz);
    };
  }
  // the passage whose stairs or portal tile is at a world point, if any
  function passageUnder(x, z) {
    const r = zone.roomAt(x, z);
    if (!r || r !== heroRoom) return null;
    for (const s of heroSpots) if (Math.hypot(x - (r.ox + s.x), z - (r.oz + s.z)) < 0.8) return s.key;
    return null;
  }

  // ---- targeting and actions ----
  const canvas = engine.renderer.domElement;
  canvas.addEventListener('pointerdown', e => {
    if (e.button !== 0 || e.ctrlKey || !ctl) return;
    const hit = ents.pick(e.clientX, e.clientY);
    if (hit) { ents.setTarget(hit.key, { byHand: true }); return; }
    const g = ctl.groundAt(e.clientX, e.clientY);
    if (!g) return;
    travel = null;
    // a click on the stairs means "take them"; anywhere else, walk around stairs on the way
    const pass = passageUnder(g.x, g.z);
    if (pass) { const s = zone.passageWorld(heroRoom, pass); ctl.walkTo(s.x, s.z, null, { goal: { room: heroRoom.vnum, dir: pass }, avoid: null }); }
    else ctl.walkTo(g.x, g.z);
  });
  canvas.addEventListener('dblclick', e => {
    const hit = ents.pick(e.clientX, e.clientY);
    if (hit && hit.kind === 'mob') { ents.setTarget(hit.key, { byHand: true }); attack(); }
  });
  MH.bus.on('hud.untarget', () => ents.setTarget(null));
  MH.bus.on('hud.cycleTarget', () => {
    if (!hero) return;
    const p = hero.root.position;
    // enemies first: whoever is fighting you, then the hostile, then the rest by distance;
    // shopkeepers, trainers and quest-givers only when nothing else is around
    const near = [...ents.list.values()].filter(e => e.kind === 'mob' && e.root && e.root.position.distanceTo(p) < 22);
    const foes = near.filter(e => !(e.data.shopkeeper || e.data.trainer || e.data.quest));
    const list = (foes.length ? foes : near)
      .sort((a, b) => (!!b.data.fighting - !!a.data.fighting) || (isHostile(b) - isHostile(a))
        || a.root.position.distanceTo(p) - b.root.position.distanceTo(p));
    if (!list.length) return hud.toast('Nothing nearby to target.');
    const i = list.findIndex(e => e.key === ents.target);
    ents.setTarget(list[(i + 1) % list.length].key, { byHand: true });
  });
  // how far from its target an action reaches (combat_range.py via /combatdata);
  // null for actions centred on the hero (rally, fade, crescendo...)
  function rangeOf(id, spell) {
    if (id === 'attack') return reachOf();
    const ab = ranges.abilities && ranges.abilities[id];
    if (ab) return /^(self|nova)/.test(ab.shape) ? null : ab.range;
    return spell ? ranges.spellDefault || 14 : ranges.melee || 2.5;
  }
  // the server fights within one room: be in the target's room and within the action's
  // reach, walking only as far as needed (an archer stops at bow range, not in its face)
  function inReach(t, range, then) {
    const same = heroRoom && t.vnum === heroRoom.vnum;
    const p = hero.root.position, q = t.root.position;
    const d = Math.hypot(q.x - p.x, q.z - p.z);
    if (range == null || (same && d <= range + 0.3)) return then();
    if (same) return approach(t, range, then);
    // another room (the server fights room by room): stop just inside the target's room,
    // at the action's reach if the room is big enough for it
    const room = zone && zone.rooms.get(t.vnum);
    if (!room) return approach(t, Math.min(range, 4), () => { if (heroRoom && t.vnum === heroRoom.vnum) then(); });
    const k = Math.max(1.2, range - 0.6) / (d || 1);
    const x = Math.min(room.ox + ROOM_W - 1.5, Math.max(room.ox + 1.5, q.x + (p.x - q.x) * k));
    const z = Math.min(room.oz + ROOM_H - 1.5, Math.max(room.oz + 1.5, q.z + (p.z - q.z) * k));
    ctl.walkTo(x, z, () => { if (heroRoom && t.vnum === heroRoom.vnum) then(); });
  }
  function attack() {
    const t = ents.targeted;
    if (!t || !t.root) return hud.toast('No target — click a creature or press Tab.');
    if (t.kind !== 'mob') return hud.toast('You cannot attack that.');
    inReach(t, reachOf(), () => {
      ctl.face(t.root.position.x, t.root.position.z);
      if (actionMode()) {
        // real time: every press goes to the server; a blow that is due shows at once, an early
        // press waits for the clock (pressed in its last moments, that blow lands perfectly)
        const now = performance.now();
        const press = clock.press(now);
        if (press.swing && MH.state.inCombat) combat.localSwing();
        const cmd = `webattack ${refFor(t)}`;
        lastAction = { cmd, at: now };
        MH.sendCommand(cmd, false);
        return;
      }
      // (the opening blow comes back at once as an attack event, with the class's swing)
      if (!MH.state.inCombat) { const cmd = `kill ${refFor(t)}`; lastAction = { cmd, at: performance.now() }; MH.sendCommand(cmd); }
    });
  }
  MH.bus.on('hud.attack', attack);
  // the server refused an action for distance: close in (or step back) and retry once
  let lastAction = null, oorToast = 0;
  function approach(target, need, then) {
    const p = hero.root.position, q = target.root.position;
    const dx = p.x - q.x, dz = p.z - q.z, d = Math.hypot(dx, dz) || 1;
    const stand = Math.max(1.2, need - 0.6);
    ctl.walkTo(q.x + dx / d * stand, q.z + dz / d * stand, then);
  }
  function outOfRange(e) {
    const ref = e.dst && e.dst.m != null ? ents.list.get(`m${e.dst.m}`) : ents.targeted;
    const t = ref && ref.root ? ref : ents.targeted;
    if (!t || !t.root) return hud.toast(e.need ? `Too far — get within ${e.need} m` : 'Out of range');
    // the round's blow fell short: a melee hero closes in on its own (keys still win);
    // archers and casters keep the spot they chose and are told the range instead
    if (e.auto) {
      if (!(ranges.auto[myClass()] || {}).ranged) { if (!ctl.keys.size && !ctl.path) approach(t, e.need || reachOf()); }
      else if (performance.now() - oorToast > 5000) { oorToast = performance.now(); hud.toast(`Out of range — get within ${e.need || reachOf()} m`); }
      return;
    }
    // an ability: walk into its reach and use it again
    if (lastAction && performance.now() - lastAction.at < 4000) {
      const retry = lastAction; lastAction = null;
      hud.toast(`Closing to ${e.need} m…`);
      approach(t, e.need || 2.5, () => MH.sendCommand(retry.cmd));
    } else hud.toast(`Too far — get within ${e.need} m`);
  }
  MH.bus.on('hud.flee', () => MH.sendCommand('flee'));
  MH.bus.on('hud.cameraReset', () => engine.snapNorth());
  // right-click a slot on the bar
  MH.bus.on('hud.slotMenu', ({ x, y, slot, id, name }) => ctxMenu.show(x, y, name || id, [
    { label: 'Use', run: () => hud.useAbility(id) },
    { label: 'Take off the bar', run: () => hud.unslot(slot) },
    { label: 'Spellbook (K)', run: () => hud.spellbook.toggle(true) },
  ]));
  const NO_GCD = new Set(['brace', 'sidestep', 'interrupt', 'flee', 'escape', 'evade']);
  MH.bus.on('hud.ability', ab => {
    const t = ents.targeted;
    // real time: skills and casts wait for the global cooldown (the bar shows its sweep)
    if (actionMode() && MH.state.inCombat && !NO_GCD.has(ab.id)) {
      const now = performance.now();
      if (clock.gcdLeft(now) > 80) return hud.flashSlot && hud.flashSlot(ab.id, 'busy');
      clock.startGcd(now);
    }
    // the hero starts the ability's own move on the key press (its recipe, abilityfx.js: the
    // clip, a leap or a blink, what gathers in the hands); the server's event then only adds
    // what flies and lands (fxdirector.js picks up where the key press left off)
    const r = combat.recipe(ab.id, myClass(), { k: ab.spell ? 'spell' : 'ability' });
    const begin = target => combat.director.prelude(r, { target: target && target.root ? target : null });
    // a heal or a blessing goes to the player you have targeted, else to yourself
    if (ab.ally) {
      begin(t && t.kind === 'player' ? t : null);
      return MH.sendCommand(abilityCommand(ab, t && t.kind === 'player' ? refFor(t) : null));
    }
    if (ab.self || !t || t.kind !== 'mob') {
      if (!ab.self && !t) return hud.toast('No target — click a creature or press Tab.');
      // a self ability that throws something (a release of charges) throws it at your target
      begin(r.travel && t && t.kind === 'mob' ? t : null);
      return MH.sendCommand(abilityCommand(ab, null));
    }
    inReach(t, rangeOf(ab.id, ab.spell), () => {
      begin(t);
      // the exact creature ('#12'): the server turns it into the keyword its commands know
      const cmd = abilityCommand(ab, refFor(t));
      lastAction = { cmd, at: performance.now() };
      MH.sendCommand(cmd);
    });
  });
  // ---- doors ----
  // Every door of the hero's room has a prompt spot (the middle of its doorway, or the
  // stairs for a trapdoor); the nearest one says what E will do (doorlogic.js). E, walking
  // into a closed door and the right-click menu all send "webdoor <room> <dir> <action>";
  // the server answers door_result and pushes the new state of both sides to everyone.
  function doorAnchorWorld(room, dir) {
    const a = doorAnchor(zone.layoutOf(room), dir, ROOM_W, ROOM_H);
    return a ? new THREE.Vector3(room.ox + a.x, 0, room.oz + a.z) : null;
  }
  function nearestDoor(maxDist, { closedOnly = false } = {}) {
    if (!heroRoom) return null;
    const p = hero.root.position;
    let best = null;
    for (const [dir, info] of Object.entries(heroRoom.doors)) {
      if (closedOnly && !info.closed) continue;
      const at = doorAnchorWorld(heroRoom, dir);
      if (!at) continue;
      const dist = Math.hypot(p.x - at.x, p.z - at.z);
      if (dist < maxDist && (!best || dist < best.dist)) best = { dir, info, at, dist };
    }
    return best;
  }
  let doorBusy = 0;
  const doorAuto = new Map();          // dir -> when we last opened it by walking into it
  function sendDoor(dir, action) {
    const now = performance.now();
    if (!heroRoom || !action || now - doorBusy < 400) return;
    doorBusy = now;
    MH.sendCommand(`webdoor ${heroRoom.vnum} ${dir} ${action}`, false);
  }
  // a door action chosen from the menu: walk up to the door first if it is out of reach
  function doDoor(dir, action) {
    const at = doorAnchorWorld(heroRoom, dir);
    const p = hero.root.position;
    if (!at || Math.hypot(p.x - at.x, p.z - at.z) < 2.6) return sendDoor(dir, action);
    const c = zone.centre(heroRoom);
    const toC = c.clone().sub(at).setY(0).normalize().multiplyScalar(1.3);
    const room = heroRoom;
    ctl.walkTo(at.x + toC.x, at.z + toC.z, () => { if (heroRoom === room) sendDoor(dir, action); });
  }
  // a door's sound when its state really changes (not when a view merely refreshes it)
  function setDoorHeard(r, dir, info) {
    const d = zone.doorOf(r, dir);
    const before = d ? { closed: d.closed, locked: d.locked } : null;
    zone.setDoor(r, dir, info);
    if (!before || !d || !heroRoom || Math.abs(r.ox - heroRoom.ox) + Math.abs(r.oz - heroRoom.oz) > 60) return false;
    const at = doorAnchorWorld(r, dir);
    if (before.closed !== d.closed) return sound.play(d.closed ? 'door_close' : 'door_open', { at });
    if (before.locked !== d.locked) return sound.play('lock', { at });
    return false;
  }
  MH.bus.on('door.update', ev => {
    if (!zone) return;
    let heard = false;
    for (const d of ev.doors || []) {
      const r = zone.rooms.get(d.vnum);
      if (!r) continue;
      // the two sides of one door arrive together: one sound for both
      if (heard) zone.setDoor(r, d.dir, d); else heard = setDoorHeard(r, d.dir, d);
    }
  });
  MH.bus.on('door.result', res => {
    doorBusy = 0;
    if (res.ok && res.pending) { castbar.start(res.secs || 5, res.action === 'lock' ? 'Locking without a key…' : 'Picking the lock…'); return; }
    if (!res.ok && res.reason) hud.toast(res.reason);
    if (!res.ok) sound.play('ui_error');
    if (res.door && zone) { const r = zone.rooms.get(res.vnum); if (r) setDoorHeard(r, res.dir, res.door); }
  });
  MH.bus.on('env.channel', c => castbar.start(c.secs || 5, c.label || 'Working…'));
  MH.bus.on('env.channel.end', () => castbar.end());
  // E: do what the prompt says
  window.addEventListener('keydown', e => {
    if (!hero || e.repeat || /INPUT|TEXTAREA/.test(e.target.tagName)) return;
    if (e.key.toLowerCase() !== 'e') return;
    const d = nearestDoor(2.6);
    if (!d) return;
    const pr = doorPrompt(d.info);
    if (pr && pr.action) sendDoor(d.dir, pr.action);
    else if (pr) hud.toast(pr.text);
  });
  // walking into a closed door: an unlocked one opens; a locked one says why not
  function pushingDoor(room, dir, now) {
    const info = room.doors[dir];
    if (!info || !info.closed) return;
    const pr = doorPrompt(info);
    if (pr && pr.action === 'open') {
      if (now - (doorAuto.get(dir) || 0) > 2000) { doorAuto.set(dir, now); sendDoor(dir, 'open'); }
    } else if (pr && now - doorToast > 4000) {
      doorToast = now;
      hud.toast(pr.action ? `${pr.text} — press E` : pr.text);
    }
  }
  // every frame: the prompt over the nearest door, pushing into a closed doorway, and timed
  // work (picking a lock) that ends when you move
  let pushClock = 0;
  function doorTick(dt, now) {
    const p = hero.root.position;
    const near = nearestDoor(2.6);
    const speed = ctl.vel.length();
    if (near && (near.info.closed || (near.dist < 1.8 && speed < 1)) && !near.info.broken) {
      const hatch = near.dir === 'up' || near.dir === 'down';
      prompt.show(near.at.clone().setY(hatch ? 1.7 : 2.8), doorPrompt(near.info));
    } else prompt.hide();
    if (near && near.info.closed && near.dist < 1.2 && ctl.keys.size) {
      const w = ctl.wish();
      const dx = near.at.x - p.x, dz = near.at.z - p.z, l = Math.hypot(dx, dz) || 1;
      if ((dx * w.x + dz * w.y) / l > 0.5) { if ((pushClock += dt) > 0.25) pushingDoor(heroRoom, near.dir, now); }
      else pushClock = 0;
    } else pushClock = 0;
    if (castbar.active && (ctl.keys.size || ctl.path)) { castbar.end(); MH.sendCommand('stopwork', false); }
  }
  // ---- right-click (press and release without dragging): a menu for what is under it ----
  // (a right-drag turns the camera: input.js tells them apart)
  attachWorldInput(engine, canvas, { onContext: openContext, typing: e => /INPUT|TEXTAREA/.test((e.target || {}).tagName || '') });
  function pickAt(x, y) {
    const ent = ents.pick(x, y);
    if (ent) return { kind: ent.kind === 'player' ? 'player' : 'mob', ent };
    const r = canvas.getBoundingClientRect();
    const hp = hero.root.position.clone().setY(hero.root.position.y + 1.1).project(engine.camera);
    const sx = r.left + (hp.x + 1) / 2 * r.width, sy = r.top + (1 - hp.y) / 2 * r.height;
    if (Math.hypot(x - sx, y - sy) < 36) return { kind: 'self' };
    const g = ctl.groundAt(x, y);
    if (!g) return null;
    let best = null;
    for (const [dir, info] of Object.entries(heroRoom.doors)) {
      const at = doorAnchorWorld(heroRoom, dir);
      if (!at) continue;
      const dist = Math.hypot(g.x - at.x, g.z - at.z);
      if (dist < 2 && (!best || dist < best.dist)) best = { dir, info, dist };
    }
    return best ? { kind: 'door', door: best } : { kind: 'ground', point: g };
  }
  function openContext(x, y) {
    if (!hero || !heroRoom) return;
    const hit = pickAt(x, y);
    if (!hit) return;
    const p = MH.state.player || {};
    const { title, items } = verbsFor(hit, { skills: hud.targetSkills(), posture: p.position, inCombat: MH.state.inCombat,
      room: heroRoom && heroRoom.vnum, inGroup: hud.party.inGroup });
    if (!items.length) return;
    ctxMenu.show(x, y, title, items.map(it => ({ label: it.label, run: (it.cmd || it.act) ? () => runVerb(hit, it) : null })));
  }
  function runVerb(hit, it) {
    if (it.cmd) return MH.sendCommand(it.cmd);
    const a = it.act;
    if (a === 'attack') { ents.setTarget(hit.ent.key, { byHand: true }); return attack(); }
    if (a === 'target') return ents.setTarget(hit.ent.key, { byHand: true });
    if (a.startsWith('ability:')) { ents.setTarget(hit.ent.key, { byHand: true }); return hud.useAbility(a.slice(8)); }
    if (a.startsWith('door:')) return doDoor(hit.door.dir, a.slice(5));
    if (a.startsWith('tell:')) return hud.whisper(a.slice(5));
    if (a === 'inventory' || a === 'character') return hud.openPanel(a);
    if (a === 'trainer') return hud.openTrainer(hit.ent.data && (hit.ent.data.short || hit.ent.data.name));
    if (a === 'walk' && hit.point) { travel = null; return ctl.walkTo(hit.point.x, hit.point.z); }
  }

  // ---- auto-target: whatever attacks you becomes your target (targeting.js decides when) ----
  const pendingAggro = new Map();      // creature id -> when it hit us before it was drawn
  let aggroRefresh = 0;
  function aggro(id) {
    const now = Date.now();
    const e = ents.list.get(`m${id}`);
    if (!e) {
      pendingAggro.set(id, now);
      if (now - aggroRefresh > 1500 && MH.refreshState) { aggroRefresh = now; MH.refreshState(); }
      return;
    }
    e.aggroAt = now;
    ents.markHostile(e);
    if (heroRoom && shouldRetarget(ents.targeted, e, heroRoom.vnum, now)) ents.setTarget(e.key);
  }
  function applyPendingAggro() {
    const now = Date.now();
    for (const [id, at] of pendingAggro) {
      const e = ents.list.get(`m${id}`);
      if (e) {
        pendingAggro.delete(id);
        e.aggroAt = at;
        if (heroRoom && shouldRetarget(ents.targeted, e, heroRoom.vnum, now)) ents.setTarget(e.key);
      } else if (now - at > 10000) pendingAggro.delete(id);
    }
  }

  // ---- in a fight: keep a target, close in for melee, show the distance ----
  let chaseClock = 0;
  function fightTick(dt) {
    const p = hero.root.position;
    let t = ents.targeted;
    // your target died or vanished: the creature that hit you last takes its place
    if (heroRoom && (!t || (t.data && t.data.maxHp && t.data.hp <= 0))) {
      const next = retargetOnDeath(ents.list.values(), heroRoom.vnum);
      if (next && next !== t) { ents.setTarget(next.key); t = next; }
    }
    if (MH.state.inCombat && (!t || !t.root)) {
      // whoever is fighting you becomes your target
      const foe = [...ents.list.values()].filter(e => e.kind === 'mob' && e.root && e.data.fighting && e.vnum === (heroRoom && heroRoom.vnum))
        .sort((a, b) => a.root.position.distanceTo(p) - b.root.position.distanceTo(p))[0];
      if (foe) { ents.setTarget(foe.key); t = foe; }
    }
    const dist = t && t.root ? Math.hypot(t.root.position.x - p.x, t.root.position.z - p.z) : null;
    hud.setDistance(dist, t && t.vnum === (heroRoom && heroRoom.vnum));
    if ((chaseClock -= dt) > 0 || !MH.state.inCombat || !t || !t.root || t.kind !== 'mob') return;
    chaseClock = 0.4;
    const reach = reachOf();
    const ranged = (ranges.auto[myClass()] || {}).ranged;
    // melee heroes follow a foe that steps away; archers and casters hold their ground
    if (!ranged && dist > reach + 0.3 && !ctl.keys.size && !ctl.path && t.vnum === heroRoom.vnum) approach(t, reach);
  }

  // ---- positions for the server's range rules (combat_range.py) ----
  // the hero's spot in its room ~5x a second in a fight (2x otherwise, only when it
  // changes), and once per room the spots where this client placed the creatures
  let posClock = 0, lastPos = '', seeded = '';
  function reportPositions(dt) {
    const sock = MH.state.mapSocket;
    if ((posClock -= dt) > 0 || !heroRoom || !sock || sock.readyState !== 1) return;
    posClock = 0.2;                 // (sent only when it changes; other players see you move from it)
    const p = hero.root.position;
    const x = +(p.x - heroRoom.ox).toFixed(2), z = +(p.z - heroRoom.oz).toFixed(2);
    const key = `${heroRoom.vnum}:${x}:${z}`;
    if (key !== lastPos) { lastPos = key; sock.send(JSON.stringify({ type: 'pos', vnum: heroRoom.vnum, x, z })); }
    const mobs = [...ents.list.values()].filter(e => e.kind === 'mob' && e.vnum === heroRoom.vnum && e.root && e.data.id != null)
      .map(e => ({ id: e.data.id, x: +(e.root.position.x - heroRoom.ox).toFixed(2), z: +(e.root.position.z - heroRoom.oz).toFixed(2) }));
    const mk = `${heroRoom.vnum}:${mobs.map(m => m.id).join(',')}`;
    if (mobs.length && mk !== seeded) { seeded = mk; sock.send(JSON.stringify({ type: 'mobpos', vnum: heroRoom.vnum, mobs })); }
  }

  // footsteps: one every stride (longer when running), by what is underfoot
  function footsteps(dt, p) {
    const v = hop || climb || slide ? 0 : ctl.vel.length();
    if (v < 0.6) { stride = Math.min(stride, 0.4); return; }
    stride += v * dt;
    const len = v > 3.2 ? 1.6 : 0.95;
    if (stride < len) return;
    stride = 0;
    const wet = heroRoom && zone.tile(heroRoom, p.x, p.z) === WATER_TILE;
    sound.play(wet ? 'step_water' : stepSurface, { vol: v > 3.2 ? 1 : 0.7 });
  }

  // ---- the frame ----
  engine.onTick((dt, t) => {
    // behind the title screen the view drifts slowly over the hollow
    if (!hero) { if (backdrop) { backdrop.update(dt, t); engine.rig.yaw = Math.sin(t * 0.045) * 0.5; } return; }
    const now = performance.now();
    if (climb) {
      // stepping onto stairs before a hop, or off them after one
      climb.t = Math.min(1, climb.t + dt / climb.dur);
      const k = 1 - Math.pow(1 - climb.t, 2);
      hero.root.position.lerpVectors(climb.from, climb.to, k);
      if (climb.t >= 1) { if (!hop) hero.root.position.y = 0; climb = null; }
    } else if (slide) {
      slide.t = Math.min(1, slide.t + dt / 0.3);
      const k = 1 - Math.pow(1 - slide.t, 3);
      hero.root.position.lerpVectors(slide.from, slide.to, k);
      if (slide.t >= 1) { setHeroRoom(slide.room); slide = null; }
    } else if (!hop) {
      ctl.update(dt);
    }
    const p = hero.root.position;
    engine.rig.target.set(p.x, 0, p.z);
    footsteps(dt, p);
    zone.update(dt, t, p, ctl.vel);
    hero.update(dt);
    if (travel && (ctl.keys.size || MH.state.inCombat)) travel = null;
    // stepping on or off stairs, sliding and hopping count as moving: only standing still
    // after you have arrived wakes the stairs beside you
    if (climb || slide || hop || ctl.keys.size || ctl.path || ctl.vel.lengthSq() > 0.04) lastActive = now;
    if (!slide && !hop && !climb && heroRoom) {
      const r = zone.roomAt(p.x, p.z);
      if (r && r !== heroRoom) heroWalkedInto(heroRoom, r);
      // a click path's passage counts only in the room it belongs to
      const goal = ctl.goal && ctl.goal.room === heroRoom.vnum ? ctl.goal.dir : null;
      gate.update(heroSpots, { x: p.x - heroRoom.ox, z: p.z - heroRoom.oz }, { idleMs: now - lastActive, goal });
      const ps = zone.passageAt(heroRoom, p, ctl.vel, gate,
        { viaKeys: ctl.keys.size > 0, viaPath: !!ctl.path, goal, inCombat: MH.state.inCombat, now });
      if (ps && !ps.blocked) startHop(ps);
      else if (ps && ps.blocked === 'combat') {
        if (now - leashToast > 2500) { leashToast = now; hud.toast("You're fighting! Flee to escape."); }
      } else if (ps && ps.blocked === 'door') pushingDoor(heroRoom, ps.dir, now);
      doorTick(dt, now);
    } else prompt.hide();
    castbar.update();
    if (hop && !hop.loading && now - hop.at > HOP_TIMEOUT_MS) {
      // no answer: give up quietly, ask the server where we are
      const h = hop; hop = null; climb = null;
      $('#vignette').style.background = '';
      hero.root.position.y = 0;
      if (heroRoom) slide = { from: hero.root.position.clone(), to: zone.side(heroRoom, h.dir), t: 0, room: heroRoom };
      gate.disarm(h.dir);
      if (MH.refreshState) MH.refreshState();
      hud.toast("The way didn't open.");
    }
    ents.update(dt, t, p);
    fightTick(dt);
    sync.tick();
    reportPositions(dt);
  });
  // overlays once the camera is placed for this frame (nothing lags while it turns)
  engine.onLateTick(() => {
    if (!hero) return;
    const p = hero.root.position;
    cutout.update(engine.camera, p);
    ents.layoutPlates(p);
    prompt.update(engine.camera, canvas);
    mm.update(p, ctl.yaw, engine.rig.yaw);
  });
}
