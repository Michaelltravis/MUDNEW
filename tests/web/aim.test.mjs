// Aiming an area spell (world3d/aimlogic.js): where the circle may land, and the command it sends.
//   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { clampAim, aimCommand } from '../../src/web_isometric/world3d/aimlogic.js';

const room = { ox: 100, oz: 40 };
test('a point within reach and inside the room is kept as it is', () => {
  const at = clampAim({ x: 102, z: 47 }, { x: 108, z: 47 }, 16, room, 24, 15);
  assert.deepEqual([at.x, at.z, at.clamped], [108, 47, false]);
});
test('a point beyond reach is drawn in along the line toward it, as the server does', () => {
  const at = clampAim({ x: 102, z: 47 }, { x: 140, z: 47 }, 16, null, 24, 15);
  assert.ok(Math.abs(at.x - 118) < 1e-9 && at.z === 47 && at.clamped);
});
test("a point outside the hero's room is kept inside it", () => {
  const at = clampAim({ x: 110, z: 45 }, { x: 110, z: 30 }, 16, room, 24, 15);
  assert.equal(at.z, 40);
  assert.ok(at.clamped);
});
test("the command carries the point in the room's own metres", () => {
  assert.equal(aimCommand("cast 'meteor storm'", room, { x: 112.5, z: 47 }), "cast 'meteor storm' @12.5,7.0");
});
test('with the rooms joined by an open way, the circle may land next door (the nearest room wins)', () => {
  const east = { ox: 124, oz: 40 };
  const at = clampAim({ x: 120, z: 47 }, { x: 132, z: 47 }, 16, [room, east], 24, 15);
  assert.deepEqual([at.x, at.z, at.clamped], [132, 47, false]);
  const north = clampAim({ x: 120, z: 47 }, { x: 120, z: 30 }, 16, [room, east], 24, 15);
  assert.equal(north.z, 40);
});
