// The right mouse button on the world: drag to turn (and tilt) the camera around the hero, a
// quick click (press and release without moving) to open a menu for what is under the cursor.
// Ctrl+click does the same on a Mac trackpad. Home snaps the view back to north up.
// The browser's own context menu never opens over the world (and never from a drag).
import { DragTracker } from './orbit.js';

export function attachWorldInput(engine, canvas, { onContext, typing = () => false } = {}) {
  const tr = new DragTracker();
  let pointer = null, quietUntil = 0;
  const begin = e => {
    pointer = e.pointerId;
    tr.press(e.clientX, e.clientY, performance.now());
    try { canvas.setPointerCapture(e.pointerId); } catch (_) { /* not capturable */ }
  };
  const finish = () => {
    if (pointer != null) { try { canvas.releasePointerCapture(pointer); } catch (_) { /* gone */ } }
    pointer = null;
    canvas.style.cursor = '';
  };
  canvas.addEventListener('pointerdown', e => {
    if (e.button === 2 || (e.button === 0 && e.ctrlKey)) { begin(e); e.preventDefault(); }
  });
  canvas.addEventListener('pointermove', e => {
    // a right button pressed while the left one is held arrives as a move, not a pointerdown
    if (pointer == null && (e.buttons & 2)) begin(e);
    if (pointer == null) return;
    const d = tr.move(e.clientX, e.clientY);
    if (d) { engine.orbit(d.dx, d.dy); canvas.style.cursor = 'grabbing'; }
  });
  canvas.addEventListener('pointerup', e => {
    if (pointer == null) return;
    const kind = tr.release(e.clientX, e.clientY, performance.now());
    finish();
    if (kind === 'drag') quietUntil = performance.now() + 300;
    else if (kind === 'click' && onContext) onContext(e.clientX, e.clientY);
  });
  const cancel = () => { tr.cancel(); finish(); };
  canvas.addEventListener('pointercancel', cancel);
  canvas.addEventListener('lostpointercapture', () => { if (pointer != null) cancel(); });
  window.addEventListener('blur', cancel);
  document.addEventListener('contextmenu', e => {
    if (e.target === canvas || performance.now() < quietUntil) e.preventDefault();
  });
  window.addEventListener('keydown', e => {
    if (e.key === 'Home' && !typing(e)) { engine.snapNorth(); e.preventDefault(); }
  });
  return { get dragging() { return tr.dragging; } };
}
