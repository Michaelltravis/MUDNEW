// Death traps look like death (the owner: "death trap rooms should look like you'll die if you
// enter"). A room the server flags deathtrap (or death) kills most who walk in, so it is drawn to
// be read from the room before it: a ledge round a black abyss whose rim burns red from far
// below, the floor strewn with bones, and a skull on a pole at every way in, a red flame over it.
// main.js stops the hero at its edge with a prompt (E to go on anyway); the minimap shows it red.
import * as THREE from 'three';
import { trs } from './assets.js';
import { carveAbyss, inside } from './deathlogic.js';
export { isDeadly } from './deathlogic.js';

const FLOOR = 0;

const VOID_MAT = new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.DoubleSide });
const RIM_MAT = new THREE.MeshBasicMaterial({ color: new THREE.Color(1.5, 0.1, 0.02), side: THREE.DoubleSide });   // HDR: blooms
// the glow far down: fainter rings of ember red toward the middle of the drop
const DEEP_MATS = [[0.5, new THREE.Color(0.16, 0.012, 0.004)], [0.28, new THREE.Color(0.38, 0.03, 0.01)], [0.12, new THREE.Color(0.7, 0.06, 0.015)]]
  .map(([s, c]) => [s, new THREE.MeshBasicMaterial({ color: c, side: THREE.DoubleSide })]);
const POLE_MAT = new THREE.MeshStandardMaterial({ color: 0x2b2018, roughness: 0.9 });
const FLAME_MAT = new THREE.MeshBasicMaterial({ color: new THREE.Color(3.2, 0.35, 0.1) });
const FLAME_GEO = new THREE.SphereGeometry(0.1, 8, 6);

// c: terrain.js's room context {layout, ox, oz, kits, b, rng, group, owned, torches}
export function deathTrap(c) {
  const { layout, ox, oz, kits, b, rng, group, owned } = c;
  const { W, H, grid } = layout;
  const G = kits.graveyard;
  const pts = carveAbyss(layout, rng);
  const shape = s => new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(W / 2 + (x - W / 2) * s, H / 2 + (y - H / 2) * s)));
  const flat = (s, y, mat) => {
    const g = new THREE.ShapeGeometry(shape(s));
    g.rotateX(Math.PI / 2);                 // the shape's y becomes the room's z
    g.translate(ox, y, oz);
    owned.push(g);
    const m = new THREE.Mesh(g, mat);
    group.add(m);
    return m;
  };
  if (pts) {
    // (above the floor tiles' tops, which stand a little proud of 0)
    flat(1.08, 0.11, RIM_MAT);               // the burning lip
    flat(1.0, 0.12, VOID_MAT);               // the drop
    DEEP_MATS.forEach(([k, mat], i) => flat(k, 0.125 + i * 0.004, mat));
  }
  const glow = new THREE.PointLight(0xff3010, 6, W * 0.75, 1.6);
  glow.position.set(ox + W / 2, 0.6, oz + H / 2);
  group.add(glow);
  // bones and skulls on the ledge
  if (G) {
    for (let i = 0; i < 26; i++) {
      const x = 1 + rng() * (W - 2), y = 1 + rng() * (H - 2);
      const cell = grid[Math.floor(y) * W + Math.floor(x)];
      if (cell !== FLOOR || (pts && inside(pts, x, y))) continue;
      const key = ['skull', 'bone_A', 'bone_B', 'bone_C', 'ribcage', 'skull'][Math.floor(rng() * 6)];
      b.add(G.get(key), trs(ox + x, 0, oz + y, rng() * 6.28, 0.55 + rng() * 0.2), { shadow: false });
    }
  }
  // a skull on a pole at every way in, a red flame above it: a warning you can read from outside
  const g = layout.gaps || {};
  const posts = [];
  if (g.north) posts.push([(g.north.x0 ?? W / 2 - 2) - 0.6, 1.2], [(g.north.x1 ?? W / 2 + 2) + 1.6, 1.2]);
  if (g.south) posts.push([(g.south.x0 ?? W / 2 - 2) - 0.6, H - 1.2], [(g.south.x1 ?? W / 2 + 2) + 1.6, H - 1.2]);
  if (g.west) posts.push([1.2, (g.west.y0 ?? H / 2 - 2) - 0.6], [1.2, (g.west.y1 ?? H / 2 + 2) + 1.6]);
  if (g.east) posts.push([W - 1.2, (g.east.y0 ?? H / 2 - 2) - 0.6], [W - 1.2, (g.east.y1 ?? H / 2 + 2) + 1.6]);
  for (const [x, y] of posts) {
    const px = Math.min(W - 0.8, Math.max(0.8, x)), pz = Math.min(H - 0.8, Math.max(0.8, y));
    const pole = new THREE.CylinderGeometry(0.06, 0.08, 2.1, 6);
    pole.translate(ox + px, 1.05, oz + pz);
    owned.push(pole);
    const m = new THREE.Mesh(pole, POLE_MAT);
    m.castShadow = true;
    group.add(m);
    if (G) b.add(G.get('skull'), trs(ox + px, 2.1, oz + pz, Math.PI, 0.5), { shadow: false });
    const f = new THREE.Mesh(FLAME_GEO, FLAME_MAT);
    f.position.set(ox + px, 2.45, oz + pz);
    f.scale.setScalar(1.6);
    group.add(f);
  }
  return true;
}
