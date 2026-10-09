// M0 look-and-feel spike (/play): four real room layouts from the MUD's room generator
// stitched into one world — a forest glade and a brook above, a crypt below — a knight
// you can walk through all of it without a single stop, and the crypt's skeletons.
// No server yet: this page exists to judge the look, the camera and the walking.
import * as THREE from 'three';
import { createEngine } from './engine.js';
import { loadKit, spawnCharacter } from './assets.js';
import { World } from './world.js';
import { Controller } from './controller.js';
import { cutout } from './cutout.js';
import { attachPerf } from './perf.js';

const params = new URLSearchParams(location.search);
const engine = createEngine(document.getElementById('stage'), { quality: params.get('q') || 'high' });
attachPerf(engine, document.getElementById('perf'));

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

async function main() {
  const [dungeon, nature] = await Promise.all([loadKit('dungeon'), loadKit('nature')]);
  if (params.get('gallery')) {
    const { showGallery } = await import('./gallery.js');
    const at = showGallery(engine, params.get('gallery') === 'nature' ? nature : dungeon);
    engine.rig.target.copy(at); engine.placeCamera(true);
    window.MH3D = { engine, THREE };
    document.getElementById('loading').classList.add('done');
    return;
  }
  const world = new World(engine, { dungeon, nature });
  for (const r of ROOMS) world.addRoom(r, r.cx, r.cy);

  // ---- the hero ----
  const hero = await spawnCharacter('knight');
  engine.scene.add(hero.root);
  const start = world.centre(world.byVnum.get(990001));
  hero.root.position.copy(start);
  const ctl = new Controller(engine, hero, (x, z) => world.blocked(x, z));
  engine.rig.target.copy(start);
  engine.placeCamera(true);

  // ---- the crypt's residents ----
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

  // ---- room awareness: mood and the room-name banner ----
  const banner = document.getElementById('room-name');
  let here = null, bannerT = 0;
  const enter = room => {
    here = room;
    engine.setMood(room.indoor ? 'crypt' : 'forest', !banner.textContent);
    banner.textContent = room.name;
    banner.style.opacity = 1;
    bannerT = 2.2;
  };

  engine.onTick((dt, t) => {
    ctl.update(dt);
    const p = hero.root.position;
    engine.rig.target.set(p.x, 0, p.z);
    cutout.update(engine.camera, p);
    world.update(dt, t, p);
    const room = world.roomAt(p.x, p.z);
    if (room && room !== here) enter(room);
    if (bannerT > 0 && (bannerT -= dt) <= 0) banner.style.opacity = 0;
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
  });

  window.MH3D = { engine, world, hero, ctl, THREE };
  setTimeout(() => document.getElementById('hint').style.opacity = 0, 9000);
  document.getElementById('loading').classList.add('done');
}

main().catch(err => {
  console.error(err);
  const l = document.getElementById('loading');
  l.textContent = 'Could not start the 3D client: ' + err.message;
});
