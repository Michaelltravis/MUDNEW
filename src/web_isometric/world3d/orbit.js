// The camera turning around the hero (right-drag) and tilting (right-drag up/down), and
// moving relative to where the camera looks. Pure (no THREE, no DOM): tested in Node.
//
// yaw 0 is the old fixed view: the camera south of the hero looking north (north = up on
// screen). Dragging right turns the view right (the camera swings the other way round).
export const YAW_PER_PX = 0.0065;      // radians per pixel dragged sideways
export const TILT_PER_PX = 0.15;       // degrees per pixel dragged up or down
export const TILT_MIN = -12, TILT_MAX = 10;     // added to the zoom's own pitch
export const PITCH_MIN = 26, PITCH_MAX = 66;    // the sun's shadow box still covers the view
export const DRAG_PX = 5;              // less than this between press and release is a click
export const CLICK_MS = 700;           // ...if it was also this quick
const D2R = Math.PI / 180;

// where the camera sits relative to the hero (metres)
export function orbitOffset(yaw, pitchRad, dist) {
  const h = Math.cos(pitchRad) * dist;
  return { x: Math.sin(yaw) * h, y: Math.sin(pitchRad) * dist, z: Math.cos(yaw) * h };
}

// the zoom's pitch plus the tilt, kept between the limits (degrees -> radians)
export function pitchFor(zoomPitchDeg, tiltDeg) {
  return Math.max(PITCH_MIN, Math.min(PITCH_MAX, zoomPitchDeg + tiltDeg)) * D2R;
}

export function clampTilt(t) { return Math.max(TILT_MIN, Math.min(TILT_MAX, t)); }

// a drag of (dx, dy) pixels: dragging right turns the view right, dragging up looks down
// more steeply (a higher view)
export function dragOrbit(yaw, tilt, dx, dy) {
  return { yaw: yaw - dx * YAW_PER_PX, tilt: clampTilt(tilt - dy * TILT_PER_PX) };
}

// keys (x right, z down the screen: W is (0, -1)) to a world direction for this view
export function toWorld(x, z, yaw) {
  const c = Math.cos(yaw), s = Math.sin(yaw);
  return { x: x * c + z * s, z: -x * s + z * c };
}

// the nearest "north up" angle (snapping back takes the short way round)
export function nearestTurn(yaw) { return Math.round(yaw / (2 * Math.PI)) * 2 * Math.PI; }

// Tells a right-click (open a menu) from a right-drag (turn the camera).
export class DragTracker {
  constructor() { this.down = null; this.dragging = false; }
  press(x, y, t) { this.down = { x, y, t, lx: x, ly: y }; this.dragging = false; }
  get active() { return !!this.down; }
  // deltas since the last move once it has become a drag, else null
  move(x, y) {
    const d = this.down;
    if (!d) return null;
    if (!this.dragging && Math.hypot(x - d.x, y - d.y) >= DRAG_PX) this.dragging = true;
    if (!this.dragging) return null;
    const out = { dx: x - d.lx, dy: y - d.ly };
    d.lx = x; d.ly = y;
    return out;
  }
  // 'click', 'drag' or null (nothing was pressed)
  release(x, y, t) {
    const d = this.down;
    if (!d) return null;
    this.down = null;
    if (this.dragging) { this.dragging = false; return 'drag'; }
    return Math.hypot(x - d.x, y - d.y) < DRAG_PX && t - d.t < CLICK_MS ? 'click' : null;
  }
  cancel() { this.down = null; this.dragging = false; }
}
