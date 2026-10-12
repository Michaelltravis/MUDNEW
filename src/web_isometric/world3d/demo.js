// The look-and-feel scene from milestone M0: four real room layouts from the MUD's room
// generator (a glade, a brook, a crypt, a hall) stitched into one world, a knight and the
// crypt's skeletons. It is the backdrop behind the login screen (the camera drifts over
// it) and, at /play?demo, a playable page for checking art, camera and performance
// (/play?demo&gallery=dungeon|nature lays out a whole kit).
import * as THREE from 'three';
import { spawnCharacter } from './assets.js';
import { World } from './world.js';
import { Controller } from './controller.js';
import { cutout } from './cutout.js';

const ROOMS = [
  { cx: 0, cy: 0, vnum: 990001, sector: 'forest', name: 'Whispering Glade',
    description: 'Tall oaks ring a mossy clearing. A small pond glitters among the ferns.',
    exits: { east: { to_room: 990002 }, south: { to_room: 990003 } } },
  { cx: 1, cy: 0, vnum: 990002, sector: 'forest', name: 'Brookside Trail',
    description: 'A brook babbles across the old trail between the pines.',
    exits: { west: { to_room: 990001 }, south: { to_room: 990004 } } },
  { cx: 0, cy: 1, vnum: 990003, sector: 'inside', name: 'Crypt Antechamber',
    description: 'Cold stone and guttering torches. Something shuffles in the dark.',
    exits: { north: { to_room: 990001 }, east: { to_room: 990004 } } },
  { cx: 1, cy: 1, vnum: 990004, sector: 'inside', name: 'Hall of Bones',
    description: 'The dead keep their vigil here.',
    exits: { north: { to_room: 990002 }, west: { to_room: 990003 } } },
];

export async function buildDemo(engine, kits, { interactive = false, banner = null } = {}) {
  const world = new World(engine, kits);
  const groups = [];
  for (const r of ROOMS) groups.push(world.addRoom(r, r.cx, r.cy).group);

  const hero = await spawnCharacter('knight');
  engine.scene.add(hero.root);
  const start = world.centre(world.byVnum.get(990001));
  hero.root.position.copy(start);
  const ctl = new Controller(engine, hero, (x, z) => world.blocked(x, z));
  ctl.enabled = interactive;
  engine.rig.target.copy(start);
  engine.placeCamera(true);

  const slot = (vnum, i) => {
    const r = world.byVnum.get(vnum), s = r.layout.spawnSlots[i % r.layout.spawnSlots.length];
    return new THREE.Vector3(r.ox + s.x / 16, 0, r.oz + s.y / 16);
  };
  const cast = [
    { model: 'skeleton_warrior', at: slot(990004, 0), anim: 'Idle_Combat' },
    { model: 'skeleton_mage', at: slot(990004, 3), anim: 'Spellcasting' },
    { model: 'skeleton_minion', at: slot(990003, 1), anim: 'Walking_D_Skeletons', patrol: true },
    { model: 'skeleton_rogue', at: slot(990003, 4), anim: 'Idle_B' },
  ];
  const actors = [hero];
  for (const c of cast) {
    const a = await spawnCharacter(c.model);
    a.root.position.copy(c.at);
    a.root.rotation.y = Math.random() * Math.PI * 2;
    a.play(c.anim, 0, 0.9 + Math.random() * 0.2);
    a.patrol = c.patrol ? { home: c.at.clone(), t: Math.random() * 6 } : null;
    engine.scene.add(a.root);
    actors.push(a);
  }

  const onKey = e => { if ((e.key === ' ' || e.key === 'f') && !e.repeat) { ctl.swing(); e.preventDefault(); } };
  const onDown = e => {
    if (e.button !== 0) return;
    const g = ctl.groundAt(e.clientX, e.clientY);
    if (g) ctl.walkTo(g.x, g.z);
  };
  if (interactive) {
    window.addEventListener('keydown', onKey);
    engine.renderer.domElement.addEventListener('pointerdown', onDown);
  }

  let here = null;
  const enter = room => {
    here = room;
    engine.setMood(room.indoor ? 'crypt' : 'forest', !banner);
    if (banner) banner(room.name);
  };
  let orbit = 0;
  function update(dt, t) {
    if (interactive) ctl.update(dt);
    else {
      // behind the login card: drift slowly over the glade and the crypt
      orbit += dt * 0.06;
      engine.rig.target.set(24 + Math.sin(orbit) * 12, 0, 15 + Math.sin(orbit * 0.7) * 6);
    }
    const p = hero.root.position;
    if (interactive) engine.rig.target.set(p.x, 0, p.z);
    cutout.update(engine.camera, interactive ? p : engine.rig.target);
    world.update(dt, t, interactive ? p : engine.rig.target);
    const room = world.roomAt(interactive ? p.x : engine.rig.target.x, interactive ? p.z : engine.rig.target.z);
    if (room && room !== here) enter(room);
    for (const a of actors) {
      if (a.patrol) {
        a.patrol.t += dt * 0.35;
        const k = a.patrol.t;
        const nx = a.patrol.home.x + Math.sin(k) * 2.2, nz = a.patrol.home.z + Math.sin(k * 2) * 1.1;
        a.root.rotation.y = Math.atan2(nx - a.root.position.x, nz - a.root.position.z);
        a.root.position.set(nx, 0, nz);
      }
      a.update(dt);
    }
  }
  function dispose() {
    window.removeEventListener('keydown', onKey);
    engine.renderer.domElement.removeEventListener('pointerdown', onDown);
    for (const g of groups) engine.scene.remove(g);
    for (const a of actors) engine.scene.remove(a.root);
    for (const l of world.lights) engine.scene.remove(l);
  }
  return { world, hero, ctl, update, dispose };
}

// /play?demo&gallery=rooms: one room of every look (room_looks.py), side by side, joined up.
// MH3D_gallery.rooms lists each look's room centre (screenshots: tests/web/probe and the
// owner's checks).
export const LOOK_SAMPLES = [
  { look: 'cave', sector: 'inside', name: 'The Dripping Cavern', description: 'Water drips from the stalactites into still pools. The cave walls glitter.' },
  { look: 'mine', sector: 'inside', name: 'The Old Mine Shaft', description: 'Timber props hold up the shaft. Ore glints in the rock where the miners left off.' },
  { look: 'crypt', sector: 'inside', name: 'The Forgotten Crypt', description: 'Coffins line the walls of the crypt, and the dead lie unquiet.' },
  { look: 'sewer', sector: 'inside', name: 'The Muddy Sewer', description: 'A channel of foul water runs down the middle of the sewer.' },
  { look: 'dungeon', sector: 'inside', name: 'The Dungeon Cells', description: 'Broken walls and rubble; the cells stand empty.' },
  { look: 'desert', sector: 'field', name: 'A Sea of Dunes', description: 'The sands roll away in dunes under a merciless sun.' },
  { look: 'snow', sector: 'field', name: 'The Frozen Waste', description: 'Snow lies deep over the tundra, and ice glazes the rocks.' },
  { look: 'shore', sector: 'field', name: 'The Pebbled Shore', description: 'Waves lap at a beach of sand and pebbles strewn with driftwood.' },
  { look: 'volcanic', sector: 'field', name: 'The Ashfields', description: 'Lava glows in the cracks of the ashen ground.' },
  { look: 'swamp', sector: 'swamp', name: 'The Sucking Mire', description: 'Dead trees stand in the black water of the swamp.' },
  { look: 'forest', sector: 'forest', name: 'A Forest Path', description: 'Tall oaks shade the path.' },
  { look: 'inside', sector: 'inside', name: 'The Great Hall', description: 'A plain stone hall.' },
];
export function buildLooksGallery(engine, kits) {
  const world = new World(engine, kits);
  const COLS = 4;
  const vnumAt = (cx, cy) => 991000 + cy * COLS + cx;
  const rooms = [];
  LOOK_SAMPLES.forEach((r, i) => {
    const cx = i % COLS, cy = Math.floor(i / COLS);
    const exits = {};
    if (cx > 0) exits.west = { to_room: vnumAt(cx - 1, cy) };
    if (cx < COLS - 1 && i + 1 < LOOK_SAMPLES.length) exits.east = { to_room: vnumAt(cx + 1, cy) };
    if (cy > 0) exits.north = { to_room: vnumAt(cx, cy - 1) };
    if (i + COLS < LOOK_SAMPLES.length) exits.south = { to_room: vnumAt(cx, cy + 1) };
    const built = world.addRoom({ ...r, vnum: vnumAt(cx, cy), exits }, cx, cy);
    const c = world.centre(world.byVnum.get(vnumAt(cx, cy)));
    rooms.push({ look: r.look, theme: built.theme, x: c.x, z: c.z, name: r.name });
  });
  window.MH3D_gallery = { rooms, world };
  return new THREE.Vector3(rooms[0].x, 0, rooms[0].z);
}

// /play?demo&gallery=steeds: a knight on each kind of mount (steed.js), walking on the spot
export const STEED_SAMPLES = ['horse', 'warhorse', 'nightmare', 'griffin', 'clockwork_steed', 'moonstag', 'stoneboar', 'merchant_camel', 'shadowpanther', 'dire_warg'];
export async function buildSteedGallery(engine, kits) {
  const { mountRider } = await import('./steed.js');
  const world = new World(engine, kits);
  world.addRoom({ vnum: 992000, sector: 'field', name: 'The Paddock', description: 'Open grass.', exits: {} }, 0, 0);
  world.addRoom({ vnum: 992001, sector: 'field', name: 'The Paddock', description: 'Open grass.', exits: {} }, 1, 0);
  const riders = [];
  for (let i = 0; i < STEED_SAMPLES.length; i++) {
    const a = await spawnCharacter('knight');
    a.root.position.set(4 + (i % 5) * 4.4, 0, 4 + Math.floor(i / 5) * 6);
    a.root.rotation.y = 0.5;
    const riding = mountRider(a, STEED_SAMPLES[i], null);
    engine.scene.add(a.root);
    riders.push({ a, riding, key: STEED_SAMPLES[i] });
  }
  window.MH3D_gallery = { riders: riders.map(r => ({ key: r.key, x: r.a.root.position.x, z: r.a.root.position.z })), world };
  let tt = 0;
  engine.onTick(dt => { tt += dt; for (const r of riders) { r.a.play('Idle', 0.2); r.a.update(dt); r.riding.steed.update(dt, true, 1.4); r.riding.pose(tt, true); } world.update(dt, 0, engine.rig.target); });
  return new THREE.Vector3(12.8, 0, 7);
}
