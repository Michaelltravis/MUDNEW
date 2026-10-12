// Real-time combat on the client (world3d/actionclock.js): the swing clock and the global
// cooldown as the server last told them.
//   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ActionClock } from '../../src/web_isometric/world3d/actionclock.js';

test('before any word from the server, a press swings at once', () => {
  const c = new ActionClock();
  assert.equal(c.ready(1000), true);
  assert.deepEqual(c.press(1000), { swing: true, perfect: false });
  assert.equal(c.ready(1001), false, 'the predicted clock runs until the server corrects it');
  assert.equal(c.ready(4000), true, '…three seconds later the next is due');
});

test("the server's word sets the clock; an early press waits (and says if it is in the perfect window)", () => {
  const c = new ActionClock();
  c.told({ res: 'hit', next_ms: 3000, gcd_ms: 0 }, 10000);
  assert.equal(c.ready(12000), false);
  assert.deepEqual(c.press(11000), { swing: false, perfect: false }, 'two seconds early: no swing, not perfect');
  assert.equal(c.queued, true, 'the press is queued (the swing comes by itself)');
  assert.equal(c.press(12600).perfect, true, 'in its last 0.6 s: the perfect window');
  assert.equal(c.inPerfect(13100), true, '…with a little grace after');
  assert.equal(c.inPerfect(13200), false);
  c.told({ res: 'hit', next_ms: 3000 }, 13050);
  assert.equal(c.queued, false, 'a landed swing clears the queued press');
});

test('the swing ring runs from 0 to 1 between blows', () => {
  const c = new ActionClock({ swing: 3 });
  c.told({ next_ms: 3000 }, 0);
  assert.equal(c.progress(0), 0);
  assert.ok(Math.abs(c.progress(1500) - 0.5) < 1e-9);
  assert.equal(c.progress(5000), 1);
});

test('the global cooldown: started by a press, corrected by the server', () => {
  const c = new ActionClock({ gcd: 1 });
  c.startGcd(500);
  assert.equal(c.gcdLeft(1000), 500);
  assert.equal(c.gcdLeft(1600), 0);
  c.told({ res: 'gcd', gcd_ms: 200 }, 2000);
  assert.equal(c.gcdLeft(2100), 100, 'the server says how much is left');
  c.startGcd(3000);
  c.told({ res: 'hit', next_ms: 2500, gcd_ms: 0 }, 3050);
  assert.equal(c.gcdLeft(3100), 900, "a swing's word sent before the server saw the skill doesn't cancel it");
  c.configure({ swing: 2, gcd: 1.5, perfect: 0.5, grace: 0.1 });
  assert.equal(c.swing, 2000);
  assert.equal(c.gcd, 1500);
});
