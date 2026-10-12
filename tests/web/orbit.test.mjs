// The camera turning around the hero (world3d/orbit.js).   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { orbitOffset, toWorld, dragOrbit, nearestTurn, pitchFor, DragTracker, TILT_MIN, TILT_MAX, PITCH_MIN, PITCH_MAX } from '../../src/web_isometric/world3d/orbit.js';

const near = (a, b, eps = 1e-9) => Math.abs(a - b) < eps;

test('yaw 0 is the old view: the camera south of the hero, looking north', () => {
  const o = orbitOffset(0, Math.PI / 4, 10);
  assert.ok(near(o.x, 0) && o.z > 0 && o.y > 0);
});

test('W walks away from the camera and D to its right, whichever way it is turned', () => {
  for (const yaw of [0, 0.7, Math.PI / 2, Math.PI, -1.9, 5]) {
    const cam = orbitOffset(yaw, 0.6, 10);
    const fwd = { x: -cam.x, z: -cam.z }, l = Math.hypot(fwd.x, fwd.z);
    const w = toWorld(0, -1, yaw);
    assert.ok(near(w.x, fwd.x / l, 1e-9) && near(w.z, fwd.z / l, 1e-9), `W at yaw ${yaw}`);
    const d = toWorld(1, 0, yaw);
    // right of forward (seen from above, x east, z south): (-fz, fx) rotated... cross product y < 0
    assert.ok(near(d.x * w.x + d.z * w.z, 0), 'D is perpendicular to W');
    assert.ok(w.x * d.z - w.z * d.x > 0, `D is to the right at yaw ${yaw}`);
  }
});

test('dragging right turns the view right; dragging up looks down more steeply, within limits', () => {
  const r = dragOrbit(0, 0, 120, 0);
  assert.ok(near(r.yaw, -0.78, 1e-9));
  const fwd = toWorld(0, -1, r.yaw);
  assert.ok(fwd.x > 0.5, 'turned toward the east (right)');
  assert.equal(dragOrbit(0, 0, 0, -1000).tilt, TILT_MAX);
  assert.equal(dragOrbit(0, 0, 0, 1000).tilt, TILT_MIN);
  assert.ok(near(pitchFor(58, TILT_MAX) * 180 / Math.PI, Math.min(PITCH_MAX, 58 + TILT_MAX)));
  assert.ok(near(pitchFor(34, TILT_MIN) * 180 / Math.PI, Math.max(PITCH_MIN, 34 + TILT_MIN)));
});

test('north up is the nearest full turn (snapping back takes the short way)', () => {
  assert.equal(nearestTurn(0.3), 0);
  assert.ok(near(nearestTurn(6.0), 2 * Math.PI));
  assert.ok(near(nearestTurn(-3.5), -2 * Math.PI));
});

test('a quick press and release is a click; moving 5 px or more is a drag', () => {
  const t = new DragTracker();
  t.press(100, 100, 0);
  assert.equal(t.move(102, 101), null);
  assert.equal(t.release(102, 101, 200), 'click');
  t.press(100, 100, 0);
  assert.deepEqual(t.move(110, 100), { dx: 10, dy: 0 });
  assert.deepEqual(t.move(115, 98), { dx: 5, dy: -2 });
  assert.equal(t.release(115, 98, 300), 'drag');
  t.press(100, 100, 0);
  assert.equal(t.release(101, 100, 900), null, 'held too long: neither');
  assert.equal(t.release(0, 0, 0), null, 'nothing pressed');
});
