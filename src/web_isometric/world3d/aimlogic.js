// Aiming an area spell, the pure parts (aim.js draws the circle; tests/web/aim.test.mjs).

// a point the spell may land on: no farther than `range` from the hero (drawn in along the line
// toward it, as the server does), and inside the hero's room, or one of `room` when it is a
// list (the hero's room and those joined to it by an open way: the circle may land next door,
// reach.py). All in world metres.
export function clampAim(hero, point, range, room, roomW, roomH) {
  let x = point.x, z = point.z;
  const d = Math.hypot(x - hero.x, z - hero.z);
  if (range && d > range) { x = hero.x + (x - hero.x) * range / d; z = hero.z + (z - hero.z) * range / d; }
  const rooms = (Array.isArray(room) ? room : [room]).filter(Boolean);
  if (rooms.length) {
    let best = null;
    for (const r of rooms) {
      const cx = Math.max(r.ox, Math.min(r.ox + roomW, x)), cz = Math.max(r.oz, Math.min(r.oz + roomH, z));
      const off = Math.hypot(cx - x, cz - z);
      if (!best || off < best.off) best = { x: cx, z: cz, off };
    }
    x = best.x; z = best.z;
  }
  return { x, z, clamped: Math.hypot(x - point.x, z - point.z) > 0.05 };
}

// the command with the point, in the room's own metres
export function aimCommand(cmd, room, point) {
  const x = point.x - (room ? room.ox : 0), z = point.z - (room ? room.oz : 0);
  return `${cmd} @${x.toFixed(1)},${z.toFixed(1)}`;
}
