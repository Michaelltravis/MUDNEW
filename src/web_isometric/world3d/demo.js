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
